# backend/raciocinio.py

import os
import sqlite3
from sentence_transformers import SentenceTransformer, util
from openai import OpenAI

# ==============================
# 🔹 Configurações iniciais
# ==============================
DB_PATH = "backend/db/conhecimento.db"
embedder = SentenceTransformer("all-MiniLM-L6-v2")
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


# ==============================
# 🔹 Busca no banco de conhecimento
# ==============================
def buscar_contexto(pergunta, limite=3):
    """Busca os trechos mais semelhantes à pergunta"""
    if not os.path.exists(DB_PATH):
        return "⚠️ Base de conhecimento não encontrada."

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT texto, embedding FROM conhecimento")
    registros = cur.fetchall()
    conn.close()

    if not registros:
        return "⚠️ Nenhum conhecimento indexado ainda."

    pergunta_emb = embedder.encode(pergunta, convert_to_tensor=True)
    resultados = []

    for texto, emb_str in registros:
        try:
            emb = eval(emb_str) if isinstance(emb_str, str) else emb_str
            score = util.pytorch_cos_sim(pergunta_emb, emb)[0][0].item()
            resultados.append((score, texto))
        except Exception as e:
            continue

    resultados = sorted(resultados, reverse=True)[:limite]
    contexto = "\n\n".join([r[1] for r in resultados])
    return contexto or "⚠️ Nenhum contexto relevante encontrado."


# ==============================
# 🔹 Geração de resposta (GPT-5)
# ==============================
def gerar_resposta(pergunta):
    """Usa GPT-5 para raciocinar, limitado ao contexto local"""
    contexto = buscar_contexto(pergunta)

    prompt = f"""
Você é a Babix IA, uma assistente jurídica especializada em direito de trânsito.
Responda APENAS com base no contexto abaixo. 
Se a resposta não estiver no contexto, diga: "Essa informação não está presente na base de conhecimento da Babix."

📚 Contexto:
{contexto}

❓ Pergunta:
{pergunta}

💬 Resposta:
"""

    try:
        resposta = client.chat.completions.create(
            model="gpt-5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.4,
            max_tokens=400,
        )
        return resposta.choices[0].message.content.strip()
    except Exception as e:
        return f"⚠️ Erro ao gerar resposta: {str(e)}"
