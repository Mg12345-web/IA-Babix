
# MVP simples: indexa texto bruto em memória e retorna trechos "fakes".
# Você pode evoluir para FAISS + embeddings locais.

import os, re
from typing import List

class RagService:
    def __init__(self, store_path: str):
        self.store_path = store_path
        os.makedirs(self.store_path, exist_ok=True)
        self.docs = []  # [(path, text)]

    def ingest_file(self, path: str) -> int:
        try:
            text = self._extract_text(path)
            self.docs.append((path, text))
            return max(1, len(text)//1000)
        except Exception as e:
            return 0

    def retrieve(self, query: str, k: int = 5) -> List[str]:
        # Heurística simples: retorna linhas que contêm palavras da query
        keywords = [w for w in re.findall(r"\w+", query.lower()) if len(w) > 3]
        hits = []
        for _, txt in self.docs:
            lines = [ln.strip() for ln in txt.splitlines() if ln.strip()]
            scored = [(sum(kw in ln.lower() for kw in keywords), ln) for ln in lines]
            scored = [ln for sc, ln in scored if sc > 0]
            hits.extend(scored[:k])
        return hits[:k]

    def _extract_text(self, path: str) -> str:
        # Só lê como texto bruto; para PDF use pdfminer.six (futuro)
        with open(path, "rb") as f:
            try:
                raw = f.read().decode("utf-8", errors="ignore")
            except:
                raw = ""
        return raw or f"[conteúdo binário: {os.path.basename(path)}]"
