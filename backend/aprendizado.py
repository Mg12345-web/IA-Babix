import os
import sqlite3
from PyPDF2 import PdfReader

DB_PATH = "backend/db/conhecimento.db"
PDF_PATH = "backend/dados/MBVT20222.pdf"  # ajuste o nome se estiver diferente

def inicializar_db():
    """Cria o banco e as tabelas caso não existam."""
    os.makedirs("backend/db", exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Tabela de documentos (origem do conhecimento)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS documentos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT UNIQUE,
            tipo TEXT,
            caminho TEXT
        )
    """)

    # Tabela de fichas (infrações individuais)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS fichas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo TEXT UNIQUE,
            titulo TEXT,
            amparo TEXT,
            gravidade TEXT,
            penalidade TEXT,
            pontos TEXT,
            conteudo TEXT,
            documento_id INTEGER,
            FOREIGN KEY (documento_id) REFERENCES documentos (id)
        )
    """)

    conn.commit()
    conn.close()


def limpar_banco():
    """Remove dados antigos sem apagar estrutura."""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("DELETE FROM documentos")
    cur.execute("DELETE FROM fichas")
    conn.commit()
    conn.close()


def extrair_texto_pdf(caminho_pdf):
    """Extrai texto do PDF (modo texto)."""
    texto = ""
    reader = PdfReader(caminho_pdf)
    for page in reader.pages:
        texto += page.extract_text() or ""
    return texto

def limpar_conhecimento():
    global conhecimento_base
    conhecimento_base = []
    
def carregar_conhecimento(caminho_pdf="dados/mbft.pdf"):
    inicializar_db()
    limpar_conhecimento()
    texto = extrair_texto_pdf(caminho_pdf)
    salvar_conhecimento("MBFT", texto)
    print("📘 Conhecimento do MBFT armazenado com sucesso.")

    # Verifica se o arquivo existe
    if not os.path.exists(PDF_PATH):
        print(f"⚠️ Arquivo PDF não encontrado: {PDF_PATH}")
        return

    print("📘 Lendo MBFT...")
    texto = extrair_texto_pdf(PDF_PATH)

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Cadastra o documento principal
    cur.execute("INSERT OR IGNORE INTO documentos (nome, tipo, caminho) VALUES (?, ?, ?)",
                ("MBFT", "pdf", PDF_PATH))
    doc_id = cur.lastrowid or cur.execute("SELECT id FROM documentos WHERE nome='MBFT'").fetchone()[0]

    # Insere tudo como uma ficha geral (depois o módulo leitor dividirá)
    cur.execute("""
        INSERT OR REPLACE INTO fichas (codigo, titulo, conteudo, documento_id)
        VALUES (?, ?, ?, ?)
    """, ("MBFT-GERAL", "Manual Brasileiro de Fiscalização de Trânsito", texto, doc_id))

    conn.commit()
    conn.close()

    print("✅ MBFT carregado na memória!")


if __name__ == "__main__":
    carregar_conhecimento()
