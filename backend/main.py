from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from aprendizado import carregar_conhecimento
from raciocinio import gerar_resposta

app = FastAPI(title="Babix IA")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 🔹 Leitura automática do MBFT ao iniciar
@app.on_event("startup")
async def startup_event():
    print("🔄 Carregando conhecimento do MBFT...")
    carregar_conhecimento("dados/mbft.pdf")
    print("✅ MBFT carregado na memória!")

@app.post("/api/chat")
async def chat(request: Request):
    data = await request.json()
    pergunta = data.get("mensagem", "")
    resposta = gerar_resposta(pergunta)
    return {"resposta": resposta}

@app.get("/")
async def root():
    return {"status": "Babix IA ativa e com MBFT carregado!"}
