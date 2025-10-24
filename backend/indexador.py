import re
import sqlite3
from backend.aprendizado import DB_PATH

def conectar():
    return sqlite3.connect(DB_PATH)


def extrair_fichas(texto):
    """
    Divide o texto do MBFT em fichas individuais com base nos códigos (ex: 596-70, 554-12, etc.).
    """
    padrao = re.compile(r"(\d{3}-\d{2})")  # Ex: 596-70
    blocos = padrao.split(texto)
    fichas = []

    for i in range(1, len(blocos), 2):
        codigo = blocos[i].strip()
        conteudo = blocos[i + 1].strip() if i + 1 < len(blocos) else ""
        if len(conteudo) > 30:  # evita falsos positivos
            fichas.append((codigo, conteudo))
    return fichas


def indexar_fichas():
    """
    Lê o texto geral do MBFT e cria fichas individuais no banco.
    """
    conn = conectar()
    cur = conn.cursor()

    cur.execute("SELECT conteudo FROM fichas WHERE codigo = 'MBFT-GERAL' LIMIT 1")
    row = cur.fetchone()
    if not row:
        print("⚠️ Nenhum texto geral encontrado. Execute carregar_conhecimento() primeiro.")
        conn.close()
        return

    texto = row[0]
    fichas = extrair_fichas(texto)
    total = 0

    for codigo, conteudo in fichas:
        cur.execute("""
            INSERT OR REPLACE INTO fichas (codigo, titulo, conteudo)
            VALUES (?, ?, ?)
        """, (codigo, f"Ficha {codigo}", conteudo))
        total += 1

    conn.commit()
    conn.close()

    print(f"📑 {total} fichas indexadas com sucesso!")


if __name__ == "__main__":
    indexar_fichas()
