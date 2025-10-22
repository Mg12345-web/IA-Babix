from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from aprendizado import responder_usuario, carregar_base

app = FastAPI(title="TrafficLaw AI", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Carrega o modelo e os embeddings ao iniciar
@app.on_event("startup")
def startup_event():
    carregar_base()

@app.post("/perguntar")
async def perguntar(request: Request):
    data = await request.json()
    pergunta = data.get("mensagem", "")
    resposta = responder_usuario(pergunta)
    return JSONResponse({"resposta": resposta})
