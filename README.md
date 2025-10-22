
# TrafficLaw AI — Starter (FastAPI + Static Frontend)

Tema vermelho e preto, com dashboard inicial semelhante ao seu mock.
Pronto para subir no Railway.

## Rodar localmente
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```
Acesse: http://localhost:8000

## Deploy no Railway (via GitHub)
1. Crie um repositório e suba estes arquivos.
2. No Railway, crie um novo projeto > Deploy from GitHub > escolha o repo.
3. Railway detecta Python pelos `requirements.txt` e usa o `Procfile`.
4. Depois do deploy, abra a URL pública.

## Deploy no Railway (CLI opcional)
```bash
railway login
railway init
railway up
```

## Estrutura
- app/main.py      → FastAPI servindo o frontend e rotas mock
- frontend/*       → HTML/CSS/JS do dashboard
- Procfile         → Comando de inicialização na plataforma
- requirements.txt → Dependências
```
