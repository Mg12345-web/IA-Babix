from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from backend.aprendizado import carregar_conhecimento
from backend.raciocinio import gerar_resposta
from backend.indexador import indexar_mbft
import os

app = FastAPI(title="Babix IA")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 🔹 Evento executado quando o servidor inicia
@app.on_event("startup")
async def startup_event():
    print("\n==============================")
    print("🚀 Inicializando Babix IA...")
    print("==============================")

    try:
        # 🧠 Carregar conhecimento do MBFT
        print("🔄 Carregando conhecimento do MBFT...")
        carregar_conhecimento("backend/dados/mbft.pdf")
        print("✅ MBFT carregado na memória!")

        # 📚 Evita reindexação se o banco já contiver fichas
        from backend.aprendizado import DB_PATH
        if os.path.exists(DB_PATH):
            import sqlite3
            conn = sqlite3.connect(DB_PATH)
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM fichas WHERE codigo != 'MBFT-GERAL'")
            total_fichas = cur.fetchone()[0]
            conn.close()

            if total_fichas > 100:
                print(f"📑 {total_fichas} fichas já indexadas — pulando reindexação.")
            else:
                print("🔍 Iniciando indexação automática das fichas...")
                indexar_mbft()
        else:
            print("⚠️ Banco não encontrado, indexando do zero...")
            indexar_mbft()

        print("✅ Sistema Babix IA pronto para uso!")
        print("==============================\n")

    except Exception as e:
        print(f"❌ Erro ao iniciar Babix IA: {e}")
        print("==============================\n")


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
    return {"status": "✅ Babix IA ativa e com MBFT carregado!"}
