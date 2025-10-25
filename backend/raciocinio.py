import sqlite3
import torch
from sentence_transformers import SentenceTransformer, util
from transformers import AutoTokenizer, AutoModelForCausalLM

# Caminho do banco de conhecimento
DB_PATH = "backend/db/conhecimento.db"

# ========================================
# 🔹 Carregamento de modelos (feito 1x só)
# ========================================
print("🧠 Carregando modelos de linguagem...")

# Modelo de embeddings leve e rápido
embedder = SentenceTransformer("all-MiniLM-L6-v2")

# Modelo de raciocínio (pode trocar por 'microsoft/phi-2' se quiser mais robusto)
tokenizer = AutoTokenizer.from_pretrained("TinyLlama/TinyLlama-1.1B-Chat-v1.0")
model = AutoModelForCausalLM.from_pretrained("TinyLlama/TinyLlama-1.1B-Chat-v1.0")

device = "cuda" if torch.cuda.is_available() else "cpu"
model.to(device)

print("✅ Modelos carregados com sucesso!\n")


# ========================================
# 🔹 Consulta semântica ao banco de dados
# ========================================
def consultar_base_semantica(pergunta: str, top_k: int = 3) -> str:
    """Busca os textos mais relevantes com base em similaridade semântica"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("SELECT conteudo FROM conhecimento LIMIT 500")
        textos = [row[0] for row in cur.fetchall()]
        conn.close()

        if not textos:
            return "⚠️ Base de conhecimento vazia."

        # Cria embeddings da pergunta e dos textos
        emb_pergunta = embedder.encode(pergunta, convert_to_tensor=True)
        emb_textos = embedder.encode(textos, convert_to_tensor=True)

        # Busca os mais parecidos
        resultados = util.semantic_search(emb_pergunta, emb_textos, top_k=top_k)
        contexto = "\n\n".join([textos[r["corpus_id"]] for r in resultados[0]])

        return contexto.strip()

    except Exception as e:
        return f"❌ Erro ao consultar base semântica: {e}"


# ========================================
# 🔹 Geração de resposta
# ========================================
def gerar_resposta(pergunta: str) -> str:
    """Gera resposta usando contexto do banco local e modelo Transformer"""
    contexto = consultar_base_semantica(pergunta)

    if not contexto or contexto.startswith("⚠️") or contexto.startswith("❌"):
        return contexto

    prompt = f"""
Você é a Babix IA, uma assistente especialista em legislação de trânsito.
Responda de forma objetiva e cite as leis, artigos ou resoluções quando possível.

📘 Contexto:
{contexto}

❓ Pergunta:
{pergunta}

🧠 Resposta:
"""

    try:
        inputs = tokenizer(prompt, return_tensors="pt").to(device)
        outputs = model.generate(**inputs, max_new_tokens=300, temperature=0.7, do_sample=True)
        resposta = tokenizer.decode(outputs[0], skip_special_tokens=True)

        # Limpa o texto final
        resposta = resposta.split("🧠 Resposta:")[-1].strip()
        return resposta or "❌ Nenhuma resposta gerada."
    except Exception as e:
        return f"❌ Erro ao gerar resposta: {e}"
