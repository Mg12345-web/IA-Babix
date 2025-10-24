import re
import sqlite3
from pathlib import Path

# Caminho do banco
BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "backend" / "db" / "conhecimento.db"

# ------------------------------------------------------------
# Funções principais
# ------------------------------------------------------------

def _conn():
    """Abre conexão com o banco"""
    return sqlite3.connect(str(DB_PATH))


def carregar_texto_geral() -> str:
    """Lê o conteúdo completo do MBFT geral"""
    with _conn() as conn:
        cur = conn.cursor()
        cur.execute("SELECT conteudo FROM fichas WHERE codigo='MBFT-GERAL' ORDER BY id DESC LIMIT 1")
        row = cur.fetchone()
    return row[0] if row else ""


def limpar_fichas_antigas():
    """Remove fichas antigas (mantém apenas a geral)"""
    with _conn() as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM fichas WHERE codigo != 'MBFT-GERAL'")
        conn.commit()


# ------------------------------------------------------------
# Função de divisão com regex aprimorada
# ------------------------------------------------------------
def dividir_em_fichas(texto: str):
    """
    Divide o texto em fichas individuais com base no padrão de código (ex: 596-70).
    Retorna uma lista de tuplas (codigo, conteudo).
    """

    # Normaliza caracteres problemáticos
    texto = texto.replace("\r", "")
    texto = re.sub(r"[ ]{2,}", " ", texto)  # remove espaços repetidos
    texto = re.sub(r"\n{2,}", "\n", texto)  # normaliza quebras duplas

    # Regex mais robusta: detecta o código e isola até o próximo código
    padrao = re.compile(
        r"(?P<codigo>\d{3}-\d{2})[\s–-]+(?P<conteudo>.*?)(?=\n\d{3}-\d{2}[\s–-]|$)",
        re.S
    )

    fichas = padrao.findall(texto)
    print(f"🔎 Detectadas {len(fichas)} possíveis fichas no MBFT.")
    return fichas


# ------------------------------------------------------------
# Salvamento com logs e verificação
# ------------------------------------------------------------
def salvar_fichas(fichas):
    """Salva as fichas individuais no banco"""
    if not fichas:
        print("⚠️ Nenhuma ficha para salvar.")
        return

    with _conn() as conn:
        cur = conn.cursor()
        # Busca o documento MBFT
        cur.execute("SELECT id FROM documentos WHERE nome='MBFT'")
        doc_id = cur.fetchone()[0]

        count = 0
        for codigo, conteudo in fichas:
            # Limpeza e formatação
            codigo = codigo.strip()
            conteudo = conteudo.strip()
            titulo = conteudo.split("\n")[0][:200] if conteudo else "(sem título)"

            # Salvamento
            cur.execute("""
                INSERT OR REPLACE INTO fichas 
                (codigo, titulo, conteudo, documento_id)
                VALUES (?, ?, ?, ?)
            """, (codigo, titulo, conteudo, doc_id))
            count += 1

            # Log parcial a cada 50 fichas
            if count % 50 == 0:
                print(f"📄 {count} fichas processadas...")

        conn.commit()
    print(f"📑 {count} fichas indexadas e armazenadas com sucesso!")


# ------------------------------------------------------------
# Execução principal
# ------------------------------------------------------------
def indexar_mbft():
    """Cria fichas reais a partir do MBFT geral"""
    texto = carregar_texto_geral()
    if not texto:
        print("⚠️ Nenhum conteúdo encontrado no MBFT-GERAL.")
        return

    print("🔍 Iniciando indexação das fichas do MBFT...")
    limpar_fichas_antigas()
    fichas = dividir_em_fichas(texto)

    if not fichas:
        print("⚠️ Nenhuma ficha foi detectada no texto. Verifique o formato.")
        return

    salvar_fichas(fichas)
    print("✅ Indexação concluída e fichas armazenadas no banco.")


if __name__ == "__main__":
    indexar_mbft()
