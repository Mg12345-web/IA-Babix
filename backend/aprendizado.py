import sqlite3
import os
from PyPDF2 import PdfReader

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

def extrair_texto_pdf(caminho_pdf):
    reader = PdfReader(caminho_pdf)
    texto = ""
    for page in reader.pages:
        texto += page.extract_text() or ""
    return texto

def carregar_conhecimento(caminho_pdf):
    inicializar_db()
    limpar_conhecimento()
    texto = extrair_texto_pdf(caminho_pdf)
    salvar_conhecimento("MBFT", texto)
    print("📘 Conhecimento do MBFT armazenado com sucesso.")
