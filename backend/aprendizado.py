import os
import sqlite3
import time
import hashlib
import numpy as np
from PyPDF2 import PdfReader
from sentence_transformers import SentenceTransformer

DB_PATH = "backend/db/conhecimento.db"

# Variável global para progresso
progresso_global = {"status": "aguardando", "atual": 0, "total": 0, "arquivo": ""}

# ======================================================
# 🔹 Inicialização e Banco de Dados
# ======================================================

def inicializar_db():
    """Cria o banco e as tabelas caso não existam."""
    os.makedirs("backend/db", exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Tabela de documentos
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS documentos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT UNIQUE,
            tipo TEXT,
            caminho TEXT
        )
    """)

    # Tabela de fichas com embeddings
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS fichas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo TEXT UNIQUE,
            titulo TEXT,
            resumo TEXT,
            conteudo TEXT,
            documento_id INTEGER,
            hash TEXT UNIQUE,
            embedding BLOB,
            FOREIGN KEY (documento_id) REFERENCES documentos (id)
        )
    """)

    conn.commit()
    conn.close()


# ======================================================
# 🔹 Utilitários de Processamento
# ======================================================

def gerar_hash(texto: str) -> str:
    """Cria hash SHA256 para evitar duplicações."""
    return hashlib.sha256(texto.strip().encode("utf-8")).hexdigest()


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
    return "\n".join(linhas[:max_linhas]) if linhas else texto[:500]


# ======================================================
# 🔹 Funções de Salvamento
# ======================================================

def salvar_conhecimento(fonte, texto, resumo="", embedder=None):
    """Salva conteúdo e embedding no banco."""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Registra o documento, se necessário
    cur.execute("""
        INSERT OR IGNORE INTO documentos (nome, tipo, caminho)
        VALUES (?, ?, ?)
    """, (fonte, "pdf", fonte))
    conn.commit()

    cur.execute("SELECT id FROM documentos WHERE nome=?", (fonte,))
    doc_id = cur.fetchone()[0]

    # Gera hash e embedding
    hash_id = gerar_hash(texto)
    embedding = embedder.encode(texto)
    embedding_bytes = np.array(embedding, dtype=np.float32).tobytes()

    cur.execute("""
        INSERT OR REPLACE INTO fichas (codigo, titulo, resumo, conteudo, documento_id, hash, embedding)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (f"{fonte}-GERAL", f"Documento {fonte}", resumo, texto, doc_id, hash_id, embedding_bytes))

    conn.commit()
    conn.close()
    print(f"✅ {fonte} indexado com sucesso e embeddings gerados.")


# ======================================================
# 🔹 Aprendizado com Progresso
# ======================================================

def processar_documentos_com_progresso(pasta_base, progresso):
    """Percorre todos os PDFs e TXTs, mostrando progresso e salvando no banco."""
    inicializar_db()
    embedder = SentenceTransformer("all-MiniLM-L6-v2")

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

        try:
            if caminho.lower().endswith(".pdf"):
                texto = extrair_texto_pdf(caminho)
            else:
                with open(caminho, "r", encoding="utf-8", errors="ignore") as f:
                    texto = f.read()

            resumo = gerar_resumo(texto)
            salvar_conhecimento(nome, texto, resumo, embedder=embedder)

        except Exception as e:
            progresso["status"] = f"⚠️ Erro ao ler {nome}: {e}"

        progresso["atual"] = idx
        progresso["status"] = f"✅ {nome} processado"
        time.sleep(1)

    progresso["status"] = "🏁 Aprendizado concluído!"
    progresso["arquivo"] = ""


# ======================================================
# 🔹 Modo Direto (sem dashboard)
# ======================================================

def carregar_todos_documentos(pasta_base="dados"):
    """Lê e indexa todos os documentos da pasta."""
    inicializar_db()
    embedder = SentenceTransformer("all-MiniLM-L6-v2")
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
                salvar_conhecimento(nome, texto, resumo, embedder=embedder)
                total += 1
                print(f"✅ {nome} indexado\n")

    print(f"🏁 {total} arquivos processados e salvos no banco.")
    return total


if __name__ == "__main__":
    carregar_todos_documentos()
