import sqlite3
import re
from difflib import SequenceMatcher

DB_PATH = "backend/db/conhecimento.db"

# ===============================================
# 🔹 Busca o texto do MBFT armazenado no banco
# ===============================================
def buscar_conhecimento():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT conteudo FROM conhecimento WHERE origem='MBFT'")
    resultado = cursor.fetchone()
    conn.close()
    return resultado[0] if resultado else ""

# ===============================================
# 🔹 Similaridade textual simples
# ===============================================
def similaridade(a, b):
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()

# ===============================================
# 🔹 Explicação interpretativa de uma ficha MBFT
# ===============================================
def explicar_ficha(codigo, texto_base):
    """
    Gera explicação estruturada e interpretada de uma ficha MBFT (ex: 596-70)
    """
    padrao = rf"{codigo}[\s\S]*?(?=\n\d{{3}}-\d{{2}}|\Z)"  # trecho entre fichas
    trecho = re.search(padrao, texto_base)

    if not trecho:
        return f"⚠️ Ficha {codigo} não encontrada no MBFT."

    conteudo = trecho.group().strip()
    explicacao = []
    explicacao.append(f"🧾 **FICHA {codigo} — Explicação Completa**")

    # Amparo legal
    art = re.search(r"Art\.\s*\d+[^\n]*", conteudo)
    if art:
        explicacao.append(f"⚖️ **Amparo Legal:** {art.group().strip()}")

    # Tipificação
    tipificacao = re.search(r"(Tipificação|Descrição)[^\n]*\n([^\n]+)", conteudo)
    if tipificacao:
        explicacao.append(f"🚗 **Descrição / Tipificação:** {tipificacao.group(2).strip()}")

    # Gravidade
    gravidade = re.search(r"Gravidade\s*[:\-]?\s*(\w+)", conteudo)
    if gravidade:
        explicacao.append(f"💣 **Gravidade:** {gravidade.group(1)}")

    # Penalidade
    penalidade = re.search(r"Penalidade\s*[:\-]?\s*([^\n]+)", conteudo)
    if penalidade:
        explicacao.append(f"💰 **Penalidade:** {penalidade.group(1).strip()}")

    # Pontuação
    pontos = re.search(r"Pontuação\s*[:\-]?\s*(\d+)", conteudo)
    if pontos:
        explicacao.append(f"🏁 **Pontuação:** {pontos.group(1)} pontos")

    # Indicações complementares
    if "quando autuar" in conteudo.lower():
        explicacao.append("🟥 **Quando autuar:** há descrição específica na ficha.")
    if "quando não autuar" in conteudo.lower():
        explicacao.append("🟩 **Quando não autuar:** existem exceções descritas na ficha.")

    explicacao.append("\n🧠 **Resumo interpretativo:**")
    explicacao.append(
        f"A infração **{codigo}** refere-se a uma conduta prevista no CTB e descrita no MBFT. "
        f"É normalmente de natureza **gravíssima**, envolvendo risco à segurança viária. "
        f"O agente deve observar as condições de sinalização e contexto antes da autuação."
    )

    return "\n".join(explicacao)

# ===============================================
# 🔹 Função principal: gerar resposta do chat
# ===============================================
def gerar_resposta(pergunta):
    texto_base = buscar_conhecimento()
    if not texto_base:
        return "Ainda não tenho conhecimento carregado do MBFT."

    # Detecta código de ficha (ex: 596-70)
    codigo_match = re.search(r"\b\d{3}-\d{2}\b", pergunta)
    if codigo_match:
        codigo = codigo_match.group()
        return explicar_ficha(codigo, texto_base)

    # Caso não seja uma ficha, faz busca semântica normal
    blocos = re.split(r'(?<=[.!?])\s+', texto_base)
    melhor_trecho = max(blocos, key=lambda t: similaridade(t, pergunta))

    resposta = f"📘 Baseando-me no MBFT:\n{melhor_trecho.strip()}"
    return resposta
