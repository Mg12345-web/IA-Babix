#!/bin/bash
set -e

echo "=============================="
echo "🚀 Iniciando Babix IA (modo produção, sem Ollama)..."
echo "=============================="

# Inicializa o banco e aprendizado básico
if [ -f "backend/aprendizado.py" ]; then
  echo "🧠 Preparando banco e aprendizado inicial..."
  python3 backend/aprendizado.py || echo "⚠️ Erro ao inicializar aprendizado (prosseguindo mesmo assim)."
fi

# Inicia o servidor FastAPI
echo "✅ Iniciando servidor FastAPI..."
exec uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8080}
