import os
import sqlite3
import re
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional

from PyPDF2 import PdfReader

BASE_DIR = Path(__file__).resolve().parent.parent  # /app/backend/..
DB_PATH = BASE_DIR / "backend" / "db" / "conhecimento.db"
DADOS_DIR = BASE_DIR / "dados"

CODE_RE = re.compile(r"\b(\d{3}-\d{2})\b")

# -----------------------------
# DB
# -----------------------------
def init_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS documentos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT,
        caminho TEXT,
        paginas INTEGER,
        criado_em TEXT
    )""")
    cur.execute("""
    CREATE TABLE IF NOT EXISTS fichas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        documento_id INTEGER,
        codigo TEXT,
        titulo TEXT,
        amparo TEXT,
        gravidade TEXT,
        penalidade TEXT,
        pontos TEXT,
        pagina_inicio INTEGER,
        pagina_fim INTEGER,
        texto LONGTEXT,
        UNIQUE(documento_id, codigo),
        FOREIGN KEY(documento_id) REFERENCES documentos(id)
    )""")
    # Compatibilidade com versões antigas
    cur.execute("""
    CREATE TABLE IF NOT EXISTS conhecimento (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        origem TEXT,
        conteudo LONGTEXT
    )""")
    conn.commit()
    conn.close()

# -----------------------------
# PDF
# -----------------------------
def _pdf_pages_text(pdf_path: Path) -> List[str]:
    reader = PdfReader(str(pdf_path))
    pages = []
    for i, page in enumerate(reader.pages):
        try:
            t = page.extract_text() or ""
        except Exception:
            t = ""
        pages.append(t)
    return pages

def _guess(field_regex: str, text: str) -> Optional[str]:
    m = re.search(field_regex, text, re.IGNORECASE)
    return m.group(1).strip() if m else None

def _normalize_space(s: str) -> str:
    return re.sub(r"[ \t]+", " ", s).strip()

# -----------------------------
# Indexação de um PDF (MBFT ou outros)
# -----------------------------
def indexar_pdf(pdf_path: str, nome_documento: str, limpar_fichas_anteriores: bool = True) -> Dict:
    """
    Lê todas as páginas, detecta fichas (###-##), agrupa por página, extrai campos, salva no DB.
    Retorna um resumo: {'documento_id': int, 'fichas': N}
    """
    init_db()
    pdf_path = Path(pdf_path)
    if not pdf_path.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {pdf_path}")

    pages = _pdf_pages_text(pdf_path)
    total_paginas = len(pages)

    # cria/atualiza documento
    conn = sqlite3.connect(str(DB_PATH))
    cur = conn.cursor()
    cur.execute("INSERT INTO documentos (nome, caminho, paginas, criado_em) VALUES (?,?,?,?)",
                (nome_documento, str(pdf_path), total_paginas, datetime.utcnow().isoformat()))
    documento_id = cur.lastrowid

    # opcional: manter texto completo na tabela compatível "conhecimento"
    completo = "\n\n".join(pages)
    cur.execute("INSERT INTO conhecimento (origem, conteudo) VALUES (?,?)", (nome_documento, completo))

    # varredura de códigos por página
    # estratégia: sempre que um código aparecer, inicia uma nova ficha, que vai até o próximo código
    # se o mesmo código reaparecer, consideramos que a ficha começou ali (ex.: cabeçalho repetido)
    indices = []  # lista de (codigo, page_idx, pos_start_in_page_text)
    for p_idx, t in enumerate(pages):
        for m in CODE_RE.finditer(t):
            indices.append((m.group(1), p_idx, m.start()))

    # ordenar por ordem no documento
    indices.sort(key=lambda x: (x[1], x[2]))
    # acrescentar sentinela final
    indices.append(("FIM", total_paginas, 0))

    fichas_salvas = 0

    for i in range(len(indices)-1):
        codigo, p_ini, _ = indices[i]
        next_codigo, p_next, _ = indices[i+1]

        if codigo == "FIM":
            continue

        pagina_inicio = p_ini + 1  # 1-based
        pagina_fim = p_next if p_next > p_ini else p_ini + 1  # se mesmo page, assume 1 página

        # juntar texto das páginas [p_ini, p_fim-1]
        trecho_pages = pages[p_ini:p_next] if p_next > p_ini else [pages[p_ini]]
        texto_ficha = "\n".join(trecho_pages)

        # heurísticas de campos
        titulo = _guess(r"(?:Tipifica[cç][aã]o|Descri[cç][aã]o)\s*[:\-]?\s*(.+)", texto_ficha) \
                 or _guess(r"(?:Resumo|Enquadramento)\s*[:\-]?\s*(.+)", texto_ficha)
        amparo = _guess(r"(Art\.\s*\d+[^\n]*)", texto_ficha)
        gravidade = _guess(r"Gravidade\s*[:\-]?\s*([^\n]+)", texto_ficha)
        penalidade = _guess(r"Penalidade\s*[:\-]?\s*([^\n]+)", texto_ficha)
        pontos = _guess(r"Pontua[cç][aã]o\s*[:\-]?\s*([^\n]+)", texto_ficha)

        try:
            cur.execute("""
                INSERT OR REPLACE INTO fichas
                (documento_id, codigo, titulo, amparo, gravidade, penalidade, pontos, pagina_inicio, pagina_fim, texto)
                VALUES (?,?,?,?,?,?,?,?,?,?)
            """, (documento_id, codigo, 
                  _normalize_space(titulo or ""), 
                  _normalize_space(amparo or ""), 
                  _normalize_space(gravidade or ""), 
                  _normalize_space(penalidade or ""), 
                  _normalize_space(pontos or ""), 
                  pagina_inicio, pagina_fim, texto_ficha))
            fichas_salvas += 1
        except Exception as e:
            # segue sem travar caso uma ficha dê erro
            print(f"⚠️ Erro ao salvar ficha {codigo}: {e}")

    conn.commit()
    conn.close()
    return {"documento_id": documento_id, "fichas": fichas_salvas}

# Conveniências específicas
def indexar_mbft_padrao():
    """Carrega /dados/mbft.pdf se existir, como 'MBFT'."""
    mbft_path = DADOS_DIR / "mbft.pdf"
    if mbft_path.exists():
        print("🔄 Indexando MBFT…")
        resumo = indexar_pdf(str(mbft_path), "MBFT", limpar_fichas_anteriores=True)
        print(f"✅ MBFT indexado: {resumo['fichas']} fichas.")
    else:
        print("⚠️ /dados/mbft.pdf não encontrado. Iniciando sem MBFT.")
