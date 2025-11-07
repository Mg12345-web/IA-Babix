from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import os
from openai import OpenAI
import chromadb
from sentence_transformers import SentenceTransformer

router = APIRouter()

# 🔹 Conexão com Chroma e Modelos
CHROMA_DIR = os.getenv("CHROMA_DIR", "./dados/chroma")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    raise ValueError("❌ Variável OPENAI_API_KEY não configurada")

client = OpenAI(api_key=OPENAI_API_KEY)
chroma = chromadb.Client(chromadb.config.Settings(persist_directory=CHROMA_DIR))
embedder = SentenceTransformer("all-MiniLM-L6-v2")

# 🔹 Schema para requisição
class ChatRequest(BaseModel):
    message: str

@router.post("/chat")
def chat(req: ChatRequest):
    try:
        query = req.message.strip()
        if not query:
            raise HTTPException(status_code=400, detail="Mensagem vazia.")

        # 1️⃣ Buscar contexto no Chroma
        collections = chroma.list_collections()
        if not collections:
            return {"response": "Nenhum conhecimento foi indexado ainda."}

        collection = chroma.get_or_create_collection("babix_docs")
        query_emb = embedder.encode([query]).tolist()[0]

        results = collection.query(
            query_embeddings=[query_emb],
            n_results=3
        )

        docs = results.get("documents", [[]])[0]
        context = "\n\n".join(docs) if docs else "Nenhum contexto relevante encontrado."

        # 2️⃣ Geração de resposta com contexto
        prompt = f"""
        Você é a Babix, uma IA jurídica especializada em Direito de Trânsito.
        Responda de forma clara, citando a base de conhecimento quando relevante.
        
        Pergunta do usuário:
        {query}

        Contexto dos documentos:
        {context}
        """

        completion = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": "Você é uma assistente jurídica da MG Multas."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7
        )

        answer = completion.choices[0].message.content.strip()
        return {
            "response": answer,
            "context_used": len(docs)
        }

    except Exception as e:
        return {"error": str(e)}
