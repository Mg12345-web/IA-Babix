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

    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao acessar a página: {str(e)}")

    soup = BeautifulSoup(response.text, "html.parser")

    # Remove tags desnecessárias
    for tag in soup(["script", "style", "noscript"]):
        tag.extract()

    text = " ".join(soup.get_text().split())
    if not text or len(text) < 200:
        raise HTTPException(status_code=400, detail="Conteúdo insuficiente para indexação.")

    embedder = get_embedder()
    chroma = get_chroma()

    embedding = embedder.encode([text])[0]
    chroma.add(
        documents=[text],
        embeddings=[embedding],
        metadatas=[{"url": url}],
        ids=[url]
    )

    print(f"✅ Página indexada com sucesso: {url}")
    return {"status": "ok", "message": f"Página '{url}' indexada com sucesso!"}
