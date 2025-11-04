from fastapi import APIRouter
from app.drive_sync import baixar_arquivos_drive

router = APIRouter()

@router.post("/ingest")
async def ingest_from_drive():
    """
    Faz a ingestão automática dos arquivos do Google Drive jurídico
    e atualiza a base de conhecimento da Babix.
    """
    try:
        baixar_arquivos_drive()
        return {"message": "✅ Ingestão concluída com sucesso! Arquivos do Drive atualizados."}
    except Exception as e:
        return {"error": str(e)}
