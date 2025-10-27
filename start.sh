#!/bin/bash
set -e  # faz o script parar se algum comando der erro

echo "=============================="
echo "🚀 Iniciando Babix IA com Ollama local..."
echo "=============================="

# Inicia o Ollama em segundo plano
ollama serve &
OLLAMA_PID=$!

# Aguarda o Ollama inicializar
echo "⏳ Aguardando Ollama iniciar..."
sleep 15

# Testa o modelo Phi-3
if ! ollama list | grep -q "phi3"; then
  echo "📦 Baixando modelo Phi-3..."
  ollama pull phi3 || echo "⚠️ Falha ao baixar modelo Phi-3, continuando..."
else
  echo "✅ Modelo Phi-3 já disponível!"
fi

# Executa a inicialização do aprendizado
echo "🧠 Preparando banco e aprendizado inicial..."
python3 iniciar_babix.py || echo "⚠️ Erro ao inicializar Babix, continuando..."

# Inicia o servidor FastAPI
echo "✅ Iniciando servidor FastAPI..."
uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8080} &

# Mantém o Ollama ativo e impede que o container encerre
wait $OLLAMA_PID
