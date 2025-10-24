import sqlite3
import os
from PyPDF2 import PdfReader

DB_PATH = "backend/db/conhecimento.db"

def inicializar_db():
    os.makedirs("backend/db", exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 🔹 Tabela principal de documentos (PDFs ou MBFT)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS documentos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT UNIQUE,
            tipo TEXT,
            origem TEXT,
            data_insercao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 🔹 Tabela de fichas (relacionada ao documento)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS fichas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            documento_id INTEGER,
            codigo TEXT,
            artigo TEXT,
            gravidade TEXT,
            valor TEXT,
            conteudo TEXT,
            FOREIGN KEY(documento_id) REFERENCES documentos(id)
        )
    """)

    conn.commit()
    conn.close()

def limpar_conhecimento(origem="MBFT"):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM documentos WHERE origem=?", (origem,))
    cursor.execute("DELETE FROM fichas")
    conn.commit()
    conn.close()

def salvar_documento(nome, tipo, origem):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO documentos (nome, tipo, origem) VALUES (?, ?, ?)",
                   (nome, tipo, origem))
    conn.commit()
    cursor.execute("SELECT id FROM documentos WHERE nome=?", (nome,))
    documento_id = cursor.fetchone()[0]
    conn.close()
    return documento_id

def salvar_ficha(documento_id, codigo, artigo, gravidade, valor, conteudo):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO fichas (documento_id, codigo, artigo, gravidade, valor, conteudo)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (documento_id, codigo, artigo, gravidade, valor, conteudo))
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
    limpar_conhecimento("MBFT")

    nome_arquivo = os.path.basename(caminho_pdf)
    documento_id = salvar_documento(nome_arquivo, "pdf", "MBFT")

    texto = extrair_texto_pdf(caminho_pdf)

    # Aqui você pode futuramente dividir por fichas (ex: "596-70")
    salvar_ficha(documento_id, "GERAL", "", "", "", texto)

    print("📘 Conhecimento do MBFT armazenado com sucesso.")
