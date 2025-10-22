from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from aprendizado_local import responder, treinar_base

app = FastAPI(title="TrafficLaw AI Local", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inicialmente vazio — você vai popular depois
LINKS_INICIAIS = [
    "https://www.planalto.gov.br/ccivil_03/leis/l9503compilado.htm",
    "https://www.gov.br/transportes/pt-br/assuntos/transito/conteudo-contran/resolucoes/Resolucao9852022.pdf"
]

@app.on_event("startup")
def iniciar():
    print("⚙️ Iniciando TrafficLaw AI local...")

@app.post("/perguntar")
async def perguntar(request: Request):
    dados = await request.json()
    pergunta = dados.get("mensagem", "")
    resposta = responder(pergunta)
    return JSONResponse({"resposta": resposta})

@app.post("/treinar")
async def treinar():
    treinar_base(LINKS_INICIAIS)
    return JSONResponse({"status": "ok", "msg": "Base de conhecimento treinada com sucesso!"})
