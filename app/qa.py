
from .db import search_fts

# Simple rule-based snippets for frequent questions (can expand later)
RULES = [
    ("cinto", "A infração por dirigir sem cinto de segurança é grave, com multa de R$ 195,23 e 5 pontos na CNH (art. 167 do CTB)."),
    ("lei seca", "Lei Seca: combinação de arts. 165, 165-A e 306 do CTB; sanções administrativas e crime por concentração de álcool igual/superior a 6 decigramas por litro de sangue ou 0,3 mg/L de ar alveolar.")
]

def rule_based_answer(q):
    ql = q.lower()
    for key, ans in RULES:
        if key in ql:
            return ans
    return None

def answer(question: str):
    # 1) Try rules for instant replies
    rb = rule_based_answer(question)
    # 2) Retrieve top passages via FTS5
    hits = search_fts(question, limit=6)
    citations = []
    if hits:
        # Build a concise extractive reply
        top_snippets = [h["snippet"] for h in hits[:3]]
        reply = (rb + "\n\n" if rb else "") + " ".join(top_snippets)
        citations = [{"url": h["url"], "title": h["title"]} for h in hits[:3]]
        return reply, citations
    # Fallback
    return (rb or "Não encontrei base suficiente ainda. Tente reformular ou ingira mais fontes."), citations
