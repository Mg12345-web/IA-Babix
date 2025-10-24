from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from backend.aprendizado import carregar_conhecimento
from backend.raciocinio import gerar_resposta

app = FastAPI(title="Babix IA")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 🔹 Inicializa a IA ao iniciar o servidor
@app.on_event("startup")
async def startup_event():
    print("🔄 Carregando conhecimento do MBFT...")
    carregar_conhecimento("dados/mbft.pdf")
    print("✅ MBFT carregado na memória!")

# 🔹 Endpoint principal de chat
@app.post("/api/chat")
async def chat(request: Request):
    data = await request.json()
    pergunta = data.get("mensagem", "")
    resposta = gerar_resposta(pergunta)
    return {"resposta": resposta}

# 🔹 Endpoint de status (teste rápido)
@app.get("/")
async def root():
    return {"status": "Babix IA ativa e com MBFT carregado!"}
