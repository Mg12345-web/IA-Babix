from pathlib import Path
from typing import List
import pdfplumber
from pdf2image import convert_from_path
import pytesseract
import io

def extrair_texto(pdf_path: Path) -> str:
    """
    Extrai texto do PDF (modo híbrido):
    1. Usa pdfplumber para leitura normal;
    2. Se a página não tiver texto legível, aplica OCR.
    """
    texto_total = []
    with pdfplumber.open(str(pdf_path)) as pdf:
        for i, page in enumerate(pdf.pages):
            text = page.extract_text(x_tolerance=1, y_tolerance=2)
            if text and len(text.strip()) > 20:
                texto_total.append(text)
            else:
                # OCR automático para páginas escaneadas
                print(f"🔍 Página {i+1}: usando OCR (sem texto legível).")
                image = convert_from_path(str(pdf_path), first_page=i+1, last_page=i+1)[0]
                ocr_text = pytesseract.image_to_string(image, lang="por")
                texto_total.append(ocr_text)
    return "\n\n".join(texto_total)

def extrair_paginas(pdf_path: Path) -> List[str]:
    """
    Extrai texto página por página.
    """
    paginas = []
    with pdfplumber.open(str(pdf_path)) as pdf:
        for i, page in enumerate(pdf.pages):
            text = page.extract_text(x_tolerance=1, y_tolerance=2)
            if not text or len(text.strip()) < 10:
                # OCR fallback
                image = convert_from_path(str(pdf_path), first_page=i+1, last_page=i+1)[0]
                text = pytesseract.image_to_string(image, lang="por")
            paginas.append(text)
    return paginas
