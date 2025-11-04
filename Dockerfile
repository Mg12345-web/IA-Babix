# imagem leve de Python
FROM python:3.11-slim

# dependências de sistema mínimas
RUN apt-get update && apt-get install -y build-essential && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# copiar reqs primeiro (cache de camadas)
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# copiar projeto
COPY backend ./backend
COPY dados ./dados
COPY .env.example ./.env.example

# porta exposta (Railway define dinamicamente)
EXPOSE 8000

COPY frontend ./frontend

# comando de inicialização com variável de ambiente dinâmica
CMD ["sh", "-c", "uvicorn backend.app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
