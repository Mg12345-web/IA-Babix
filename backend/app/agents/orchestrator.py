
from typing import Tuple, List
from ..services.rag_service import RagService
from ..services.memory_service import MemoryService

ASK_TEMPLATE = [
    "Informe a data e hora do AIT.",
    "Confirme o local exato (logradouro, nº, sentido).",
    "Há fotos, vídeos ou testemunhas anexas?",
    "O campo 'Observações' do AIT está legível/completo?"
]

class Orchestrator:
    def __init__(self, rag: RagService, memory: MemoryService):
        self.rag = rag
        self.memory = memory

    def answer(self, pergunta: str, caso: dict) -> Tuple[str, List[str], List[str]]:
        # 1) Memória: se já vimos fatos iguais, reaproveitar
        fatos = caso.get("fatos", "")
        reused = self.memory.get_similar(fatos) if fatos else None

        # 2) RAG: recuperar trechos simples (MVP)
        fontes = self.rag.retrieve(pergunta, k=5)

        # 3) Heurística de resposta (MVP rule-based)
        if reused:
            resposta = "Encontrei um caso semelhante. Adaptei a tese:
" + reused
        else:
            corpo = [
                "Baseado na sua pergunta, seguem diretrizes iniciais para a peça:",
                "• Verificar vícios formais do AIT (art. 280 CTB) e descrição adequada dos fatos;",
                "• Conferir prazos e regularidade da notificação;",
                "• Levantar jurisprudências específicas (com links) para reforço.",
            ]
            resposta = "\n".join(corpo)

        perguntas = ASK_TEMPLATE[:]
        return resposta, fontes, perguntas
