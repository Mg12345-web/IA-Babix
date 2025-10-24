import os
from pathlib import Path
from typing import List
import pdfplumber

try:
    import pytesseract
    from PIL import Image
except ImportError:
    pytesseract = None  # OCR opcional


# ============================================================
# 🔹 Funções principais
# ============================================================

def extrair_paginas(pdf_path: Path, usar_ocr: bool = False) -> List[str]:
    """
    Extrai o texto de cada página do PDF.
    Se usar_ocr=True, faz OCR em páginas que não têm texto.
    """
    paginas = []
    if not pdf_path.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {pdf_path}")

    with pdfplumber.open(str(pdf_path)) as pdf:
        for i, page in enumerate(pdf.pages, start=1):
            texto = page.extract_text(x_tolerance=1, y_tolerance=2) or ""

            # 🔍 Se a página não tiver texto, tenta OCR
            if not texto.strip() and usar_ocr and pytesseract:
                print(f"📸 Página {i} sem texto — aplicando OCR...")
                img = page.to_image(resolution=250).original
                texto = pytesseract.image_to_string(img, lang="por")

            # Limpeza básica
            texto = limpar_texto(texto)
            paginas.append(texto)

    return paginas


def extrair_texto(pdf_path: Path, usar_ocr: bool = False) -> str:
    """
    Extrai o texto completo de um PDF, aplicando OCR quando necessário.
    """
    paginas = extrair_paginas(pdf_path, usar_ocr=usar_ocr)
    texto = "\n\n".join(paginas)
    return texto


# ============================================================
# 🔹 Funções auxiliares
# ============================================================

def limpar_texto(texto: str) -> str:
    """Remove artefatos, espaços e cabeçalhos comuns de PDFs jurídicos."""
    if not texto:
        return ""

    # Remove cabeçalhos e numeração repetitiva
    texto = texto.replace("\r", "")
    texto = texto.replace("–", "-")
    texto = texto.replace("—", "-")

    # Remove páginas e rodapés comuns
    texto = re.sub(r"Página\s+\d+\s+de\s+\d+", "", texto, flags=re.I)
    texto = re.sub(r"Copyright.+?(Senatran|Detran|Denatran)", "", texto, flags=re.I)

    # Remove espaçamentos e hífens quebrando palavras
    texto = re.sub(r"(\w)-\n(\w)", r"\1\2", texto)
    texto = re.sub(r"\n{2,}", "\n", texto)
    texto = re.sub(r"[ ]{2,}", " ", texto)

    return texto.strip()


# ============================================================
# 🔹 Teste isolado
# ============================================================

if __name__ == "__main__":
    exemplo = Path("backend/dados/mbft.pdf")
    if exemplo.exists():
        print("📘 Testando leitura do MBFT...")
        conteudo = extrair_texto(exemplo, usar_ocr=True)
        print(f"\nTrecho lido:\n{'-'*40}\n{conteudo[:1000]}")
    else:
        print("⚠️ Nenhum PDF de exemplo encontrado.")
