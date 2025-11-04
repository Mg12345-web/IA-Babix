from fastapi import APIRouter
from ..drive_sync import baixar_arquivos_drive

router = APIRouter()

@router.post("/ingest")
async def ingest_from_drive():
    try:
        baixar_arquivos_drive()
        return {"message": "ok", "source": "drive"}
    except Exception as e:
        return {"error": str(e)}
