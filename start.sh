#!/bin/bash
echo "=============================="
echo "🚀 Iniciando Babix IA com Ollama local..."
echo "=============================="

# Inicia o Ollama em segundo plano
ollama serve &
OLLAMA_PID=$!

# Aguarda o Ollama inicializar
echo "⏳ Aguardando Ollama iniciar..."
sleep 15

# Testa o modelo
if ! ollama list | grep -q "phi3"; then
  echo "📦 Baixando modelo Phi-3..."
  ollama pull phi3
fi

# Executa inicialização do aprendizado
echo "🧠 Preparando banco e aprendizado inicial..."
python3 iniciar_babix.py || echo "⚠️ Erro ao inicializar Babix, continuando..."

# Inicia o servidor FastAPI
echo "✅ Iniciando servidor FastAPI..."
uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8080}

# Mantém o container ativo
wait $OLLAMA_PID
