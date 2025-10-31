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

# Copia todos os arquivos do projeto
COPY . /app

# Instala dependências Python
RUN pip install --no-cache-dir -r requirements.txt

# Expõe a porta usada pela aplicação
EXPOSE 8080

# Comando de inicialização (executado via Procfile)
ENTRYPOINT ["bash", "start.sh"]
