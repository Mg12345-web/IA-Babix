# backend/main.py

import os
from subprocess import Popen
import uvicorn
from fastapi import FastAPI, Request, Form
from fastapi.responses import JSONResponse, HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from jinja2 import Environment, FileSystemLoader

from backend.raciocinio import evaluate_topic
from backend.memoria import Memoria
from backend.utils import ensure_db, log_action


# Caminho para o banco SQLite
DB_PATH = os.environ.get("DB_PATH", "db/conhecimento.db")
ensure_db(DB_PATH)
mem = Memoria(DB_PATH)

# Inicializa o app FastAPI
app = FastAPI(title="Babix IA - Backend")

# Monta o diretório do frontend como estático
frontend_dir = os.path.join(os.path.dirname(__file__), "../frontend")
app.mount("/static", StaticFiles(directory=frontend_dir), name="static")


# --- ROTAS PRINCIPAIS ---

# Chat endpoint: recebe {"message": "..."}
@app.post("/api/chat")
async def api_chat(payload: dict):
    text = payload.get("message", "")
    keywords = [w for w in text.split() if len(w) > 3][:8]
    res = evaluate_topic(DB_PATH, keywords)
    log_action(DB_PATH, "chat_query", text)
    return JSONResponse(content=res)


# Inicia o processo de aprendizado (modo web ou local)
@app.post("/api/learn")
async def api_learn(mode: str = Form("web"), query: str = Form(...)):
    if mode not in ("web", "local"):
        return JSONResponse({"ok": False, "msg": "mode invalid"})
    script = os.path.join(os.path.dirname(__file__), "aprendizado.py")
    Popen(["python", script, "--db", DB_PATH, "--mode", mode, "--query", query])
    return JSONResponse({"ok": True, "msg": "indexing started"})


# Dashboard de aprendizado
@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    templates = os.path.join(os.path.dirname(__file__), "../frontend")
    env = Environment(loader=FileSystemLoader(templates))
    tmpl = env.get_template("dashboard.html")
    sources = mem.list_sources()
    chunks = mem.list_chunks(limit=200)
    html = tmpl.render(sources=sources, chunks=chunks)
    return HTMLResponse(content=html)


# Retorna texto completo de um chunk específico
@app.get("/api/chunk/{chunk_id}")
async def get_chunk(chunk_id: int):
    text = mem.get_chunk_text(chunk_id)
    return JSONResponse({"id": chunk_id, "text": text})


# --- ROTA RAIZ (serve o frontend automaticamente) ---
@app.get("/", response_class=FileResponse)
async def serve_frontend():
    index_path = os.path.join(os.path.dirname(__file__), "../frontend/index.html")
    return FileResponse(index_path)


# --- INICIALIZAÇÃO ---
if __name__ == "__main__":
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 8000)),
        reload=False,
    )
