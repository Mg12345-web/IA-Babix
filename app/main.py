
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse, HTMLResponse

app = FastAPI(title="TrafficLaw AI", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = os.path.dirname(__file__)
FRONTEND_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "frontend"))
app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

@app.get("/", response_class=HTMLResponse)
def root():
    index_path = os.path.join(FRONTEND_DIR, "index.html")
    return FileResponse(index_path) if os.path.exists(index_path) else HTMLResponse("<h1>Frontend not found</h1>", status_code=404)

# ---- Mock API routes you can replace later ----
@app.get("/api/health")
def health():
    return {"status": "ok"}

@app.get("/api/quick-answers")
def quick_answers():
    return {
        "belt_fine": {
            "description": "Dirigir sem cinto de segurança",
            "gravity": "Grave",
            "fine": 195.23,
            "points": 5
        }
    }

@app.post("/api/ask")
async def ask(payload: dict):
    question = payload.get("question", "").strip()
    # Dummy response just to wire the UI; replace with your IA later
    if "cinto" in question.lower():
        return JSONResponse({
            "answer": "A infração por dirigir sem cinto de segurança é grave, com multa de R$ 195,23 e 5 pontos na CNH."
        })
    return JSONResponse({"answer": "Recebi sua pergunta. Em breve conectaremos ao motor de IA."})


# ---------- DB init on startup ----------
from .db import init_db
init_db()

# ---------- Ingestion & QA ----------
from pydantic import BaseModel
from typing import List
from .ingest import fetch_and_index
from .qa import answer
from .db import search_fts

class IngestBody(BaseModel):
    urls: List[str]

@app.post("/api/ingest")
async def api_ingest(body: IngestBody):
    results = []
    for url in body.urls:
        results.append(fetch_and_index(url))
    return {"ingested": results}

@app.get("/api/search")
def api_search(q: str):
    return {"results": search_fts(q)}

@app.post("/api/ask")
async def ask(payload: dict):
    question = payload.get("question", "").strip()
    if not question:
        return {"answer": "Pergunta vazia."}
    reply, cites = answer(question)
    return {"answer": reply, "citations": cites}
