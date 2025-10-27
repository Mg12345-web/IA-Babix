import os
import sqlite3
from backend.aprendizado import carregar_todos_documentos
from backend.indexador import indexar_mbft

print("\n==============================")
print("🚀 Iniciando rotina automática da Babix IA")
print("==============================\n")

# 1️⃣ Garante que a pasta do banco exista
os.makedirs("backend/db", exist_ok=True)

# 2️⃣ Cria o banco se não existir
db_path = "backend/db/conhecimento.db"
if not os.path.exists(db_path):
    print("⚙️ Criando banco de conhecimento...")
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS documentos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT UNIQUE,
            tipo TEXT,
            caminho TEXT
        )
    """)
    cur.execute("""
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
    print("✅ Banco criado com sucesso.")
else:
    print("🧠 Banco já existe — continuando...")

# 3️⃣ Lê e indexa todos os PDFs da pasta backend/dados
try:
    print("📘 Iniciando leitura e aprendizado...")
    total = carregar_todos_documentos("backend/dados")
    print(f"✅ {total} documentos processados.")
except Exception as e:
    print(f"❌ Erro ao ler documentos: {e}")

# 4️⃣ Reindexa fichas MBFT (divide em códigos)
try:
    print("📑 Reindexando fichas MBFT...")
    indexar_mbft()
    print("🏁 Indexação completa!")
except Exception as e:
    print(f"⚠️ Erro ao indexar fichas: {e}")

print("\n✅ Babix IA pronta para uso!\n")
