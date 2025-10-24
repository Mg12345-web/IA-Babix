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
        CREATE TABLE IF NOT EXISTS fichas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo TEXT UNIQUE,
            artigo TEXT,
            gravidade TEXT,
            valor TEXT,
            conteudo TEXT
        )
    """)
    # tabela de compatibilidade para respostas gerais (opcional)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS conhecimento (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            origem TEXT,
            conteudo TEXT
        )
    """)
    conn.commit()
    conn.close()

def limpar_conhecimento():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("DELETE FROM fichas")
    cur.execute("DELETE FROM conhecimento WHERE origem='MBFT'")
    conn.commit()
    conn.close()

def salvar_conhecimento(origem, conteudo):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("INSERT INTO conhecimento (origem, conteudo) VALUES (?,?)", (origem, conteudo))
    conn.commit()
    conn.close()

def carregar_conhecimento(caminho_pdf):
    inicializar_db()
    pdf_path = Path(caminho_pdf)
    if not pdf_path.exists():
        print(f"❌ Arquivo {caminho_pdf} não encontrado.")
        return
    print(f"📖 Lendo {pdf_path.name} com pdfplumber…")
    texto = extrair_texto(pdf_path)
    limpar_conhecimento()
    salvar_conhecimento("MBFT", texto)
    print("📘 Conhecimento do MBFT armazenado (modo texto).")
