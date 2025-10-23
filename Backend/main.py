import os
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from dotenv import load_dotenv
from supabase import create_client, Client
from datetime import datetime

# ==== IMPORTA MÓDULOS INTERNOS ====
from backend.raciocinio import gerar_resposta
from backend.busca_avancada import modo_avancado
from backend.memoria import salvar_memoria, buscar_memoria
from backend.documentos import gerar_peticao_word
from backend.usuarios import autenticar_usuario, registrar_usuario
from backend.utils import log_acao

# ==== CARREGAR VARIÁVEIS DE AMBIENTE ====
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise Exception("⚠️  Variáveis SUPABASE_URL e SUPABASE_KEY não configuradas!")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ==== CONFIGURAÇÃO DO FASTAPI ====
app = FastAPI(
    title="Babix IA - Advogada Digital de Trânsito",
    description="API oficial da Babix IA. Roda no Railway e integra Supabase + Bing Search + ElevenLabs.",
    version="1.0.0"
)

# ==== CONFIGURAÇÃO DE CORS ====
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==== ROTAS ====

@app.get("/")
async def root():
    return {"message": "🚦 Babix IA rodando com sucesso no Railway!"}

# ========== ROTA 1: LOGIN ==========
@app.post("/api/login")
async def login(request: Request):
    data = await request.json()
    email = data.get("email")
    senha = data.get("senha")

    usuario = autenticar_usuario(supabase, email, senha)
    if not usuario:
        raise HTTPException(status_code=401, detail="Credenciais inválidas.")
    return {"status": "ok", "usuario": usuario}


# ========== ROTA 2: REGISTRO ==========
@app.post("/api/register")
async def register(request: Request):
    data = await request.json()
    return registrar_usuario(supabase, data)


# ========== ROTA 3: CHAT NORMAL ==========
@app.post("/api/chat")
async def chat(request: Request):
    data = await request.json()
    mensagem = data.get("mensagem", "")
    usuario_id = data.get("usuario_id")

    if not mensagem:
        raise HTTPException(status_code=400, detail="Mensagem vazia.")

    # tenta buscar algo parecido na memória
    memoria = buscar_memoria(supabase, usuario_id, mensagem)
    if memoria:
        resposta = memoria
    else:
        resposta = gerar_resposta(mensagem)
        salvar_memoria(supabase, usuario_id, mensagem, resposta)

    log_acao(supabase, usuario_id, "chat_basico")
    return {"resposta": resposta, "origem": "raciocínio interno"}


# ========== ROTA 4: MODO AVANÇADO ==========
@app.post("/api/advanced")
async def chat_avancado(request: Request):
    data = await request.json()
    mensagem = data.get("mensagem", "")
    usuario_id = data.get("usuario_id")

    if not mensagem:
        raise HTTPException(status_code=400, detail="Mensagem vazia.")

    resultado = modo_avancado(mensagem, usuario_id)
    salvar_memoria(supabase, usuario_id, mensagem, resultado["texto"])
    log_acao(supabase, usuario_id, "modo_avancado")

    return JSONResponse(content=resultado)


# ========== ROTA 5: GERAR PETIÇÃO ==========
@app.post("/api/gerar_doc")
async def gerar_doc(request: Request):
    data = await request.json()
    conteudo = data.get("conteudo", "")
    usuario_id = data.get("usuario_id")

    if not conteudo:
        raise HTTPException(status_code=400, detail="Conteúdo vazio.")

    caminho = gerar_peticao_word(conteudo)
    log_acao(supabase, usuario_id, "gerar_peticao")
    return FileResponse(caminho, filename="peticao_babix.docx")


# ========== ROTA 6: ESTATÍSTICAS ==========
@app.get("/api/stats")
async def stats():
    registros = supabase.table("estatisticas").select("*").execute()
    return {"estatisticas": registros.data}


# ========== ERRO PADRÃO ==========
@app.exception_handler(Exception)
async def erro_geral(request: Request, exc: Exception):
    return JSONResponse(status_code=500, content={"erro": str(exc)})


# ========== MAIN ==========
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000)
