from pathlib import Path
from typing import List
import pdfplumber

def extrair_paginas(pdf_path: Path) -> List[str]:
    paginas = []
    with pdfplumber.open(str(pdf_path)) as pdf:
        for page in pdf.pages:
            text = page.extract_text(x_tolerance=1, y_tolerance=2) or ""
            paginas.append(text)
    return paginas

def extrair_texto(pdf_path: Path) -> str:
    return "\n\n".join(extrair_paginas(pdf_path))
