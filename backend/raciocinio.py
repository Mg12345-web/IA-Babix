# backend/raciocinio.py

import os
import sqlite3
from sentence_transformers import SentenceTransformer, util
from openai import OpenAI

# Inicializa modelos e API
embedder = SentenceTransformer("all-MiniLM-L6-v2")
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

DB_PATH = "backend/db/conhecimento.db"

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

    # Calcula embeddings e similaridade
    pergunta_emb = embedder.encode(pergunta, convert_to_tensor=True)
    textos, scores = [], []

    for texto, emb_blob in registros:
        try:
            emb = eval(emb_blob) if isinstance(emb_blob, str) else emb_blob
            score = util.pytorch_cos_sim(pergunta_emb, emb)[0][0].item()
            textos.append((score, texto))
        except:
            continue

    textos = sorted(textos, reverse=True)[:limite]
    contexto = "\n\n".join([t[1] for t in textos])
    return contexto or "⚠️ Nenhum contexto relevante encontrado."

def gerar_resposta(pergunta):
    """Raciocina usando GPT-5, restrito à base local"""
    contexto = buscar_contexto(pergunta)

    prompt = f"""
Você é a Babix IA, uma assistente jurídica especializada em direito de trânsito.
Use APENAS as informações do contexto abaixo para responder. 
Se algo não estiver no contexto, diga claramente que não sabe.

📚 Contexto extraído da base:
{contexto}

❓ Pergunta do usuário:
{pergunta}

💬 Resposta:
"""

    resposta = client.chat.completions.create(
        model="gpt-5-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.4,
        max_tokens=400,
    )

    return resposta.choices[0].message.content.strip()
