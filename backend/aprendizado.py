import sqlite3
import os
from pathlib import Path
from backend.leitor import extrair_texto

DB_PATH = "backend/db/conhecimento.db"

def inicializar_db():
    os.makedirs("backend/db", exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS conhecimento (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            origem TEXT,
            conteudo TEXT
        )
    """)
    conn.commit()
    conn.close()

def limpar_conhecimento(origem="MBFT"):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM conhecimento WHERE origem=?", (origem,))
    conn.commit()
    conn.close()

def salvar_conhecimento(origem, conteudo):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO conhecimento (origem, conteudo) VALUES (?, ?)", (origem, conteudo))
    conn.commit()
    conn.close()

def carregar_conhecimento(caminho_pdf):
    inicializar_db()
    limpar_conhecimento()

    pdf_path = Path(caminho_pdf)
    if not pdf_path.exists():
        print(f"❌ Arquivo {caminho_pdf} não encontrado.")
        return

    print(f"📖 Lendo conteúdo do {pdf_path.name}...")
    texto = extrair_texto(pdf_path)
    salvar_conhecimento("MBFT", texto)
    print("📘 Conhecimento do MBFT armazenado com sucesso.")
