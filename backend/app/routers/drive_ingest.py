from fastapi import APIRouter
from ..drive_sync import baixar_arquivos_drive

router = APIRouter()

@router.post("/ingest_drive")
def ingest_from_drive():
    """
    Faz o download e indexação dos arquivos do Google Drive.
    Usa as credenciais definidas na variável GOOGLE_CREDENTIALS.
    """
    try:
        baixar_arquivos_drive()
        return {"status": "success", "message": "Arquivos do Drive processados com sucesso."}
    except Exception as e:
        return {"status": "error", "detail": str(e)}
