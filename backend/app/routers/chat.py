from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer
import chromadb
import os
from openai import OpenAI
import tiktoken

router = APIRouter()

# Configurações principais
CHROMA_DIR = os.getenv("CHROMA_DIR", "./dados/chroma")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Cliente OpenAI
client = OpenAI(api_key=OPENAI_API_KEY)

# Token counter
encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")

def get_chroma_client():
    """Conecta ao ChromaDB persistente"""
    return chromadb.PersistentClient(path=CHROMA_DIR)

def get_embedder():
    """Carrega modelo de embedding"""
    return SentenceTransformer("all-MiniLM-L6-v2")

def truncate_text(text, max_tokens=1000):
    """Trunca texto para não exceder max_tokens"""
    tokens = encoding.encode(text)
    if len(tokens) > max_tokens:
        truncated = encoding.decode(tokens[:max_tokens])
        return truncated + "..."
    return text

class ChatRequest(BaseModel):
    message: str

@router.post("/chat")
async def chat(req: ChatRequest):
    """
    Endpoint de chat com RAG otimizado
    """
    try:
        query = req.message.strip()
        
        if not query:
            raise HTTPException(status_code=400, detail="Mensagem vazia.")
        
        # 🔍 Conectar ao ChromaDB
        chroma_client = get_chroma_client()
        
        # Tentar obter a coleção existente
        try:
            collection = chroma_client.get_collection("babix_docs")
        except Exception as e:
            print(f"❌ Coleção não encontrada: {e}")
            return {
                "response": "⚠️ Nenhum documento foi indexado ainda. Clique em 'Fazer Ingestão' primeiro."
            }
        
        # Verificar quantos documentos estão indexados
        count = collection.count()
        print(f"📚 Documentos na coleção: {count}")
        
        if count == 0:
            return {
                "response": "⚠️ Coleção vazia. Faça a ingestão de PDFs primeiro."
            }
        
        # 🔍 Buscar documentos similares (pega apenas 2 para economizar tokens)
        embedder = get_embedder()
        query_embedding = embedder.encode(query)
        
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=2  # Reduzido de 3 para 2
        )
        
        # Verificar se encontrou resultados
        if not results or not results.get("documents") or len(results["documents"][0]) == 0:
            print("⚠️ Nenhum documento similar encontrado")
            return {
                "response": "Desculpe, não encontrei informações relevantes sobre sua pergunta."
            }
        
        # 📄 Extrair contextos e truncar
        documents = results["documents"][0]
        metadatas = results["metadatas"][0] if results.get("metadatas") else []
        
        # Truncar cada documento para max 800 tokens
        truncated_docs = [truncate_text(doc, max_tokens=800) for doc in documents]
        context = "\n\n---\n\n".join(truncated_docs)
        
        # Verificar tamanho do contexto
        context_tokens = len(encoding.encode(context))
        print(f"📊 Tokens do contexto: {context_tokens}")
        
        if context_tokens > 2000:
            # Se ainda for grande, truncar o contexto inteiro
            context = truncate_text(context, max_tokens=1500)
            print("⚠️ Contexto muito grande, truncado para 1500 tokens")
        
        # 🤖 Chamar GPT com contexto (RAG)
        system_message = """Você é um assistente jurídico especializado em direito de trânsito brasileiro.
Use as informações dos documentos fornecidos para responder.
Seja conciso e objetivo. Máximo 200 palavras."""
        
        user_message = f"""Informações dos documentos:
{context}

Pergunta do usuário: {query}

Responda com base nas informações acima."""
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message}
            ],
            temperature=0.5,
            max_tokens=300  # Reduzido para economizar
        )
        
        answer = response.choices[0].message.content
        
        # Adicionar fontes
        sources = [m.get("name", "Documento")[:40] for m in metadatas if m]  # Apenas 40 chars
        sources_text = f"\n\n📚 Fontes: {', '.join(set(sources))}" if sources else ""
        
        return {
            "response": answer + sources_text
        }
        
    except Exception as e:
        print(f"❌ Erro no chat: {str(e)}")
        
        return {
            "response": f"Desculpe, tivemos um erro ao processar sua pergunta. Tente novamente em alguns segundos."
        }
