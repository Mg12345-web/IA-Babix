from fastapi import FastAPI, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from backend.aprendizado import (
    carregar_todos_documentos,
    processar_documentos_com_progresso,
    progresso_global,
    DB_PATH
)
from backend.raciocinio import gerar_resposta
from backend.indexador import indexar_mbft
import os
import sqlite3

app = FastAPI(title="Babix IA")

# =====================================================
# 🔹 Configuração de CORS
# =====================================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =====================================================
# 🔹 Evento de inicialização
# =====================================================
@app.on_event("startup")
async def startup_event():
    print("\n==============================")
    print("🚀 Inicializando Babix IA...")
    print("==============================")

    try:
        # Cria pasta e banco, se necessário
        os.makedirs("backend/db", exist_ok=True)

        if not os.path.exists(DB_PATH):
            print("⚙️ Criando banco e carregando base inicial...")
            carregar_todos_documentos("dados")
        else:
            conn = sqlite3.connect(DB_PATH)
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM fichas")
            total = cur.fetchone()[0]
            conn.close()

            if total == 0:
                print("📚 Banco vazio — carregando documentos...")
                carregar_todos_documentos("dados")
            else:
                print(f"✅ Banco com {total} registros prontos!")

        # Reindexa MBFT se necessário
        print("🔍 Verificando fichas do MBFT...")
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM fichas WHERE codigo != 'MBFT-GERAL'")
        total_fichas = cur.fetchone()[0]
        conn.close()

        if total_fichas < 50:
            print("📑 Reindexando fichas do MBFT...")
            indexar_mbft()
        else:
            print(f"📋 {total_fichas} fichas já indexadas — OK.")

        print("✅ Sistema Babix IA pronto para uso!")
        print("==============================\n")

    except Exception as e:
        print(f"❌ Erro ao iniciar Babix IA: {e}")
        print("==============================\n")

# =====================================================
# 🔹 Endpoints principais
# =====================================================

@app.post("/api/chat")
async def chat(request: Request):
    """Chat principal com Babix IA"""
    data = await request.json()
    pergunta = data.get("mensagem", "").strip()

    if not pergunta:
        return {"resposta": "⚠️ Nenhuma pergunta recebida."}

    resposta = gerar_resposta(pergunta)
    return {"resposta": resposta}


# =====================================================
# 🧩 Endpoints do Painel de Aprendizado (Dashboard)
# =====================================================

@app.post("/api/aprender_dashboard")
async def aprender_dashboard(background_tasks: BackgroundTasks):
    """Inicia aprendizado com monitoramento (para o dashboard)."""
    pasta = "backend/dados"
    background_tasks.add_task(processar_documentos_com_progresso, pasta, progresso_global)
    return {"status": f"🚀 Iniciando aprendizado e atualização em tempo real a partir de {pasta}..."}


@app.get("/api/progresso")
async def progresso_leitura():
    """Retorna o progresso atual em tempo real."""
    return progresso_global


@app.post("/api/aprender")
async def aprender_tudo():
    """Modo rápido (sem progresso visual) — útil para carregamento manual."""
    try:
        total = carregar_todos_documentos("dados")
        return {"status": f"✅ {total} arquivos lidos e armazenados com sucesso."}
    except Exception as e:
        return {"status": f"❌ Erro ao aprender: {e}"}


# =====================================================
# 🔹 Endpoint de status geral
# =====================================================
@app.get("/")
async def root():
    """Status geral da Babix IA."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM fichas")
        total = cur.fetchone()[0]
        conn.close()
    except:
        total = 0

    return {
        "status": "✅ Babix IA ativa!",
        "descricao": "Sistema de aprendizado contínuo e análise de legislação de trânsito",
        "registros": total,
        "modulos": ["chat", "aprender", "dashboard"]
    }
