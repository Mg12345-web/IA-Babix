import sqlite3
import re
from pathlib import Path
from difflib import SequenceMatcher
from typing import Optional, List, Tuple, Dict

# Caminho do banco
BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "backend" / "db" / "conhecimento.db"

# ============================================================
# 🧩 Utilitários
# ============================================================

def _conn():
    return sqlite3.connect(str(DB_PATH))

def _sim(a: str, b: str) -> float:
    """Calcula similaridade textual simples"""
    return SequenceMatcher(None, (a or "").lower(), (b or "").lower()).ratio()

def _resumir_texto(texto: str, max_linhas: int = 8) -> str:
    """Cria um resumo simples com base nas partes mais informativas."""
    linhas = [l.strip() for l in texto.split("\n") if len(l.strip()) > 50]
    if not linhas:
        return texto[:400]
    return "\n".join(linhas[:max_linhas])

# ============================================================
# 🔹 Parte 1 — Busca e Fichas
# ============================================================

def obter_ficha_por_codigo(codigo: str) -> Optional[dict]:
    """Busca uma ficha específica por código (ex: 596-70)."""
    with _conn() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT f.codigo, f.titulo, f.conteudo, d.nome, f.resumo
            FROM fichas f
            JOIN documentos d ON d.id = f.documento_id
            WHERE f.codigo = ?
            ORDER BY f.id DESC LIMIT 1
        """, (codigo,))
        row = cur.fetchone()
    if not row:
        return None
    return {
        "codigo": row[0],
        "titulo": row[1] or "",
        "conteudo": row[2] or "",
        "documento": row[3] or "",
        "resumo": row[4] or ""
    }

def buscar_fichas_por_texto(q: str, limit: int = 5) -> List[Tuple[float, dict]]:
    """Busca fichas similares a um texto ou pergunta."""
    with _conn() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT f.codigo, f.titulo, f.conteudo, d.nome, f.resumo
            FROM fichas f
            JOIN documentos d ON d.id = f.documento_id
        """)
        rows = cur.fetchall()

    scored = []
    for codigo, titulo, conteudo, doc, resumo in rows:
        score = max(_sim(q, titulo), _sim(q, conteudo))
        scored.append((score, {
            "codigo": codigo,
            "titulo": titulo,
            "conteudo": conteudo,
            "documento": doc,
            "resumo": resumo
        }))
    scored.sort(key=lambda x: x[0], reverse=True)
    return scored[:limit]

# ============================================================
# 🔹 Parte 2 — Interpretação e Explicação
# ============================================================

def formatar_explicacao(f: dict) -> str:
    """Formata uma ficha ou documento para exibição."""
    resumo = f.get("resumo") or _resumir_texto(f.get("conteudo", ""))
    return (
        f"🧾 **Ficha {f['codigo']} — Explicação**\n"
        f"🚗 **Descrição:** {f['titulo'] or '(sem título)'}\n"
        f"📘 **Fonte:** {f['documento']}\n"
        "\n🧠 **Resumo:**\n"
        f"{resumo}\n"
        "\n⚙️ **Interpretação automática:**\n"
        f"Aplicar conforme descrito na ficha. "
        f"Verifique exceções em 'quando não autuar', sinalização e abordagem obrigatória.\n"
    )

# ============================================================
# 🔹 Parte 3 — Campo de Observações (Análise Técnica)
# ============================================================

def analisar_observacao(texto: str) -> Dict[str, str]:
    """
    Analisa o campo de Observações de um AIT e gera parecer técnico.
    """
    if not texto or len(texto.strip()) < 10:
        return {"status": "❌ Texto muito curto.", "detalhe": "Forneça o texto completo do campo Observações."}

    candidatos = buscar_fichas_por_texto(texto, limit=3)
    if not candidatos:
        return {"status": "❌ Nenhuma ficha compatível encontrada."}

    melhor_score, melhor_ficha = candidatos[0]
    codigo = melhor_ficha["codigo"]
    titulo = melhor_ficha["titulo"]
    conteudo = melhor_ficha["conteudo"]

    texto_lower = texto.lower()
    conteudo_lower = conteudo.lower()
    match = _sim(texto_lower, conteudo_lower)

    if match > 0.7:
        parecer = "✅ Correto — descrição condiz com o enquadramento e critérios técnicos."
    elif 0.45 < match <= 0.7:
        parecer = "⚠️ Parcial — há coerência parcial entre o campo e o MBFT."
    else:
        parecer = "❌ Incorreto — descrição não se enquadra conforme o MBFT."

    return {
        "codigo": codigo,
        "titulo": titulo,
        "parecer": parecer,
        "similaridade": f"{match:.2f}"
    }

def gerar_resposta_observacao(texto: str) -> str:
    """Gera resposta formatada para o campo de observações."""
    resultado = analisar_observacao(texto)
    if "codigo" not in resultado:
        return resultado.get("status", "❌ Erro ao analisar o texto.")

    return f"""
📋 **Análise Técnica — Campo de Observações**

🧾 **Ficha sugerida:** {resultado['codigo']} — {resultado['titulo']}

💬 **Texto informado:**
{texto.strip()}

🧠 **Parecer técnico:** {resultado['parecer']}
🔢 **Similaridade:** {resultado['similaridade']}
""".strip()

# ============================================================
# 🔹 Parte 4 — Geração de resposta geral (chat)
# ============================================================

def gerar_resposta(pergunta: str) -> str:
    """Processa a pergunta e retorna a resposta apropriada."""
    if not pergunta or not pergunta.strip():
        return "Envie uma pergunta, código de ficha ou o campo de observações para análise."

    # Modo observação
    if any(p in pergunta.lower() for p in ["observação", "observacoes", "analisar", "campo do ait"]):
        texto_limpo = re.sub(r"(analisar|observaç(ões|ao)|campo do ait|verifique|verificar)", "", pergunta, flags=re.IGNORECASE)
        return gerar_resposta_observacao(texto_limpo.strip())

    # Código de ficha
    m = re.search(r"\b\d{3}-\d{2}\b", pergunta)
    if m:
        codigo = m.group(0)
        f = obter_ficha_por_codigo(codigo)
        if f:
            return formatar_explicacao(f)
        return f"Não encontrei a ficha {codigo} nas fontes carregadas."

    # Pergunta conceitual sobre MBFT
    if re.search(r"\b(o que é|o que significa|explique)\b.*\bmbft\b", pergunta, re.IGNORECASE):
        return (
            "📚 **MBFT — Manual Brasileiro de Fiscalização de Trânsito**\n"
            "Conjunto de fichas operacionais que orientam a autuação conforme o CTB. "
            "Cada ficha descreve conduta, enquadramento, exceções e procedimentos técnicos."
        )

    # Busca textual por similaridade
    candidatos = buscar_fichas_por_texto(pergunta, limit=1)
    if candidatos and candidatos[0][0] > 0.25:
        _, ficha = candidatos[0]
        return formatar_explicacao(ficha)

    # Fallback
    with _conn() as conn:
        cur = conn.cursor()
        cur.execute("SELECT conteudo FROM fichas WHERE codigo='MBFT-GERAL' ORDER BY id DESC LIMIT 1")
        row = cur.fetchone()
    texto = row[0] if row else ""
    if not texto:
        return "Base do MBFT ainda não carregada."
    partes = re.split(r'(?<=[.!?])\s+', texto)
    melhor = max(partes, key=lambda s: _sim(s, pergunta)) if partes else texto[:400]
    return f"📘 Baseando-me no MBFT: {melhor.strip()[:1200]}"
