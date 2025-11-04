# Babix (zero-base)

## Setup local
1. `cp .env.example .env` e preencha `OPENAI_API_KEY`.
2. `python -m venv .venv && source .venv/bin/activate` (Windows: `.\.venv\Scripts\activate`)
3. `pip install -r requirements.txt`
4. `uvicorn backend.app.main:app --reload`

Acesse: `http://localhost:8000/api/health` → `{"status":"ok"}`

## Estrutura
- `/dados`: sua base de arquivos (mantido).
- `Chroma` persiste em `./dados/chroma`.

## Próximos passos
- Criar `routers/ingest.py` para varrer `/dados`, gerar embeddings e popular a coleção.
- Criar `routers/chat.py` para RAG (recupera contextos da Chroma + GPT).
