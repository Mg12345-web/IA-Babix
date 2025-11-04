from fastapi import APIRouter, Body
from ..deps import client, OPENAI_MODEL, collection
from sentence_transformers import SentenceTransformer, util

router = APIRouter()

@router.post("/chat")
def chat_with_babix(message: str = Body(..., embed=True)):
    """Faz uma busca semântica e responde com o GPT."""
    # busca documentos relevantes
    results = collection.query(query_texts=[message], n_results=3)

    # junta os contextos
    contexts = "\n\n".join(results.get("documents", [[""]])[0])

    # prompt final
    prompt = f"""
Você é a IA Babix, especialista em Direito de Trânsito.
Use o contexto abaixo para responder de forma precisa e explicativa.

Contexto:
{contexts}

Pergunta do usuário:
{message}

Responda de forma natural e fundamentada:
"""

    completion = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
    )

    return {
        "message": message,
        "context_used": len(contexts.split()),
        "response": completion.choices[0].message.content,
    }
