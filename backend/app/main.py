from fastapi import FastAPI
from .routers import health, ingest, chat

def create_app() -> FastAPI:
    app = FastAPI(title="Babix API", version="0.2.0")
    app.include_router(health.router, prefix="/api", tags=["health"])
    app.include_router(ingest.router, prefix="/api", tags=["ingest"])
    app.include_router(chat.router, prefix="/api", tags=["chat"])
    return app

app = create_app()
