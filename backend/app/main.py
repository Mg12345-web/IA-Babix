from fastapi import FastAPI
from .routers import health

def create_app() -> FastAPI:
    app = FastAPI(title="Babix API", version="0.1.0")
    app.include_router(health.router, prefix="/api", tags=["health"])
    return app

app = create_app()
