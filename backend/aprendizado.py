import os
import sqlite3
import time
from PyPDF2 import PdfReader

DB_PATH = "backend/db/conhecimento.db"

# Variável global para progresso
progresso_global = {"status": "aguardando", "atual": 0, "total": 0, "arquivo": ""}

# ======================================================
# BANCO DE DADOS
# ======================================================

def inicializar_db():
    """Cria o banco e as tabelas caso não existam."""
    os.makedirs("backend/db", exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS documentos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT UNIQUE,
            tipo TEXT,
            caminho TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS fichas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo TEXT UNIQUE,
            titulo TEXT,
            resumo TEXT,
            conteudo TEXT,
            documento_id INTEGER,
            FOREIGN KEY (documento_id) REFERENCES documentos (id)
        )
    """)

    conn.commit()
    conn.close()


def salvar_conhecimento(fonte, texto, resumo=""):
    """Salva conteúdo e resumo no banco."""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
        INSERT OR IGNORE INTO documentos (nome, tipo, caminho)
        VALUES (?, ?, ?)
    """, (fonte, "pdf", fonte))
    conn.commit()

    cur.execute("SELECT id FROM documentos WHERE nome=?", (fonte,))
    doc_id = cur.fetchone()[0]

    cur.execute("""
        INSERT OR REPLACE INTO fichas (codigo, titulo, resumo, conteudo, documento_id)
        VALUES (?, ?, ?, ?, ?)
    """, (f"{fonte}-GERAL", f"Documento {fonte}", resumo, texto, doc_id))

    conn.commit()
    conn.close()
    print(f"✅ {fonte} indexado com sucesso")


# ======================================================
# LEITURA DE DOCUMENTOS
# ======================================================

def extrair_texto_pdf(caminho_pdf):
    """Extrai texto de um PDF."""
    texto = ""
    reader = PdfReader(caminho_pdf)
    for page in reader.pages:
        texto += page.extract_text() or ""
    return texto


def gerar_resumo(texto, max_linhas=10):
    """Gera um resumo simples do texto (sem IA externa)."""
    linhas = [l.strip() for l in texto.split("\n") if len(l.strip()) > 50]
    return "\n".join(linhas[:max_linhas])


def processar_documentos_com_progresso(pasta_base, progresso):
    """Percorre todos os PDFs e TXTs, mostrando progresso e salvando no banco."""
    inicializar_db()
    arquivos = []

    for root, _, files in os.walk(pasta_base):
        for f in files:
            if f.lower().endswith((".pdf", ".txt")):
                arquivos.append(os.path.join(root, f))

    progresso["total"] = len(arquivos)
    progresso["atual"] = 0
    progresso["status"] = "Iniciando leitura..."

    for idx, caminho in enumerate(arquivos, 1):
        nome = os.path.basename(caminho)
        progresso["arquivo"] = nome
        progresso["status"] = f"Lendo {nome}..."
        texto = ""

        try:
            if caminho.lower().endswith(".pdf"):
                texto = extrair_texto_pdf(caminho)
            else:
                with open(caminho, "r", encoding="utf-8", errors="ignore") as f:
                    texto = f.read()

            resumo = gerar_resumo(texto)
            salvar_conhecimento(nome, texto, resumo)

        except Exception as e:
            progresso["status"] = f"⚠️ Erro ao ler {nome}: {e}"

        progresso["atual"] = idx
        time.sleep(1)  # Simula tempo de processamento
        progresso["status"] = f"✅ {nome} processado"

    progresso["status"] = "🏁 Aprendizado concluído!"
    progresso["arquivo"] = ""


# ======================================================
# MODO DIRETO (sem dashboard)
# ======================================================

def carregar_todos_documentos(pasta_base="backend/dados"):
    """Lê e indexa todos os documentos da pasta."""
    inicializar_db()
    total = 0
    for root, _, files in os.walk(pasta_base):
        for f in files:
            if f.lower().endswith((".pdf", ".txt")):
                caminho = os.path.join(root, f)
                nome = os.path.basename(caminho)
                print(f"📘 Lendo {nome}...")

                if caminho.endswith(".pdf"):
                    texto = extrair_texto_pdf(caminho)
                else:
                    with open(caminho, "r", encoding="utf-8", errors="ignore") as file:
                        texto = file.read()

                resumo = gerar_resumo(texto)
                salvar_conhecimento(nome, texto, resumo)
                total += 1
                print(f"✅ {nome} indexado\n")

    print(f"🏁 {total} arquivos processados e salvos no banco.")
    return total


if __name__ == "__main__":
    carregar_todos_documentos()
