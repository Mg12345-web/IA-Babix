from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from bs4 import BeautifulSoup
import requests
from sentence_transformers import SentenceTransformer
from chromadb import Client
from chromadb.config import Settings
import os

router = APIRouter()

CHROMA_DIR = os.getenv("CHROMA_DIR", "./dados/chroma")
_embedder = None


class WebIngestRequest(BaseModel):
    url: str


def get_embedder():
    global _embedder
    if _embedder is None:
        _embedder = SentenceTransformer("all-MiniLM-L6-v2")
    return _embedder


def get_chroma():
    os.makedirs(CHROMA_DIR, exist_ok=True)
    client = Client(Settings(chroma_db_impl="duckdb+parquet", persist_directory=CHROMA_DIR))
    return client.get_or_create_collection("babix_docs")


@router.post("/ingest_web")
async def ingest_web(req: WebIngestRequest):
    url = req.url.strip()
    if not url.startswith("http"):
        raise HTTPException(status_code=400, detail="URL inválida.")

    print(f"🌐 Iniciando ingestão de: {url}")

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "pt-BR,pt;q=0.9",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }

    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        response.encoding = response.apparent_encoding  # garante leitura correta
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao acessar a página: {str(e)}")

    soup = BeautifulSoup(response.text, "html.parser")

    # Remove scripts, estilos e metadados
    for tag in soup(["script", "style", "noscript", "meta", "iframe"]):
        tag.decompose()

    # Extrai apenas o texto limpo
    text = " ".join(soup.get_text(separator=" ").split())

    if not text or len(text) < 200:
        raise HTTPException(status_code=400, detail="Conteúdo insuficiente para indexação.")

    chroma = get_chroma()
    embedder = get_embedder()

    # Evita duplicar documentos
    existing_docs = chroma.get(ids=[url])
    if existing_docs and len(existing_docs["ids"]) > 0:
        return {"status": "ok", "message": f"A página '{url}' já está indexada."}

    embedding = embedder.encode([text])[0]
    chroma.add(
        documents=[text],
        embeddings=[embedding],
        metadatas=[{"url": url}],
        ids=[url]
    )

    print(f"✅ Página indexada com sucesso: {url}")
    return {"status": "ok", "message": f"Página '{url}' indexada com sucesso!"}
