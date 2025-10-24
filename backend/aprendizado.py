import os
import sqlite3
from PyPDF2 import PdfReader

DB_PATH = "backend/db/conhecimento.db"
PDF_PATH = "backend/dados/mbft.pdf"  

# Variável global para conhecimento em memória
conhecimento_base = []

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


def limpar_conhecimento():
    """Limpa o conhecimento em memória."""
    global conhecimento_base
    conhecimento_base = []
    print("✓ Conhecimento em memória limpo")


def extrair_texto_pdf(caminho_pdf):
    """Extrai texto do PDF (modo texto)."""
    texto = ""
    reader = PdfReader(caminho_pdf)
    for page in reader.pages:
        texto += page.extract_text() or ""
    return texto


def salvar_conhecimento(fonte, texto):
    """Salva conhecimento no banco de dados."""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Cadastra o documento principal
    cur.execute("INSERT OR IGNORE INTO documentos (nome, tipo, caminho) VALUES (?, ?, ?)",
                (fonte, "pdf", PDF_PATH))
    doc_id = cur.lastrowid or cur.execute(f"SELECT id FROM documentos WHERE nome='{fonte}'").fetchone()[0]

    # Insere tudo como uma ficha geral
    cur.execute("""
        INSERT OR REPLACE INTO fichas (codigo, titulo, conteudo, documento_id)
        VALUES (?, ?, ?, ?)
    """, (f"{fonte}-GERAL", f"Manual Brasileiro de Fiscalização de Trânsito", texto, doc_id))

    conn.commit()
    conn.close()
    print(f"✓ Conhecimento de {fonte} salvo no banco")


def carregar_conhecimento(caminho_pdf=None):
    """Carrega conhecimento do PDF para o banco de dados."""
    # Usa PDF_PATH se nenhum caminho for fornecido
    pdf_final = caminho_pdf if caminho_pdf else PDF_PATH
    
    # Verifica se o arquivo existe
    if not os.path.exists(pdf_final):
        print(f"⚠️ Arquivo PDF não encontrado: {pdf_final}")
        return

    # Inicializa banco e limpa conhecimento anterior
    inicializar_db()
    limpar_conhecimento()
    
    print("📘 Lendo MBFT...")
    texto = extrair_texto_pdf(pdf_final)
    
    # Salva no banco
    salvar_conhecimento("MBFT", texto)
    
    print("✅ MBFT carregado na memória!")


if __name__ == "__main__":
    carregar_conhecimento()
