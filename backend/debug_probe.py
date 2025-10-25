from __future__ import annotations
import os, re, glob, html
from typing import List, Dict, Any
from dataclasses import dataclass
from fastapi import APIRouter, HTTPException, Query
from bs4 import BeautifulSoup

# Tente importar pypdf (leve, sem dependências do SO)
try:
    from pypdf import PdfReader
except Exception:
    PdfReader = None

router = APIRouter()

# =======================
# Config
# =======================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_DOCS_DIR = os.path.join(BASE_DIR, "dados")
DOCS_DIR = os.environ.get("BABX_DOCS_DIR", DEFAULT_DOCS_DIR)

CHUNK_CHARS = 1200
CHUNK_OVERLAP = 200
MAX_SNIPPETS_PER_FILE = 3

# =======================
# Estruturas em memória
# =======================
@dataclass
class Chunk:
    source_id: str
    idx: int
    text: str

_LOADED = False
_FILES: List[str] = []
_CHUNKS: List[Chunk] = []
_ERRORS: Dict[str, str] = {}

# =======================
# Utilitários de parsing
# =======================
def _read_txt(path: str) -> str:
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    except Exception as e:
        return f"[ERRO lendo TXT: {e}]"

def _read_html(path: str) -> str:
    try:
        raw = _read_txt(path)
        soup = BeautifulSoup(raw, "html.parser")
        # remove scripts/styles
        for tag in soup(["script", "style", "noscript"]):
            tag.decompose()
        text = soup.get_text(separator="\n")
        return re.sub(r"\n{3,}", "\n\n", text).strip()
    except Exception as e:
        return f"[ERRO lendo HTML: {e}]"

def _read_pdf(path: str) -> str:
    if PdfReader is None:
        return "[ERRO] pypdf não disponível. Adicione 'pypdf' no requirements.txt"
    try:
        reader = PdfReader(path)
        parts = []
        for page in reader.pages:
            txt = page.extract_text() or ""
            parts.append(txt)
        return "\n".join(parts)
    except Exception as e:
        return f"[ERRO lendo PDF: {e}]"

def _ext_to_text(path: str) -> str:
    ext = os.path.splitext(path.lower())[1]
    if ext in [".txt", ".md", ".rst"]:
        return _read_txt(path)
    if ext in [".html", ".htm"]:
        return _read_html(path)
    if ext in [".pdf"]:
        return _read_pdf(path)
    # fallback: tenta abrir como texto
    return _read_txt(path)

def _chunk_text(text: str, size: int = CHUNK_CHARS, overlap: int = CHUNK_OVERLAP) -> List[str]:
    text = re.sub(r"\r\n?", "\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    blocks: List[str] = []
    i = 0
    n = len(text)
    if n == 0:
        return blocks
    while i < n:
        end = min(i + size, n)
        blocks.append(text[i:end].strip())
        if end >= n:
            break
        i = end - overlap if end - overlap > i else end
    return [b for b in blocks if b]

def _collect_files() -> List[str]:
    patterns = ["**/*.pdf", "**/*.txt", "**/*.md", "**/*.html", "**/*.htm"]
    files = []
    for p in patterns:
        files.extend(glob.glob(os.path.join(DOCS_DIR, p), recursive=True))
    return sorted(list(dict.fromkeys(files)))  # unique, stable order

# =======================
# Carregamento Lazy
# =======================
def _ensure_loaded():
    global _LOADED, _FILES, _CHUNKS, _ERRORS
    if _LOADED:
        return
    _FILES = _collect_files()
    _CHUNKS = []
    _ERRORS = {}
    for path in _FILES:
        src_id = os.path.relpath(path, DOCS_DIR).replace("\\", "/")
        text = _ext_to_text(path)
        if text.startswith("[ERRO"):
            _ERRORS[src_id] = text
            continue
        chunks = _chunk_text(text)
        for i, ch in enumerate(chunks):
            _CHUNKS.append(Chunk(source_id=src_id, idx=i, text=ch))
    _LOADED = True

# =======================
# Buscas simples (lexical)
# =======================
def _score_chunk_query(ch: Chunk, q_terms: List[str]) -> int:
    # pontua pela contagem de termos (case-insensitive)
    text = ch.text.lower()
    score = 0
    for t in q_terms:
        if not t: 
            continue
        score += text.count(t)
    return score

def _make_snippet(text: str, term: str, radius: int = 160) -> str:
    t = text
    tl = t.lower()
    terml = term.lower()
    pos = tl.find(terml)
    if pos == -1:
        # sem posição: retorna começo
        return (t[:radius*2] + "…") if len(t) > radius*2 else t
    start = max(0, pos - radius)
    end = min(len(t), pos + len(terml) + radius)
    snippet = t[start:end].strip()
    if start > 0: snippet = "… " + snippet
    if end < len(t): snippet = snippet + " …"
    return snippet

# =======================
# Rotas
# =======================
@router.get("/ingest-status")
def ingest_status() -> Dict[str, Any]:
    _ensure_loaded()
    by_file: Dict[str, int] = {}
    for ch in _CHUNKS:
        by_file[ch.source_id] = by_file.get(ch.source_id, 0) + 1
    return {
        "docs_dir": DOCS_DIR,
        "total_files_found": len(_FILES),
        "total_chunks": len(_CHUNKS),
        "per_file": [{"source_id": f, "chunks": by_file.get(f, 0), "error": _ERRORS.get(f)} for f in sorted(set([c.source_id for c in _CHUNKS] + list(_ERRORS.keys())))],
        "errors": _ERRORS,
        "note": "Se um arquivo aparecer em 'errors', o parser falhou (ex.: PDF imagem sem OCR)."
    }

@router.get("/probe")
def probe(term: str = Query(..., min_length=1, description="Termo exato para localizar (ex.: 518-51, Art. 280)"),
          per_file: int = Query(3, ge=1, le=10)) -> Dict[str, Any]:
    _ensure_loaded()
    term_l = term.lower()
    hits: Dict[str, List[Dict[str, Any]]] = {}
    for ch in _CHUNKS:
        if term_l in ch.text.lower():
            hits.setdefault(ch.source_id, [])
            if len(hits[ch.source_id]) < per_file:
                hits[ch.source_id].append({
                    "chunk_idx": ch.idx,
                    "snippet": _make_snippet(ch.text, term)
                })
    return {
        "term": term,
        "per_file_limit": per_file,
        "matches": hits,
        "note": "Isto prova ONDE o termo aparece, por arquivo e chunk."
    }

@router.get("/search")
def search(q: str = Query(..., min_length=1, description="Pergunta/consulta"),
           k: int = Query(5, ge=1, le=50)) -> Dict[str, Any]:
    _ensure_loaded()
    # Busca lexical simples: divide q em termos; pontua por contagem
    # Ex.: q='art. 280 CTB' -> termos ['art.', '280', 'ctb']
    terms = [t.strip().lower() for t in re.split(r"[\\W_]+", q) if t.strip()]
    scored: List[Dict[str, Any]] = []
    for ch in _CHUNKS:
        s = _score_chunk_query(ch, terms)
        if s > 0:
            scored.append({
                "source_id": ch.source_id,
                "chunk_idx": ch.idx,
                "score": s,
                "snippet": _make_snippet(ch.text, terms[0] if terms else "")
            })
    scored.sort(key=lambda x: x["score"], reverse=True)
    return {
        "query": q,
        "terms": terms,
        "k": k,
        "results": scored[:k],
        "note": "Rankeamento lexical simples (diagnóstico). Próximo passo é híbrido com BM25/vetorial."
    }
