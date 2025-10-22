
# IA Advogada de Trânsito — Monorepo (Offline/MVP)

Este é um MVP **offline** pronto para rodar localmente e fazer deploy no Railway.
Inclui:
- **Backend FastAPI** (Python 3.11) com endpoints principais, RAG simples (FAISS), gerador DOCX, memória em SQLite/Postgres, e estrutura para plugar **llama.cpp** local.
- **Frontend React (Vite)** com tema vermelho/preto (MVP).
- **Dockerfiles** + `supervisord` para subir API e (opcional) servidor `llama.cpp`.
- **Scripts** úteis (ingestão de arquivos, extração de códigos MBFT, seed).

> **Observação**: Este zip traz um gerador de texto *offline de exemplo* (rule-based).
> Para LLM real sem API externa, plugue `llama.cpp` no arquivo `backend/app/llm/llama_server.py`
> e posicione o modelo GGUF em `/data/models/model.gguf`.

## Rodando local (sem Docker)

1. Requisitos: Python 3.11+
2. Crie ambiente e instale deps:
   ```bash
   cd backend
   python -m venv .venv && source .venv/bin/activate
   pip install -r requirements.txt
   ```
3. Copie `.env.example` para `.env` e ajuste o que precisar.
4. Opcional: inicializar banco (SQLite por padrão):
   ```bash
   python -m backend.app.db.init
   ```
5. Inicie a API:
   ```bash
   uvicorn backend.app.main:app --reload --port 8000
   ```
6. Frontend:
   ```bash
   cd ../frontend
   npm install
   npm run dev
   ```

## Docker / Railway (resumo)
- `docker/Dockerfile.backend` constrói imagem com FastAPI + supervisord.
- Configure variáveis no Railway e mapeie um volume para `/data`.
- Processo web: `supervisord -c /app/docker/supervisord.conf`.

## RAG e Memória (MVP)
- Vetores: FAISS (arquivo) em `/data/vectors`.
- Memória: SQLite (`/data/app.db`) por padrão; Postgres via `DATABASE_URL`.
- Ingestão: `scripts/ingest_files.py --path ./meus_pdfs`.

## Geração DOCX
- Endpoint `POST /documents/generate` cria um DOCX básico com seções:
  Fatos, Direito, Jurisprudências, Pedidos, Conclusão.

## Estrutura
Veja a árvore de pastas no repositório. Este MVP é base sólida para expandir.
