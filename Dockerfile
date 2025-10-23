# Usa imagem oficial do Python
FROM python:3.11-slim

# Define o diretório de trabalho
WORKDIR /app

# Copia os arquivos do projeto
COPY . .

# Instala as dependências
RUN cd Backend && pip install --no-cache-dir -r requirements.txt

# Expõe a porta
EXPOSE 8000

# Comando para iniciar o servidor
CMD ["uvicorn", "Backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
