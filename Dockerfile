# ======================================================
# 🧠 Babix IA — IA Autônoma com Ollama (Caminho 3)
# ======================================================

# Imagem base (Ubuntu + Python)
FROM ubuntu:22.04

# Evita prompts interativos
ENV DEBIAN_FRONTEND=noninteractive

# Atualiza sistema e instala dependências
RUN apt-get update && apt-get install -y \
    curl \
    python3 \
    python3-pip \
    sqlite3 \
    git \
    && rm -rf /var/lib/apt/lists/*

# ======================================================
# 🔹 Instalação do Ollama
# ======================================================
RUN curl -fsSL https://ollama.com/install.sh | sh

# ======================================================
# 🔹 Define diretório de trabalho
# ======================================================
WORKDIR /app

# Copia os arquivos do projeto
COPY . .

# ======================================================
# 🔹 Instala dependências Python
# ======================================================
RUN pip install --no-cache-dir -r requirements.txt

# ======================================================
# 🔹 Baixa o modelo local (Phi-3 é leve e rápido)
# ======================================================
RUN ollama pull phi3

# ======================================================
# 🔹 Define variáveis padrão
# ======================================================
ENV PORT=8080
EXPOSE 8080

# ======================================================
# 🔹 Inicia Ollama + FastAPI via script
# ======================================================
CMD ["bash", "start.sh"]
