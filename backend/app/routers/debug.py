from fastapi import APIRouter
import chromadb
import os

router = APIRouter()

CHROMA_DIR = os.getenv("CHROMA_DIR", "./dados/chroma")

@router.get("/debug")
def debug_collection():
    """
    Debug da coleção ChromaDB
    Mostra quantos documentos, de quais arquivos, etc.
    """
    try:
        client = chromadb.PersistentClient(path=CHROMA_DIR)
        collection = client.get_collection("babix_docs")
        
        # Contar total
        total = collection.count()
        
        # Pegar amostra de metadados
        sample = collection.get(limit=100)
        
        # Agrupar por arquivo
        files_count = {}
        for meta in sample["metadatas"]:
            if meta:
                filename = meta.get("name", "unknown")
                files_count[filename] = files_count.get(filename, 0) + 1
        
        # Verificar se tem MBFT
        has_mbft = any("mbft" in f.lower() for f in files_count.keys())
        
        return {
            "total_documents": total,
            "files_indexed": files_count,
            "has_mbft": has_mbft,
            "sample_metadata": sample["metadatas"][:5]
        }
        
    except Exception as e:
        return {
            "error": str(e),
            "chroma_dir": CHROMA_DIR
        }
