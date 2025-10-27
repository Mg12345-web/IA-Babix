import os, sqlite3

os.makedirs("backend/db", exist_ok=True)

db = sqlite3.connect("backend/db/conhecimento.db")
cur = db.cursor()

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

db.commit()
db.close()
print("✅ Banco 'conhecimento.db' criado com sucesso em backend/db/")
