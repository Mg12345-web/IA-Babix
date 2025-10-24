import sqlite3
import re
from pathlib import Path
from difflib import SequenceMatcher
from typing import Optional, List, Tuple, Dict

# Caminho do banco
BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "backend" / "db" / "conhecimento.db"

# =============================
# Funções utilitárias
# =============================

def _conn():
    return sqlite3.connect(str(DB_PATH))

def _sim(a: str, b: str) -> float:
    """Calcula similaridade textual simples"""
    return SequenceMatcher(None, (a or "").lower(), (b or "").lower()).ratio()

# ============================================================
# 🔹 Parte 1 — Funções antigas (mantidas)
# ============================================================

def obter_ficha_por_codigo(codigo: str) -> Optional[dict]:
    with _conn() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT f.codigo, f.titulo, f.conteudo, d.nome
            FROM fichas f
            JOIN documentos d ON d.id = f.documento_id
            WHERE f.codigo = ?
            ORDER BY f.id DESC
            LIMIT 1
        """, (codigo,))
        row = cur.fetchone()
    if not row:
        return None
    return {
        "codigo": row[0],
        "titulo": row[1] or "",
        "conteudo": row[2] or "",
        "documento": row[3] or "",
    }

def buscar_fichas_por_texto(q: str, limit: int = 5) -> List[Tuple[float, dict]]:
    with _conn() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT f.codigo, f.titulo, f.conteudo, d.nome
            FROM fichas f
            JOIN documentos d ON d.id = f.documento_id
        """)
        rows = cur.fetchall()

    scored = []
    for codigo, titulo, conteudo, doc in rows:
        score = max(_sim(q, titulo), _sim(q, conteudo))
        scored.append((score, {
            "codigo": codigo,
            "titulo": titulo,
            "conteudo": conteudo,
            "documento": doc
        }))
    scored.sort(key=lambda x: x[0], reverse=True)
    return scored[:limit]

def formatar_explicacao(f: dict) -> str:
    linhas = [
        f"🧾 **Ficha {f['codigo']} — Explicação**",
        f"🚗 **Descrição:** {f['titulo'] or '(sem título)'}",
        f"📘 **Fonte:** {f['documento']}",
        "\n🧠 **Resumo:**",
        f"{(f['conteudo'][:1200] + '...') if len(f['conteudo']) > 1200 else f['conteudo']}",
        "\n⚙️ **Interpretação automática:** Aplicar conforme descrito. Verifique exceções e observações de 'quando não autuar'."
    ]
    return "\n".join(linhas)

def _texto_completo() -> str:
    with _conn() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT conteudo FROM fichas 
            WHERE codigo = 'MBFT-GERAL' 
            ORDER BY id DESC LIMIT 1
        """)
        row = cur.fetchone()
    return row[0] if row else ""

def contar_fichas() -> int:
    with _conn() as conn:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM fichas WHERE codigo != 'MBFT-GERAL'")
        return cur.fetchone()[0]

def resposta_conceito_mbft() -> str:
    texto = _texto_completo()
    total = len(texto.split()) if texto else 0
    return (
        "📚 **MBFT — Manual Brasileiro de Fiscalização de Trânsito**\n"
        "Conjunto de fichas e orientações operacionais para autuação, com amparo no CTB. "
        f"Base atual carregada com ~{total} palavras e {contar_fichas()} fichas indexadas."
    )

# ============================================================
# 🔹 Parte 2 — NOVO RACIOCÍNIO (Campo de Observações)
# ============================================================

def analisar_observacao(texto: str) -> Dict[str, str]:
    """
    Analisa o texto do campo Observações e indica se está correto ou incorreto
    conforme as fichas do MBFT.
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

    # Heurística de coerência
    texto_lower = texto.lower()
    conteudo_lower = conteudo.lower()
    match = _sim(texto_lower, conteudo_lower)

    if match > 0.65:
        parecer = "✅ Correto — descrição condiz com o enquadramento."
    elif 0.4 < match <= 0.65:
        parecer = "⚠️ Parcial — texto parcialmente coerente com a ficha."
    else:
        parecer = "❌ Incorreto — texto não condiz com a infração descrita."

    return {
        "codigo": codigo,
        "titulo": titulo,
        "parecer": parecer,
        "similaridade": f"{match:.2f}"
    }

def gerar_resposta_observacao(texto: str) -> str:
    """Gera a resposta formatada do campo de observação."""
    resultado = analisar_observacao(texto)
    if "codigo" not in resultado:
        return resultado["status"]

    return f"""
📋 **Análise de Observação**

**Texto informado:**
{texto.strip()}

**Ficha sugerida:** {resultado['codigo']} — {resultado['titulo']}

**🧠 Interpretação automática:**
{resultado['parecer']} (similaridade {resultado['similaridade']})
""".strip()

# ============================================================
# 🔹 Parte 3 — Roteador principal (mantido e ampliado)
# ============================================================

def gerar_resposta(pergunta: str) -> str:
    """
    Mantém compatibilidade com o modo de chat anterior.
    Agora identifica automaticamente se é uma 'observação' ou pergunta geral.
    """
    if not pergunta or not pergunta.strip():
        return "Faça sua pergunta sobre o MBFT ou envie o campo de observações para análise."

    # 🔍 Novo modo: análise de observações
    if any(p in pergunta.lower() for p in ["observação", "observacoes", "analisar", "campo do ait"]):
        # Remove palavras de comando e analisa o conteúdo
        texto_limpo = re.sub(r"(analisar|observaç(ões|ao)|campo do ait|verifique|verificar)", "", pergunta, flags=re.IGNORECASE)
        return gerar_resposta_observacao(texto_limpo.strip())

    # Modo antigo: perguntas normais
    m = re.search(r"\\b\\d{3}-\\d{2}\\b", pergunta)
    if m:
        codigo = m.group(0)
        f = obter_ficha_por_codigo(codigo)
        if f:
            return formatar_explicacao(f)
        return f"Não encontrei a ficha {codigo} nas fontes carregadas."

    if re.search(r"\\b(o que é|o que significa|explique)\\b.*\\bmbft\\b", pergunta, re.IGNORECASE):
        return resposta_conceito_mbft()

    candidatos = buscar_fichas_por_texto(pergunta, limit=1)
    if candidatos and candidatos[0][0] > 0.25:
        _, ficha = candidatos[0]
        return formatar_explicacao(ficha)

    texto = _texto_completo()
    if not texto:
        return "Base do MBFT ainda não carregada."
    partes = re.split(r'(?<=[\\.!?])\\s+', texto)
    melhor = max(partes, key=lambda s: _sim(s, pergunta)) if partes else texto[:400]
    return f"📘 Baseando-me no MBFT: {melhor.strip()[:1200]}"
