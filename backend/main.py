from fastapi import FastAPI, Request, UploadFile, File, Header
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import os

from backend.leitor import indexar_mbft_padrao, indexar_pdf
from backend.raciocinio import gerar_resposta, obter_ficha_por_codigo, formatar_explicacao

app = FastAPI(title="Babix IA — MBFT Core")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # deixe restrito ao seu domínio do Hostinger se quiser
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ADMIN_TOKEN = os.getenv("ADMIN_TOKEN")

# -----------------------------
# Startup: indexa MBFT /dados/mbft.pdf se existir
# -----------------------------
@app.on_event("startup")
async def startup_event():
    print("🔄 Inicializando Babix IA…")
    indexar_mbft_padrao()
    print("✅ Pronta para responder.")

# -----------------------------
# Chat livre
# -----------------------------
@app.post("/api/chat")
async def chat(request: Request):
    data = await request.json()
    pergunta = (data.get("mensagem") or "").strip()
    resposta = gerar_resposta(pergunta)
    return {"resposta": resposta}

# -----------------------------
# Explicação direta por código
# -----------------------------
@app.post("/api/explicar")
async def explicar(request: Request):
    data = await request.json()
    codigo = (data.get("codigo") or "").strip()
    if not codigo:
        return {"erro": "Informe o código de ficha. Ex.: 596-70"}
    f = obter_ficha_por_codigo(codigo)
    if not f:
        return {"erro": f"Ficha {codigo} não encontrada."}
    return {"codigo": codigo, "explicacao": formatar_explicacao(f)}

# -----------------------------
# Upload seguro de novos PDFs (admin)
# -----------------------------
@app.post("/api/learn")
async def learn(file: UploadFile = File(...), authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        return {"erro": "Token ausente. Use Authorization: Bearer <ADMIN_TOKEN>."}
    token = authorization.split(" ", 1)[1]
    if token != (ADMIN_TOKEN or ""):
        return {"erro": "Acesso negado. Token inválido."}

    dados_dir = Path(__file__).resolve().parent.parent / "dados"
    dados_dir.mkdir(parents=True, exist_ok=True)
    destino = dados_dir / file.filename
    destino.write_bytes(await file.read())

    resumo = indexar_pdf(str(destino), Path(file.filename).stem, limpar_fichas_anteriores=False)
    return {"status": "✅ Novo conhecimento adicionado.", "resumo": resumo}

# -----------------------------
# Health
# -----------------------------
@app.get("/")
async def root():
    return {"status": "Babix IA ativa (MBFT indexado se presente)."}
