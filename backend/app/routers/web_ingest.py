from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import requests
from bs4 import BeautifulSoup
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.config import Settings
import os

router = APIRouter()

# Configurações
CHROMA_DIR = os.getenv("CHROMA_DIR", "./dados/chroma")
embedder = SentenceTransformer("all-MiniLM-L6-v2")
chroma = chromadb.Client(Settings(persist_directory=CHROMA_DIR))
collection = chroma.get_or_create_collection("babix_docs")

# Modelo do corpo da requisição
class WebIngestRequest(BaseModel):
    url: str

def extrair_texto(url: str) -> str:
    """Baixa e limpa o texto principal de uma página web."""
    headers = {"User-Agent": "Mozilla/5.0 (compatible; BabixBot/1.0)"}
    res = requests.get(url, headers=headers, timeout=20)

    if res.status_code != 200:
        raise HTTPException(status_code=400, detail=f"Erro ao acessar {url} ({res.status_code})")

    soup = BeautifulSoup(res.text, "html.parser")

    # Remove scripts e estilos
    for tag in soup(["script", "style", "header", "footer", "nav", "aside"]):
        tag.extract()

    text = soup.get_text(separator=" ", strip=True)
    return " ".join(text.split())  # remove espaçamento extra


@router.post("/ingest_web")
def ingest_web(req: WebIngestRequest):
    """Indexa o conteúdo textual de uma página web no Chroma."""
    url = req.url.strip()
    if not url:
        raise HTTPException(status_code=400, detail="URL não informada.")

    try:
        texto = extrair_texto(url)
        embedding = embedder.encode([texto])[0]

        collection.add(
            documents=[texto],
            embeddings=[embedding],
            metadatas=[{"url": url}],
            ids=[url]
        )

        return {"status": "ok", "message": f"Página '{url}' indexada com sucesso!"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
