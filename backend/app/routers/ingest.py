import os
from fastapi import APIRouter
from sentence_transformers import SentenceTransformer
from ..deps import chroma_client, collection, EMBEDDING_MODEL

router = APIRouter()

@router.post("/ingest")
def ingest_files():
    """
    Lê recursivamente todos os arquivos de texto (.txt, .md) dentro da pasta /dados
    e adiciona ao ChromaDB.
    """
    base_path = "./dados"
    print(f"📂 Varredura iniciada em: {os.path.abspath(base_path)}")
    embedder = SentenceTransformer(EMBEDDING_MODEL)
    added_files = []

    for root, dirs, files in os.walk(base_path):
        for file_name in files:
            if not file_name.lower().endswith((".txt", ".md")):
                continue

            file_path = os.path.join(root, file_name)
            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()

                # cria o embedding
                embedding = embedder.encode(content).tolist()

                # adiciona à coleção (usa caminho completo como ID)
                collection.add(
                    ids=[file_path],
                    documents=[content],
                    embeddings=[embedding],
                )

                added_files.append(file_path)
                print(f"✅ Indexado: {file_path}")

            except Exception as e:
                print(f"⚠️ Erro ao processar {file_path}: {e}")

    return {"ingested_files": added_files, "total": len(added_files)}
