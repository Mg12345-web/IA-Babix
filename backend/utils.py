# backend/utils.py
import os
import json
from datetime import datetime


# =========================
# 📘 FUNÇÃO: REGISTRAR LOG
# =========================
def log_action(usuario_id: str, acao: str, detalhes: str = ""):
    """
    Grava logs de ações da Babix IA em arquivo local (logs/actions.log).
    Cada linha contém data, ID do usuário, ação e detalhes.
    """
    pasta = "logs"
    os.makedirs(pasta, exist_ok=True)
    caminho_log = os.path.join(pasta, "actions.log")

    with open(caminho_log, "a", encoding="utf-8") as f:
        data = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        f.write(f"[{data}] {usuario_id} - {acao} - {detalhes}\n")


# ==================================
# 🧩 FUNÇÃO: LIMPAR TEXTO DE RESPOSTAS
# ==================================
def limpar_texto(texto: str) -> str:
    """
    Remove quebras de linha, espaços duplos e caracteres estranhos.
    Deixa o texto limpo para exibição e gravação no banco.
    """
    if not texto:
        return ""

    texto = texto.replace("\r", " ").replace("\n", " ")
    while "  " in texto:
        texto = texto.replace("  ", " ")
    texto = texto.strip()

    return texto


# ==================================
# 🧠 FUNÇÃO: AVALIAR MODO AVANÇADO
# ==================================
def verificar_modo_avancado(plano: str, contador_uso: int) -> dict:
    """
    Define se o usuário pode usar o modo avançado da Babix IA.
    """
    limites = {
        "basico": 0,
        "medio": 30,
        "ilimitado": 9999
    }

    limite = limites.get(plano, 0)
    restante = limite - contador_uso

    if restante <= 0:
        return {
            "permitido": False,
            "mensagem": "⚠️ Seu limite mensal de buscas avançadas foi atingido. Faça upgrade para o plano Ilimitado."
        }

    return {
        "permitido": True,
        "mensagem": f"✅ Você ainda pode realizar {restante} buscas avançadas este mês."
    }


# ==================================
# 🔎 FUNÇÃO: LER CONFIGURAÇÃO GLOBAL
# ==================================
def carregar_config():
    """
    Carrega o arquivo de configuração global (config.json),
    onde ficam parâmetros como chaves, limites e variáveis padrão.
    """
    caminho = "config.json"
    if not os.path.exists(caminho):
        return {}

    with open(caminho, "r", encoding="utf-8") as f:
        return json.load(f)


# ==================================
# 💾 FUNÇÃO: GARANTIR BANCO SQLITE
# ==================================
def ensure_db(caminho_db: str):
    """
    Garante que o banco SQLite exista e tenha as tabelas essenciais.
    Evita erros no primeiro start.
    """
    import sqlite3
    os.makedirs(os.path.dirname(caminho_db), exist_ok=True)

    conn = sqlite3.connect(caminho_db)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS memoria (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            topico TEXT,
            conteudo TEXT,
            criado_em DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS historico (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id TEXT,
            entrada TEXT,
            resposta TEXT,
            criado_em DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()


# ==================================
# 🧾 FUNÇÃO: FORMATAR RESPOSTAS JSON
# ==================================
def resposta_padrao(status: str, mensagem: str, dados: dict = None) -> dict:
    """
    Padroniza as respostas da API (JSON).
    """
    return {
        "status": status,
        "mensagem": mensagem,
        "dados": dados or {}
    }
