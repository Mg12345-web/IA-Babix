import os
from fastapi import APIRouter
from sentence_transformers import SentenceTransformer
from ..deps import chroma_client, collection, EMBEDDING_MODEL

router = APIRouter()

@router.post("/ingest")
def ingest_files():
    """Lê arquivos de /dados e armazena embeddings no Chroma."""
    base_path = "./dados"
    embedder = SentenceTransformer(EMBEDDING_MODEL)
    added_files = []

    for file_name in os.listdir(base_path):
        file_path = os.path.join(base_path, file_name)
        if not os.path.isfile(file_path):
            continue

        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()

        # cria embeddings
        embedding = embedder.encode(content).tolist()

        # adiciona à coleção (id = nome do arquivo)
        collection.add(
            ids=[file_name],
            documents=[content],
            embeddings=[embedding],
        )

        added_files.append(file_name)

    return {"ingested_files": added_files, "total": len(added_files)}
