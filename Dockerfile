# ======================================================
# 🧠 Babix IA — IA Autônoma com Ollama (instalação direta)
# Compatível com Railway - Outubro/2025
# ======================================================

FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

# -------------------------
# 🔹 Instala dependências
# -------------------------
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    python3 \
    python3-pip \
    sqlite3 \
    git \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# -------------------------
# 🔹 Instala Ollama manualmente (última versão estável)
# -------------------------
RUN wget https://github.com/ollama/ollama/releases/download/v0.3.13/ollama-linux-amd64.tgz && \
    tar -xvzf ollama-linux-amd64.tgz && \
    mv ollama /usr/local/bin/ && \
    rm ollama-linux-amd64.tgz

# -------------------------
# 🔹 Define diretório de trabalho
# -------------------------
WORKDIR /app

# Copia todos os arquivos
COPY . .

# -------------------------
# 🔹 Instala dependências Python
# -------------------------
RUN pip install --no-cache-dir -r requirements.txt

# -------------------------
# 🔹 (Opcional) baixa modelo local para cache
# -------------------------
RUN ollama pull phi3 || true

# -------------------------
# 🔹 Define variáveis e porta
# -------------------------
ENV PORT=8080
EXPOSE 8080

# -------------------------
# 🔹 Comando de inicialização
# -------------------------
CMD ["bash", "start.sh"]
