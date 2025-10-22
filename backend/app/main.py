
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse, PlainTextResponse
from pydantic import BaseModel
from .services.docx_service import build_docx
from .services.rag_service import RagService
from .services.memory_service import MemoryService
from .agents.orchestrator import Orchestrator
import os

app = FastAPI(title="IA Advogada de Trânsito (MVP)", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

VECTORS_PATH = os.getenv("VECTORS_PATH", "/data/vectors")
UPLOADS_PATH = os.getenv("UPLOADS_PATH", "/data/uploads")
os.makedirs(VECTORS_PATH, exist_ok=True)
os.makedirs(UPLOADS_PATH, exist_ok=True)

rag = RagService(VECTORS_PATH)
memory = MemoryService()
orchestrator = Orchestrator(rag=rag, memory=memory)

class ChatInput(BaseModel):
    pergunta: str
    caso: dict | None = None

@app.get("/health")
def health():
    return {"ok": True}

@app.post("/knowledge/files")
async def ingest_file(file: UploadFile = File(...)):
    # salva e indexa
    dest = os.path.join(UPLOADS_PATH, file.filename)
    with open(dest, "wb") as f:
        f.write(await file.read())
    added = rag.ingest_file(dest)
    return {"file": file.filename, "chunks": added}

@app.post("/chat")
async def chat(inp: ChatInput):
    resposta, fontes, perguntas = orchestrator.answer(inp.pergunta, inp.caso or {})
    return {"resposta": resposta, "fontes": fontes, "perguntas_faltantes": perguntas}

class DocInput(BaseModel):
    fatos: str
    direito: str
    jurisprudencias: list[str] = []
    pedidos: list[str] = []
    conclusao: str = "Termos em que, pede deferimento."

@app.post("/documents/generate")
async def doc_generate(payload: DocInput):
    path = build_docx(payload)
    return FileResponse(path, filename=os.path.basename(path))

@app.get("/", response_class=PlainTextResponse)
def root():
    return "IA Advogada de Trânsito — Backend OK"
