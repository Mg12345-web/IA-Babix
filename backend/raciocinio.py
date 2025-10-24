import sqlite3
import re
from pathlib import Path
from difflib import SequenceMatcher
from typing import Optional, List, Tuple

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "backend" / "db" / "conhecimento.db"

def _conn():
    return sqlite3.connect(str(DB_PATH))

def _sim(a: str, b: str) -> float:
    return SequenceMatcher(None, (a or "").lower(), (b or "").lower()).ratio()

# -----------------------------
# Busca e formatação de fichas
# -----------------------------
def obter_ficha_por_codigo(codigo: str) -> Optional[dict]:
    with _conn() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT f.codigo, f.titulo, f.amparo, f.gravidade, f.penalidade, f.pontos, 
                   f.pagina_inicio, f.pagina_fim, d.nome, f.texto
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
        "amparo": row[2] or "",
        "gravidade": row[3] or "",
        "penalidade": row[4] or "",
        "pontos": row[5] or "",
        "pagina_inicio": row[6],
        "pagina_fim": row[7],
        "documento": row[8],
        "texto": row[9] or ""
    }

def buscar_fichas_por_texto(q: str, limit: int = 5) -> List[Tuple[float, dict]]:
    """Retorna fichas ordenadas por similaridade (título + texto)."""
    with _conn() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT f.codigo, f.titulo, f.texto, f.amparo, f.gravidade, f.penalidade, f.pontos,
                   f.pagina_inicio, f.pagina_fim, d.nome
            FROM fichas f
            JOIN documentos d ON d.id = f.documento_id
        """)
        rows = cur.fetchall()

    scored = []
    for r in rows:
        codigo, titulo, texto, amparo, gravidade, penalidade, pontos, p1, p2, doc = r
        score = max(_sim(q, titulo or ""), _sim(q, texto or ""), _sim(q, amparo or ""))
        scored.append((score, {
            "codigo": codigo, "titulo": titulo or "", "texto": texto or "",
            "amparo": amparo or "", "gravidade": gravidade or "", "penalidade": penalidade or "", "pontos": pontos or "",
            "pagina_inicio": p1, "pagina_fim": p2, "documento": doc
        }))
    scored.sort(key=lambda x: x[0], reverse=True)
    return scored[:limit]

def formatar_explicacao(f: dict) -> str:
    linhas = [f"🧾 **Ficha {f['codigo']} — Explicação**"]
    if f["titulo"]:
        linhas.append(f"🚗 **Tipificação/Descrição:** {f['titulo']}")
    if f["amparo"]:
        linhas.append(f"⚖️ **Amparo Legal:** {f['amparo']}")
    if f["gravidade"]:
        linhas.append(f"💣 **Gravidade:** {f['gravidade']}")
    if f["penalidade"]:
        linhas.append(f"💰 **Penalidade:** {f['penalidade']}")
    if f["pontos"]:
        linhas.append(f"🏁 **Pontuação:** {f['pontos']}")
    linhas.append(f"📄 **Fonte:** {f['documento']} — páginas {f['pagina_inicio']}–{f['pagina_fim']}.")
    linhas.append("\n🧠 **Resumo interpretativo:**")
    linhas.append("Aplicação conforme condições descritas na ficha. Observe sinalização, contexto e exceções (\"quando não autuar\").")
    return "\n".join(linhas)

# -----------------------------
# Perguntas gerais
# -----------------------------
def _texto_completo(origem="MBFT") -> str:
    with _conn() as conn:
        cur = conn.cursor()
        cur.execute("SELECT conteudo FROM conhecimento WHERE origem=? ORDER BY id DESC LIMIT 1", (origem,))
        row = cur.fetchone()
    return row[0] if row else ""

def resposta_conceito_mbft() -> str:
    texto = _texto_completo("MBFT")
    total = len(texto.split()) if texto else 0
    return (
        "📚 **MBFT — Manual Brasileiro de Fiscalização de Trânsito**\n"
        "Conjunto de fichas e orientações operacionais para autuação, com amparo no CTB. "
        "Cada ficha traz tipificação, amparo legal, gravidade, penalidade, pontos e notas de quando (não) autuar. "
        f"Base atual carregada com ~{total} palavras e fichas indexadas para busca rápida."
    )

# -----------------------------
# Roteador principal
# -----------------------------
def gerar_resposta(pergunta: str) -> str:
    if not pergunta or not pergunta.strip():
        return "Faça sua pergunta sobre o MBFT ou informe um código de ficha (ex.: 596-70)."

    # 1) Se a pergunta contém código de ficha -> explicar
    m = re.search(r"\b\d{3}-\d{2}\b", pergunta)
    if m:
        codigo = m.group(0)
        f = obter_ficha_por_codigo(codigo)
        if f:
            return formatar_explicacao(f)
        # fallback
        return f"Não encontrei a ficha {codigo} nas fontes carregadas."

    # 2) Perguntas conceituais sobre o MBFT
    if re.search(r"\b(o que é|o que significa|explique)\b.*\bmbft\b", pergunta, re.IGNORECASE):
        return resposta_conceito_mbft()

    # 3) Busca semântica simples entre fichas
    candidatos = buscar_fichas_por_texto(pergunta, limit=1)
    if candidatos and candidatos[0][0] > 0.25:
        _, ficha = candidatos[0]
        return formatar_explicacao(ficha)

    # 4) Fallback no texto bruto (compatibilidade)
    texto = _texto_completo("MBFT")
    if not texto:
        return "Base do MBFT ainda não carregada."
    # best sentence
    partes = re.split(r'(?<=[\.\!\?])\s+', texto)
    melhor = max(partes, key=lambda s: _sim(s, pergunta)) if partes else texto[:400]
    return f"📘 Baseando-me no MBFT: {melhor.strip()[:1200]}"
