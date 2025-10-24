from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from backend.aprendizado import carregar_conhecimento
from backend.raciocinio import gerar_resposta, explicar_ficha, buscar_conhecimento

app = FastAPI(title="Babix IA")

# ======================================================
# 🔹 Middleware CORS
# ======================================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ======================================================
# 🔹 Evento de inicialização
# ======================================================
@app.on_event("startup")
async def startup_event():
    print("🔄 Carregando conhecimento do MBFT...")
    carregar_conhecimento("dados/mbft.pdf")
    print("✅ MBFT carregado na memória!")

# ======================================================
# 🔹 Endpoint principal de chat
# ======================================================
@app.post("/api/chat")
async def chat(request: Request):
    data = await request.json()
    pergunta = data.get("mensagem", "")
    resposta = gerar_resposta(pergunta)
    return {"resposta": resposta}

# ======================================================
# 🔹 Novo endpoint: explicação direta de fichas MBFT
# ======================================================
@app.post("/api/explicar")
async def explicar(request: Request):
    data = await request.json()
    codigo = data.get("codigo", "").strip()
    if not codigo:
        return {"erro": "É necessário informar o código da ficha, ex: 596-70."}

    texto_base = buscar_conhecimento()
    if not texto_base:
        return {"erro": "Base do MBFT ainda não carregada."}

    resposta = explicar_ficha(codigo, texto_base)
    return {"codigo": codigo, "explicacao": resposta}

# ======================================================
# 🔹 Status de verificação
# ======================================================
@app.get("/")
async def root():
    return {"status": "Babix IA ativa e com MBFT carregado!"}
