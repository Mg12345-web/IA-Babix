
# MVP de memória: guarda pares (hash_fatos -> texto) em dicionário.
# Para produção, mover para Postgres, com similaridade e deduplicação.
import hashlib

class MemoryService:
    def __init__(self):
        self.db = {}

    def signature(self, fatos: str) -> str:
        return hashlib.sha256(fatos.strip().lower().encode()).hexdigest()

    def get_similar(self, fatos: str):
        sig = self.signature(fatos)
        return self.db.get(sig)

    def save(self, fatos: str, texto: str):
        sig = self.signature(fatos)
        self.db[sig] = texto
