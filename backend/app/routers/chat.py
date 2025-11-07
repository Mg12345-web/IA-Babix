from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer
import chromadb
import os
from openai import OpenAI

router = APIRouter()

# Configurações principais
CHROMA_DIR = os.getenv("CHROMA_DIR", "./dados/chroma")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Cliente OpenAI
client = OpenAI(api_key=OPENAI_API_KEY)

# Inicializar Chroma
def get_chroma_client():
    """Conecta ao ChromaDB persistente"""
    return chromadb.PersistentClient(path=CHROMA_DIR)

def get_embedder():
    """Carrega modelo de embedding"""
    return SentenceTransformer("all-MiniLM-L6-v2")

class ChatRequest(BaseModel):
    message: str

@router.post("/chat")
async def chat(req: ChatRequest):
    """
    Endpoint de chat com RAG:
    1. Busca documentos relevantes no ChromaDB
    2. Envia para GPT com contexto
    3. Retorna resposta
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
        
        # 🔍 Buscar documentos similares
        embedder = get_embedder()
        query_embedding = embedder.encode(query)
        
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=3
        )
        
        # Verificar se encontrou resultados
        if not results or not results.get("documents") or len(results["documents"][0]) == 0:
            print("⚠️ Nenhum documento similar encontrado")
            return {
                "response": "Desculpe, não encontrei informações relevantes sobre sua pergunta nos documentos indexados."
            }
        
        # 📄 Extrair contextos encontrados
        documents = results["documents"][0]
        metadatas = results["metadatas"][0] if results.get("metadatas") else []
        
        # Concatenar contextos
        context = "\n\n".join(documents)
        
        # 🤖 Chamar GPT com contexto (RAG)
        system_message = """Você é um assistente jurídico especializado em direito de trânsito brasileiro.
Use as informações dos documentos fornecidos para responder as perguntas.
Se a informação não estiver nos documentos, diga claramente.
Sempre cite a fonte quando possível."""
        
        user_message = f"""Documentos relevantes:
{context}

Pergunta: {query}

Responda com base nos documentos acima."""
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message}
            ],
            temperature=0.5,
            max_tokens=500
        )
        
        answer = response.choices[0].message.content
        
        # Adicionar fontes
        sources = [m.get("name", "Documento") for m in metadatas if m]
        sources_text = f"\n\n📚 **Fontes:** {', '.join(set(sources))}" if sources else ""
        
        return {
            "response": answer + sources_text
        }
        
    except Exception as e:
        print(f"❌ Erro no chat: {str(e)}")
        import traceback
        traceback.print_exc()
        
        return {
            "response": f"Erro ao processar sua pergunta: {str(e)}"
        }
