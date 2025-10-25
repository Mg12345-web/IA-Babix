# ------------------------------------------------------------
# 🧠 Babix IA — Ambiente de produção (sem Ollama)
# ------------------------------------------------------------

FROM python:3.11-slim

# Instala dependências básicas
RUN apt-get update && apt-get install -y \
    build-essential \
    libsqlite3-dev \
    git \
    && rm -rf /var/lib/apt/lists/*

# Define diretório de trabalho
WORKDIR /app

# Copia os arquivos
COPY . /app

# Instala dependências Python
RUN pip install --no-cache-dir -r requirements.txt

# Porta padrão da FastAPI
EXPOSE 8000

# Comando de inicialização
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
