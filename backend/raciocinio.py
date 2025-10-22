# raciocinio.py
import sqlite3
from typing import List, Dict
from utils import ensure_db
CONFIDENCE_THRESHOLD = 0.55
MIN_SUPPORT_SOURCES = 1
def simple_search_chunks(db_path: str, keywords: List[str]) -> List[Dict]:
conn = sqlite3.connect(db_path)
cur = conn.cursor()
like_clauses = []
params = []
for k in keywords:
like_clauses.append(' text LIKE ? ')
params.append(f"%{k}%")
q = 'SELECT id, source_id, chunk_index, text FROM chunks '
if like_clauses:
q += ' WHERE ' + ' AND '.join(like_clauses)
q += ' LIMIT 200'
cur.execute(q, params)
6
rows = cur.fetchall()
conn.close()
return [{'id': r[0], 'source_id': r[1], 'idx': r[2], 'text': r[3]} for r
in rows]
def evaluate_topic(db_path: str, keywords: List[str]) -> Dict:
chunks = simple_search_chunks(db_path, keywords)
if not chunks:
return {'ok': False, 'message': 'Nenhuma evidência encontrada',
'confidence': 0.0}
# agrupar por source
by_source = {}
for c in chunks:
by_source.setdefault(c['source_id'], []).append(c)
supports = [{'source': s, 'count': len(v), 'sample': v[0]['text'][:600]}
for s, v in by_source.items()]
supports = sorted(supports, key=lambda x: x['count'], reverse=True)
top = supports[0]
support_count = len(supports)
confidence = min(0.99, 0.1 + 0.9 * (top['count'] / (top['count'] +
support_count)))
ok = (confidence >= CONFIDENCE_THRESHOLD and support_count >=
MIN_SUPPORT_SOURCES)
return {
'ok': ok,
'confidence': confidence,
'support_count': support_count,
'top': top,
'all_supports': supports
}
