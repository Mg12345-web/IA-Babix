import re
import sqlite3
from pathlib import Path

# Caminho do banco
BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "backend" / "db" / "conhecimento.db"

# ------------------------------------------------------------
# Funções principais
# ------------------------------------------------------------

def _conn():
    """Abre conexão com o banco"""
    return sqlite3.connect(str(DB_PATH))

def carregar_texto_geral() -> str:
    """Lê o conteúdo completo do MBFT geral"""
    with _conn() as conn:
        cur = conn.cursor()
        cur.execute("SELECT conteudo FROM fichas WHERE codigo='MBFT-GERAL' ORDER BY id DESC LIMIT 1")
        row = cur.fetchone()
    return row[0] if row else ""

def limpar_fichas_antigas():
    """Remove fichas antigas (mantém apenas a geral)"""
    with _conn() as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM fichas WHERE codigo != 'MBFT-GERAL'")
        conn.commit()

def dividir_em_fichas(texto: str):
    """
    Divide o texto em fichas individuais com base no padrão de código (ex: 596-70).
    Retorna uma lista de tuplas (codigo, conteudo).
    """
    # Regex para capturar cabeçalho de ficha: ex "596-70 – Dirigir veículo ..."
    padrao = re.compile(r"(?P<codigo>\d{3}-\d{2})[\s–-]+(?P<titulo>.+?)(?=\n\d{3}-\d{2}|$)", re.S)
    fichas = padrao.findall(texto)
    return fichas

def salvar_fichas(fichas):
    """Salva as fichas individuais no banco"""
    with _conn() as conn:
        cur = conn.cursor()
        # Busca o documento MBFT
        cur.execute("SELECT id FROM documentos WHERE nome='MBFT'")
        doc_id = cur.fetchone()[0]
        count = 0
        for i, (codigo, conteudo) in enumerate(fichas):
            titulo = conteudo.strip().split("\n")[0][:200]  # Primeira linha curta
            cur.execute("""
                INSERT OR REPLACE INTO fichas (codigo, titulo, conteudo, documento_id)
                VALUES (?, ?, ?, ?)
            """, (codigo.strip(), titulo.strip(), conteudo.strip(), doc_id))
            count += 1
        conn.commit()
    print(f"📑 {count} fichas indexadas com sucesso!")

# ------------------------------------------------------------
# Execução principal
# ------------------------------------------------------------
def indexar_mbft():
    """Cria fichas reais a partir do MBFT geral"""
    texto = carregar_texto_geral()
    if not texto:
        print("⚠️ Nenhum conteúdo encontrado no MBFT-GERAL.")
        return

    print("🔍 Iniciando indexação das fichas do MBFT...")
    limpar_fichas_antigas()
    fichas = dividir_em_fichas(texto)

    if not fichas:
        print("⚠️ Nenhuma ficha foi detectada no texto. Verifique o formato.")
        return

    salvar_fichas(fichas)
    print("✅ Indexação concluída e fichas armazenadas no banco.")


if __name__ == "__main__":
    indexar_mbft()
