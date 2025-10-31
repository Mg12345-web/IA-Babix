#!/bin/bash
set -e

echo "=============================="
echo "🚀 Iniciando Babix IA (modo produção, sem Ollama)..."
echo "=============================="

# Inicia o aprendizado em segundo plano (não bloqueia o container)
if [ -f "backend/aprendizado.py" ]; then
  echo "🧠 Inicializando aprendizado em background..."
  python3 backend/aprendizado.py &
fi

# Inicia o servidor FastAPI
echo "✅ Iniciando servidor FastAPI..."
exec uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8080}
