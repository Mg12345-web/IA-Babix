from fastapi import FastAPI, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from backend.aprendizado import (
    carregar_todos_documentos,
    processar_documentos_com_progresso,
    progresso_global
)
from backend.raciocinio import gerar_resposta, gerar_resposta_observacao
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
        from backend.aprendizado import DB_PATH

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
    pergunta = data.get("mensagem", "")
    resposta = gerar_resposta(pergunta)
    return {"resposta": resposta}


@app.post("/api/analisar")
async def analisar_observacao(request: Request):
    """Análise técnica de campo observações"""
    data = await request.json()
    texto = data.get("observacao", "")
    resposta = gerar_resposta_observacao(texto)
    return {"resposta": resposta}


# =====================================================
# 🧩 Endpoints do Painel de Aprendizado (Dashboard)
# =====================================================

@app.post("/api/aprender_dashboard")
async def aprender_dashboard(background_tasks: BackgroundTasks):
    """
    Inicia aprendizado com monitoramento (para o dashboard no Hostinger).
    """
    background_tasks.add_task(processar_documentos_com_progresso, "dados", progresso_global)
    return {"status": "🚀 Iniciando aprendizado e atualização em tempo real..."}


@app.get("/api/progresso")
async def progresso_leitura():
    """Retorna o progresso atual em tempo real."""
    return progresso_global


@app.post("/api/aprender")
async def aprender_tudo():
    """
    Modo rápido (sem progresso visual) — útil para carregar manualmente via POST.
    """
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
    return {
        "status": "✅ Babix IA ativa!",
        "descricao": "Sistema de aprendizado contínuo e análise de infrações",
        "modulos": ["chat", "analisar", "aprender", "dashboard"]
    }
