import os
from fastapi import APIRouter

router = APIRouter()

@router.get("/debug/files")
def list_files():
    """
    Lista todos os arquivos e pastas dentro de /app/dados para verificar
    se o Railway copiou corretamente os arquivos no build.
    """
    base_path = "./dados"
    if not os.path.exists(base_path):
        return {"error": f"Pasta {base_path} não encontrada."}

    file_list = []
    for root, dirs, files in os.walk(base_path):
        for f in files:
            file_list.append(os.path.join(root, f))

    return {
        "base_path": os.path.abspath(base_path),
        "files_found": file_list,
        "total": len(file_list)
    }
