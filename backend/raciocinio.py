import os
import sqlite3
from sentence_transformers import SentenceTransformer, util
from openai import OpenAI

# Caminho do banco
DB_PATH = "backend/db/conhecimento.db"

print("🧠 Iniciando Babix Raciocínio com GPT-4o-mini...")

# Modelo de embeddings leve e rápido
embedder = SentenceTransformer("all-MiniLM-L6-v2")

# Cliente OpenAI (usa variável de ambiente no Railway)
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

print("✅ Babix Raciocínio inicializado com sucesso!\n")

# ============================================================
# 🔹 Consulta semântica ao banco
# ============================================================
def consultar_base_semantica(pergunta: str, top_k: int = 3) -> str:
    """Busca os textos mais relevantes no banco local (semântico)."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("SELECT conteudo FROM fichas LIMIT 300")
        textos = [row[0] for row in cur.fetchall()]
        conn.close()

        if not textos:
            return "⚠️ Base de conhecimento vazia."

        emb_pergunta = embedder.encode(pergunta, convert_to_tensor=True)
        emb_textos = embedder.encode(textos, batch_size=16, convert_to_tensor=True)
        resultados = util.semantic_search(emb_pergunta, emb_textos, top_k=top_k)
        contexto = "\n\n".join([textos[r["corpus_id"]] for r in resultados[0]])

        return contexto.strip()
    except Exception as e:
        return f"❌ Erro ao consultar base semântica: {e}"

# ============================================================
# 🔹 Geração de resposta (usando GPT)
# ============================================================
def gerar_resposta(pergunta: str) -> str:
    """Gera a resposta final usando contexto local + GPT."""
    contexto = consultar_base_semantica(pergunta)

    if not contexto or contexto.startswith(("⚠️", "❌")):
        return contexto

    # Prompt antialucinação
    prompt = f"""
Você é a Babix IA, uma assistente especialista em legislação de trânsito.

Use APENAS o conteúdo do contexto abaixo para responder.
Se a resposta não estiver no contexto, diga exatamente:
"⚠️ A informação solicitada não está presente na base de conhecimento da Babix IA."

Regras:
1️⃣ Nunca invente.
2️⃣ Cite sempre a base legal (CTB, Resoluções CONTRAN, MBFT etc.).
3️⃣ Seja objetiva, técnica e com linguagem jurídica.

📘 Contexto:
{contexto}

❓ Pergunta:
{pergunta}

Responda no formato:
📘 Base legal:
🧩 Explicação:
📎 Fonte:
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            top_p=0.8,
            max_tokens=600
        )

        resposta = response.choices[0].message.content.strip()
        return resposta

    except Exception as e:
        return f"❌ Erro ao gerar resposta via GPT: {e}"
