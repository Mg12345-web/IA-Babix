from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer, util
import chromadb
from chromadb.config import Settings
import os
import openai

router = APIRouter()

# Configurações principais
CHROMA_DIR = os.getenv("CHROMA_DIR", "./dados/chroma")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

embedder = SentenceTransformer("all-MiniLM-L6-v2")

client = chromadb.Client(Settings(persist_directory=CHROMA_DIR))
collection = client.get_or_create_collection("babix_docs")

openai.api_key = OPENAI_API_KEY

class ChatRequest(BaseModel):
    message: str

@router.post("/chat")
async def chat(req: ChatRequest):
    query = req.message.strip()
    if not query:
        raise HTTPException(status_code=400, detail="Mensagem vazia.")

    # 🔍 Busca semântica no banco Chroma
    results = collection.query(
        query_texts=[query],
        n_results=3
    )

    if not results or not results.get("documents") or not results["documents"][0]:
        return {"response": "Nenhum conhecimento foi indexado ainda."}

    contextos = "\n\n".join(results["documents"][0])

    # 💬 Prompt contextualizado
    prompt = f"""
Você é a Babix, uma IA especializada em Direito de Trânsito brasileiro.
Responda com base apenas no contexto abaixo (se houver), e seja clara e direta.

Contexto:
{contextos}

Pergunta do usuário:
{query}
"""

    try:
        completion = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Você é uma assistente jurídica chamada Babix, especialista em Direito de Trânsito."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.5,
            max_tokens=500
        )

        resposta = completion.choices[0].message.content.strip()
        return {"response": resposta}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
