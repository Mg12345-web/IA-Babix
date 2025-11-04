# imagem base leve do Python
FROM python:3.11-slim

# instalar dependências do sistema necessárias
RUN apt-get update && apt-get install -y build-essential poppler-utils && rm -rf /var/lib/apt/lists/*

# definir diretório de trabalho
WORKDIR /app

# copiar dependências primeiro (cache)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# copiar o projeto completo
COPY backend ./backend
COPY frontend ./frontend
COPY dados ./dados
COPY .env.example ./.env.example

# garantir permissões de leitura
RUN chmod -R 755 /app/dados

# expor porta
EXPOSE 8000

# comando de execução
CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
