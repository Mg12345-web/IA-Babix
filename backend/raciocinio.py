import sqlite3
import subprocess


def consultar_base(pergunta: str) -> str:
    """Busca contexto relevante no banco local"""
    try:
        conn = sqlite3.connect("backend/db/conhecimento.db")
        cur = conn.cursor()
        cur.execute(
            "SELECT conteudo FROM conhecimento WHERE conteudo LIKE ? LIMIT 5",
            (f"%{pergunta}%",),
        )
        resultados = cur.fetchall()
        conn.close()

        if not resultados:
            return "Nenhum conteúdo relevante encontrado no banco local."

        # Junta pequenos trechos em um só contexto
        return "\n\n".join([r[0][:1500] for r in resultados])

    except Exception as e:
        return f"❌ Erro ao consultar banco: {e}"


def gerar_resposta(pergunta: str) -> str:
    """
    Gera resposta com base no conhecimento local + raciocínio do modelo Ollama.
    """
    contexto = consultar_base(pergunta)

    prompt = f"""
    Você é a Babix IA, uma assistente especialista em legislação de trânsito.
    Use as informações abaixo para responder de forma clara e fundamentada.
    Se o contexto for insuficiente, diga 'Informação não encontrada na base local'.

    📚 Contexto:
    {contexto}

    ❓ Pergunta:
    {pergunta}

    🧠 Resposta:
    """

    try:
        comando = ["ollama", "run", "phi3", prompt]
        resultado = subprocess.run(comando, capture_output=True, text=True, timeout=90)
        saida = resultado.stdout.strip()
        return saida or "❌ Nenhuma resposta retornada pelo modelo."
    except subprocess.TimeoutExpired:
        return "⚠️ Tempo excedido ao processar com o modelo local (Ollama)."
    except Exception as e:
        return f"❌ Erro ao gerar resposta: {e}"
