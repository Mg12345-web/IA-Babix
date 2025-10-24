# ======================================================
# 🧠 Babix IA — IA Autônoma com Ollama (versão CPU-only)
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
    tar \
    && rm -rf /var/lib/apt/lists/*

# -------------------------
# 🔹 Instala Ollama (CPU-only)
# -------------------------
RUN wget https://github.com/ollama/ollama/releases/download/v0.3.13/ollama-linux-amd64.tgz && \
    tar -xvzf ollama-linux-amd64.tgz && \
    mv ./bin/ollama /usr/local/bin/ && \
    chmod +x /usr/local/bin/ollama && \
    rm -rf ollama-linux-amd64.tgz ./bin ./lib

# -------------------------
# 🔹 Define diretório de trabalho
# -------------------------
WORKDIR /app

# Copia todos os arquivos do projeto
COPY . .

# -------------------------
# 🔹 Instala dependências Python
# -------------------------
RUN pip install --no-cache-dir -r requirements.txt

# -------------------------
# 🔹 Baixa modelo local (modo seguro)
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
