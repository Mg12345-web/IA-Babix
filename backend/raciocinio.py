import sqlite3
import re
from difflib import SequenceMatcher

DB_PATH = "backend/db/conhecimento.db"

def buscar_conhecimento():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT conteudo FROM conhecimento WHERE origem='MBFT'")
    resultado = cursor.fetchone()
    conn.close()
    return resultado[0] if resultado else ""

def similaridade(a, b):
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()

def gerar_resposta(pergunta):
    texto_base = buscar_conhecimento()
    if not texto_base:
        return "Ainda não tenho conhecimento carregado do MBFT."

    # divide texto em blocos para busca contextual
    blocos = re.split(r'(?<=[.!?])\s+', texto_base)
    melhor_trecho = max(blocos, key=lambda t: similaridade(t, pergunta))

    resposta = f"📘 Baseando-me no MBFT:\n{melhor_trecho.strip()}"
    return resposta
