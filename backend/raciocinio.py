import sqlite3
import re
from pathlib import Path
from difflib import SequenceMatcher
from typing import Optional, List, Tuple

# Caminho do banco
BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "backend" / "db" / "conhecimento.db"


def _conn():
    return sqlite3.connect(str(DB_PATH))


def _sim(a: str, b: str) -> float:
    """Calcula similaridade textual simples"""
    return SequenceMatcher(None, (a or "").lower(), (b or "").lower()).ratio()


# -----------------------------
# Busca e formatação de fichas
# -----------------------------
def obter_ficha_por_codigo(codigo: str) -> Optional[dict]:
    """Busca ficha específica por código (ex.: 596-70)"""
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
    """Retorna fichas ordenadas por similaridade (título + conteúdo)."""
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
    """Formata uma ficha para resposta textual"""
    linhas = [
        f"🧾 **Ficha {f['codigo']} — Explicação**",
        f"🚗 **Descrição:** {f['titulo'] or '(sem título)'}",
        f"📘 **Fonte:** {f['documento']}",
        "\n🧠 **Resumo:**",
        f"{(f['conteudo'][:1200] + '...') if len(f['conteudo']) > 1200 else f['conteudo']}",
        "\n⚙️ **Interpretação automática:** Aplicar conforme descrito. Verifique exceções e observações de 'quando não autuar'."
    ]
    return "\n".join(linhas)


# -----------------------------
# Perguntas gerais
# -----------------------------
def _texto_completo(origem="MBFT") -> str:
    """Retorna o conteúdo completo do MBFT"""
    with _conn() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT conteudo FROM fichas 
            WHERE codigo = 'MBFT-GERAL' 
            ORDER BY id DESC LIMIT 1
        """)
        row = cur.fetchone()
    return row[0] if row else ""


def resposta_conceito_mbft() -> str:
    texto = _texto_completo("MBFT")
    total = len(texto.split()) if texto else 0
    return (
        "📚 **MBFT — Manual Brasileiro de Fiscalização de Trânsito**\n"
        "Conjunto de fichas e orientações operacionais para autuação, com amparo no CTB. "
        "Cada ficha traz tipificação, descrição, observações e critérios de autuação. "
        f"Base atual carregada com ~{total} palavras e {contar_fichas()} fichas indexadas."
    )


def contar_fichas() -> int:
    with _conn() as conn:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM fichas WHERE codigo != 'MBFT-GERAL'")
        return cur.fetchone()[0]


# -----------------------------
# Roteador principal
# -----------------------------
def gerar_resposta(pergunta: str) -> str:
    """Processa a pergunta e retorna a resposta adequada"""
    if not pergunta or not pergunta.strip():
        return "Faça sua pergunta sobre o MBFT ou informe um código de ficha (ex.: 596-70)."

    # 1️⃣ Código de ficha
    m = re.search(r"\b\d{3}-\d{2}\b", pergunta)
    if m:
        codigo = m.group(0)
        f = obter_ficha_por_codigo(codigo)
        if f:
            return formatar_explicacao(f)
        return f"Não encontrei a ficha {codigo} nas fontes carregadas."

    # 2️⃣ Pergunta conceitual
    if re.search(r"\b(o que é|o que significa|explique)\b.*\bmbft\b", pergunta, re.IGNORECASE):
        return resposta_conceito_mbft()

    # 3️⃣ Busca textual
    candidatos = buscar_fichas_por_texto(pergunta, limit=1)
    if candidatos and candidatos[0][0] > 0.25:
        _, ficha = candidatos[0]
        return formatar_explicacao(ficha)

    # 4️⃣ Fallback
    texto = _texto_completo()
    if not texto:
        return "Base do MBFT ainda não carregada."
    partes = re.split(r'(?<=[\.\!\?])\s+', texto)
    melhor = max(partes, key=lambda s: _sim(s, pergunta)) if partes else texto[:400]
    return f"📘 Baseando-me no MBFT: {melhor.strip()[:1200]}"
