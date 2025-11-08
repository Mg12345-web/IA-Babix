from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer
import chromadb
import os
import re
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

def truncate_text(text, max_tokens=800):
    """Trunca texto para não exceder max_tokens"""
    tokens = encoding.encode(text)
    if len(tokens) > max_tokens:
        truncated = encoding.decode(tokens[:max_tokens])
        return truncated + "..."
    return text

def extract_codes(query):
    """Extrai códigos/números da query (ex: 516-91, art 165)"""
    codes = re.findall(r'\d{3}-\d{2}', query)
    articles = re.findall(r'(?:art(?:igo)?\.?\s*)?(\d{1,3})', query, re.IGNORECASE)
    return {"codes": codes, "articles": articles}

class ChatRequest(BaseModel):
    message: str

@router.post("/chat")
async def chat(req: ChatRequest):
    """
    Endpoint de chat com RAG melhorado
    Sistema de prompt profissional para respostas como um professor
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
        
        # 🔍 Detectar códigos/artigos
        entities = extract_codes(query)
        print(f"🔢 Entidades detectadas: {entities}")
        
        # Enriquecer query com termos relacionados
        query_enriched = query
        if entities["codes"]:
            query_enriched += " " + " ".join([f"código {code} infração" for code in entities["codes"]])
        if entities["articles"]:
            query_enriched += " " + " ".join([f"artigo {art} CTB" for art in entities["articles"]])
        
        # 🔍 Buscar documentos similares (aumentado para 5 para melhor contexto)
        embedder = get_embedder()
        query_embedding = embedder.encode(query_enriched)
        
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=5  # Aumentado de 3 para 5
        )
        
        # Verificar se encontrou resultados
        if not results or not results.get("documents") or len(results["documents"][0]) == 0:
            print("⚠️ Nenhum documento similar encontrado")
            return {
                "response": "Desculpe, não encontrei informações específicas sobre sua pergunta nos documentos indexados. Você poderia reformular ou ser mais específico?"
            }
        
        # 📄 Extrair contextos e truncar
        documents = results["documents"][0]
        metadatas = results["metadatas"][0] if results.get("metadatas") else []
        
        # Truncar cada documento
        truncated_docs = [truncate_text(doc, max_tokens=600) for doc in documents]
        context = "\n\n─────────────────────────\n\n".join(truncated_docs)
        
        # Verificar tamanho do contexto
        context_tokens = len(encoding.encode(context))
        print(f"📊 Tokens do contexto: {context_tokens}")
        
        if context_tokens > 3000:
            context = truncate_text(context, max_tokens=2500)
            print("⚠️ Contexto truncado para 2500 tokens")
        
        # 🎓 PROMPT MELHORADO - Como um Professor
        system_message = """Você é a Babix, uma especialista em legislação de trânsito brasileiro com mais de 10 anos de experiência.

# SUA PERSONALIDADE:
- Você é uma PROFESSORA dedicada, não apenas um buscador de textos
- Você ESTUDOU profundamente todo o CTB (Código de Trânsito Brasileiro) e MBFT (Manual Brasileiro de Fiscalização de Trânsito)
- Você explica de forma DIDÁTICA, clara e acessível
- Você tem PACIÊNCIA para explicar conceitos complexos de forma simples
- Você sempre CITA suas fontes (artigos, códigos, resoluções)

# COMO VOCÊ DEVE RESPONDER:

1. **LEIA COM ATENÇÃO** todos os documentos fornecidos
2. **INTERPRETE** o contexto, não apenas copie trechos
3. **ORGANIZE** sua resposta de forma estruturada:
   - Comece com uma resposta direta e clara (1-2 frases)
   - Depois explique os detalhes
   - Finalize com informações práticas (se aplicável)
4. **CITE** sempre a fonte específica (artigo, código, página)
5. **USE EXEMPLOS** práticos quando possível
6. **SEJA PRECISA** - se não souber, ADMITA

# O QUE VOCÊ NUNCA DEVE FAZER:

❌ Inventar informações que não estão nos documentos
❌ Copiar e colar texto sem explicar
❌ Misturar informações de contextos diferentes sem deixar claro
❌ Dar respostas vagas ou genéricas quando tem informação específica
❌ Ignorar a pergunta do usuário

# FORMATO DA RESPOSTA:

**Resposta Direta:** (1-2 frases resumindo a resposta)

**Detalhes:**
- Explicação completa e didática
- Cite artigos/códigos específicos
- Use exemplos se ajudar

**Fonte:** (sempre cite de onde veio a informação)

Lembre-se: Você é uma PROFESSORA, não uma copiadora de textos!"""

        user_message = f"""# DOCUMENTOS RELEVANTES:

{context}

─────────────────────────

# PERGUNTA DO USUÁRIO:
{query}

─────────────────────────

Agora, como uma professora especialista em trânsito:

1. LEIA todos os documentos acima com atenção
2. IDENTIFIQUE qual(is) documento(s) responde(m) à pergunta
3. INTERPRETE e EXPLIQUE de forma didática
4. Se os documentos NÃO responderem à pergunta, diga claramente

Sua resposta:"""
        
        # 🤖 Chamar GPT com prompt melhorado
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message}
            ],
            temperature=0.3,  # Baixo para mais precisão
            max_tokens=600,  # Aumentado para respostas mais completas
            top_p=0.9
        )
        
        answer = response.choices[0].message.content
        
        # Adicionar fontes de forma mais clara
        sources = []
        for meta in metadatas:
            if meta:
                name = meta.get("name", "Documento")
                chunk = meta.get("chunk_id", "")
                page = meta.get("page", "")
                
                if chunk != "":
                    sources.append(f"{name} (chunk {chunk}, pág. {page})")
                else:
                    sources.append(name)
        
        # Remover duplicatas mantendo ordem
        unique_sources = list(dict.fromkeys(sources))
        sources_text = f"\n\n📚 **Fontes consultadas:** {', '.join(unique_sources[:3])}" if unique_sources else ""
        
        return {
            "response": answer + sources_text
        }
        
    except Exception as e:
        print(f"❌ Erro no chat: {str(e)}")
        import traceback
        traceback.print_exc()
        
        return {
            "response": "Desculpe, tivemos um erro ao processar sua pergunta. Por favor, tente novamente ou reformule sua pergunta."
        }
