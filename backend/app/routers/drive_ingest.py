from fastapi import APIRouter, BackgroundTasks
from ..drive_sync import baixar_arquivos_drive

router = APIRouter()

@router.post("/ingest_drive")
def ingest_from_drive(background_tasks: BackgroundTasks):
    """
    Faz o download e indexação dos arquivos do Google Drive.
    Executa em background para não travar a API.
    """
    try:
        # Executa a ingestão em background (não bloqueia)
        background_tasks.add_task(baixar_arquivos_drive)
        
        return {
            "status": "processing",
            "message": "Ingestão iniciada em background. Verifique os logs para progresso."
        }
    except Exception as e:
        return {
            "status": "error",
            "detail": str(e)
        }
