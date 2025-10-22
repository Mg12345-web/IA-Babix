# backend/main.py

import os
from subprocess import Popen

import uvicorn
from fastapi import FastAPI, Request, Form
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from jinja2 import Environment, FileSystemLoader

from raciocinio import evaluate_topic
from memoria import Memoria
from utils import ensure_db, log_action

# Caminho do banco de dados
DB_PATH = os.environ.get("DB_PATH", "db/conhecimento.db")
ensure_db(DB_PATH)
mem = Memoria(DB_PATH)

app = FastAPI(title="Babix IA - Backend")

# Servir frontend estático
app.mount(
    "/static",
    StaticFiles(directory=os.path.join(os.path.dirname(__file__), "../frontend")),
    name="static",
)

# Endpoint chat — recebe texto e keywords
@app.post("/api/chat")
async def api_chat(payload: dict):
    text = payload.get("message", "")
    # Extrair keywords simples (split) — ideal: usar NER no futuro
    keywords = [w for w in text.split() if len(w) > 3][:8]
    res = evaluate_topic(DB_PATH, keywords)
    log_action(DB_PATH, "chat_query", text)
    return JSONResponse(content=res)

# Endpoint para iniciar aprendizado a partir de query web
@app.post("/api/learn")
async def api_learn(mode: str = Form("web"), query: str = Form(...)):
    if mode not in ("web", "local"):
        return JSONResponse({"ok": False, "msg": "mode invalid"})
    # Chama o indexador em background
    Popen(
        [
            "python",
            os.path.join(os.path.dirname(__file__), "aprendizado.py"),
            "--db",
            DB_PATH,
            "--mode",
            mode,
            "--query",
            query,
        ]
    )
    return JSONResponse({"ok": True, "msg": "indexing started"})

# Dashboard para visualização do que a IA aprendeu
@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    env = Environment(
        loader=FileSystemLoader(os.path.join(os.path.dirname(__file__), "../frontend"))
    )
    tmpl = env.get_template("dashboard.html")
    sources = mem.list_sources()
    chunks = mem.list_chunks(limit=200)
    html = tmpl.render(sources=sources, chunks=chunks)
    return HTMLResponse(content=html)

# API para obter texto completo de um chunk
@app.get("/api/chunk/{chunk_id}")
async def get_chunk(chunk_id: int):
    text = mem.get_chunk_text(chunk_id)
    return JSONResponse({"id": chunk_id, "text": text})

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 8000)),
        reload=True,
    )
