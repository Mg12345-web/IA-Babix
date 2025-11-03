#!/bin/bash
set -e

echo "=============================="
echo "🚀 Iniciando Babix IA (modo produção, sem Ollama)..."
echo "=============================="

# Inicia o aprendizado inicial em background
if [ -f "backend/aprendizado.py" ]; then
  echo "🧠 Inicializando aprendizado em background..."
  python3 backend/aprendizado.py &
fi

# Inicia o watcher em background (monitora /dados)
if [ -f "backend/watcher.py" ]; then
  echo "👀 Iniciando monitor de aprendizado automático..."
  python3 backend/watcher.py &
fi

# Inicia o servidor FastAPI
echo "✅ Iniciando servidor FastAPI..."
exec python3 -m uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8080} --timeout-keep-alive 75
