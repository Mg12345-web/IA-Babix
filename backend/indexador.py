import re
import sqlite3
import hashlib
from pathlib import Path
from difflib import SequenceMatcher

# ============================================================
# 🔹 Caminhos e configuração
# ============================================================
BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "backend" / "db" / "conhecimento.db"

# ============================================================
# 🔹 Utilitários
# ============================================================

def _conn():
    """Abre conexão com o banco"""
    return sqlite3.connect(str(DB_PATH))

def _sim(a: str, b: str) -> float:
    """Calcula similaridade textual simples"""
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()

def _hash_texto(texto: str) -> str:
    """Gera hash único para cada ficha e evita duplicação."""
    return hashlib.sha256(texto.strip().encode("utf-8")).hexdigest()

def _resumir(texto: str, max_linhas: int = 8) -> str:
    """Cria um resumo simples para armazenar junto da ficha."""
    linhas = [l.strip() for l in texto.split("\n") if len(l.strip()) > 50]
    return "\n".join(linhas[:max_linhas]) if linhas else texto[:500]

# ============================================================
# 🔹 Funções principais de banco e fichas
# ============================================================

def carregar_documentos() -> list:
    """Retorna todos os documentos cadastrados para indexação."""
    with _conn() as conn:
        cur = conn.cursor()
        cur.execute("SELECT id, titulo, conteudo FROM fichas WHERE codigo LIKE '%GERAL%'")
        return cur.fetchall()

def limpar_fichas_antigas():
    """Remove fichas antigas mantendo apenas as gerais."""
    with _conn() as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM fichas WHERE codigo NOT LIKE '%GERAL%'")
        conn.commit()

# ============================================================
# 🔹 Divisão e indexação de textos
# ============================================================

def dividir_em_blocos(texto: str, nome_doc: str) -> list:
    """
    Divide o texto em blocos de sentido (artigos, seções ou fichas MBFT).
    Retorna lista de tuplas (codigo, conteudo).
    """
    texto = texto.replace("\r", "")
    texto = re.sub(r"\n{2,}", "\n", texto)

    # Detecta se é MBFT (códigos 123-45)
    if "MBFT" in nome_doc.upper() or re.search(r"\d{3}-\d{2}", texto):
        padrao = re.compile(
            r"(?P<codigo>\d{3}-\d{2})[\s–-]+(?P<conteudo>.*?)(?=\n\d{3}-\d{2}[\s–-]|$)",
            re.S
        )
        fichas = padrao.findall(texto)
        blocos = [(codigo.strip(), conteudo.strip()) for codigo, conteudo in fichas]
    else:
        # Divide por artigos, seções, títulos ou blocos longos
        padrao = re.compile(
            r"(?P<titulo>(Art\. ?\d+|SEÇÃO|TÍTULO|CAPÍTULO).+?)(?=(?:Art\. ?\d+|SEÇÃO|TÍTULO|CAPÍTULO|$))",
            re.S | re.I
        )
        blocos = []
        for match in padrao.finditer(texto):
            titulo = match.group("titulo").strip()
            codigo = re.sub(r"[^0-9A-Za-z]+", "_", titulo[:15])
            blocos.append((codigo, titulo))

    print(f"📚 Documento '{nome_doc}' dividido em {len(blocos)} blocos.")
    return blocos

# ============================================================
# 🔹 Salvamento das fichas processadas
# ============================================================

def salvar_blocos(doc_id: int, nome_doc: str, blocos: list):
    """Salva cada bloco como ficha individual no banco."""
    if not blocos:
        print(f"⚠️ Nenhum bloco detectado em {nome_doc}.")
        return

    with _conn() as conn:
        cur = conn.cursor()
        count = 0

        for codigo, conteudo in blocos:
            resumo = _resumir(conteudo)
            cur.execute("""
                INSERT OR REPLACE INTO fichas (codigo, titulo, resumo, conteudo, documento_id)
                VALUES (?, ?, ?, ?, ?)
            """, (codigo, nome_doc, resumo, conteudo, doc_id))
            count += 1

            if count % 50 == 0:
                print(f"📄 {count} blocos processados de {nome_doc}...")

        conn.commit()

    print(f"✅ {count} blocos de '{nome_doc}' salvos com sucesso.")

# ============================================================
# 🔹 Função principal de indexação
# ============================================================

def indexar_mbft():
    """
    Indexa todos os documentos no banco (não apenas o MBFT),
    criando fichas por blocos temáticos.
    """
    limpar_fichas_antigas()
    documentos = carregar_documentos()

    if not documentos:
        print("⚠️ Nenhum documento base encontrado (fichas -GERAL).")
        return

    print(f"🔍 Iniciando indexação automática de {len(documentos)} documentos...")
    for doc_id, nome, texto in documentos:
        blocos = dividir_em_blocos(texto, nome)
        salvar_blocos(doc_id, nome, blocos)

    print("🏁 Indexação completa de todos os documentos!")
