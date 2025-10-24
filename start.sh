#!/bin/bash
echo "=============================="
echo "🚀 Iniciando Babix IA com Ollama local..."
echo "=============================="

# Inicia o servidor Ollama em segundo plano
ollama serve &

# Aguarda o Ollama inicializar
echo "⏳ Aguardando Ollama iniciar..."
sleep 8

# Testa se o modelo phi3 está disponível
if ! ollama list | grep -q "phi3"; then
  echo "📦 Baixando modelo Phi-3..."
  ollama pull phi3
fi

# Inicia o servidor FastAPI
echo "✅ Iniciando servidor FastAPI..."
uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8080}
