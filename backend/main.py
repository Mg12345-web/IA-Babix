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
import threading

app = FastAPI(title="Babix IA")

# =====================================================
# 🔹 CORS — permite integração com o frontend (Hostinger)
# =====================================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =====================================================
# 🔹 Inicialização assíncrona (evita travar Railway)
# =====================================================
@app.on_event("startup")
async def startup_event():
    print("\n==============================")
    print("🚀 Inicializando Babix IA...")
    print("==============================")

    def inicializar_background():
        """Executa toda a rotina de preparação de forma segura"""
        try:
            os.makedirs("backend/db", exist_ok=True)

            # ✅ Verifica se o banco já existe e está populado
            precisa_carregar = False
            if not os.path.exists(DB_PATH):
                precisa_carregar = True
            else:
                try:
                    conn = sqlite3.connect(DB_PATH)
                    cur = conn.cursor()
                    cur.execute("SELECT COUNT(*) FROM fichas")
                    total = cur.fetchone()[0]
                    conn.close()
                    if total == 0:
                        precisa_carregar = True
                except Exception:
                    precisa_carregar = True

            # 🔹 Só carrega a pasta /dados se necessário
            if precisa_carregar:
                print("📚 Banco vazio — iniciando aprendizado inicial da pasta /dados...")
                carregar_todos_documentos("dados")
            else:
                print("✅ Banco já existente — pulando carregamento inicial.")

            # 🔹 Reindexa MBFT apenas se necessário
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

    # Roda em segundo plano (não trava o Railway)
    threading.Thread(target=inicializar_background, daemon=True).start()

# =====================================================
# 🔹 Endpoints principais
# =====================================================

from backend.raciocinio import gerar_resposta

@app.post("/api/chat")
async def chat(request: Request):
    dados = await request.json()
    pergunta = dados.get("mensagem", "")
    resposta = gerar_resposta(pergunta)
    return {"resposta": resposta}

# =====================================================
# 🧩 Aprendizado manual e dashboard
# =====================================================

@app.post("/api/aprender_dashboard")
async def aprender_dashboard(background_tasks: BackgroundTasks):
    """Inicia aprendizado com monitoramento (para o dashboard)."""
    pasta = "dados"  # ✅ Raiz
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
        total = carregar_todos_documentos("dados")  # ✅ Raiz
        return {"status": f"✅ {total} arquivos lidos e armazenados com sucesso."}
    except Exception as e:
        return {"status": f"❌ Erro ao aprender: {e}"}

# =====================================================
# 🔹 Status geral
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
