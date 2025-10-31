import sqlite3
import torch
from sentence_transformers import SentenceTransformer, util
from transformers import AutoTokenizer, AutoModelForCausalLM

# Caminho do banco
DB_PATH = "backend/db/conhecimento.db"

print("🧠 Carregando modelos de linguagem...")

# Embeddings (leve e rápido)
embedder = SentenceTransformer("all-MiniLM-L6-v2")

# Modelo de raciocínio (TinyLlama é pesado para Railway — use DistilGPT2)
try:
    tokenizer = AutoTokenizer.from_pretrained("distilgpt2")
    model = AutoModelForCausalLM.from_pretrained("distilgpt2")
except Exception as e:
    print(f"⚠️ Falha ao carregar modelo principal: {e}")
    model, tokenizer = None, None

device = "cuda" if torch.cuda.is_available() else "cpu"
try:
    if model:
        model.to(device)
except Exception:
    print("⚠️ Rodando apenas em CPU.")

print("✅ Modelos carregados com sucesso!\n")


# ============================================================
# 🔹 Consulta semântica ao banco
# ============================================================
def consultar_base_semantica(pergunta: str, top_k: int = 3) -> str:
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("SELECT conteudo FROM fichas LIMIT 200")
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
# 🔹 Geração de resposta
# ============================================================
def gerar_resposta(pergunta: str) -> str:
    contexto = consultar_base_semantica(pergunta)

    if not contexto or contexto.startswith(("⚠️", "❌")):
        return contexto

    prompt = f"""
Você é a Babix IA, assistente especialista em Direito de Trânsito.
Responda de forma objetiva e cite leis, artigos ou resoluções.

📘 Contexto:
{contexto}

❓ Pergunta:
{pergunta}

🧠 Resposta:
"""

    if not model or not tokenizer:
        return "⚠️ O modelo de raciocínio ainda não foi inicializado corretamente."

    try:
        inputs = tokenizer(prompt, return_tensors="pt").to(device)
        outputs = model.generate(**inputs, max_new_tokens=200, temperature=0.7, do_sample=True)
        resposta = tokenizer.decode(outputs[0], skip_special_tokens=True, clean_up_tokenization_spaces=True)
        resposta = resposta.split("🧠 Resposta:")[-1].strip()
        return resposta or "⚠️ Nenhuma resposta gerada."
    except Exception as e:
        return f"⚠️ Erro ao gerar resposta: {e}"
