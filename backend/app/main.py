from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from .routers import health, ingest, chat, debug, drive_ingest, web_ingest
import os

# 🔹 Importa todas as rotas
from .routers import health, ingest, chat, debug, drive_ingest


def create_app() -> FastAPI:
    app = FastAPI(title="Babix API", version="0.3.0")

    # 🔹 Rotas principais
    app.include_router(health.router, prefix="/api", tags=["health"])
    app.include_router(ingest.router, prefix="/api", tags=["ingest"])
    app.include_router(chat.router, prefix="/api", tags=["chat"])
    app.include_router(debug.router, prefix="/api", tags=["debug"])
    app.include_router(drive_ingest.router, prefix="/api", tags=["drive_ingest"])
    app.include_router(web_ingest.router, prefix="/api", tags=["web_ingest"])

    # 🔹 Servir arquivos estáticos da pasta frontend
    frontend_path = os.path.join(os.path.dirname(__file__), "../../frontend")
    app.mount("/frontend", StaticFiles(directory=frontend_path), name="frontend")

    # 🔹 Rota padrão: redireciona para o painel de teste
    @app.get("/")
    async def root():
        test_file = os.path.join(frontend_path, "test.html")
        if os.path.exists(test_file):
            return FileResponse(test_file)
        return {"message": "Frontend não encontrado."}

    return app


app = create_app()
