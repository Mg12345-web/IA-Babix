# aprendizado.py
import argparse
import os
import time
from utils import fetch_html, extract_text_from_html, extract_publish_date,
chunk_text, ensure_db, insert_source, insert_chunk, is_trusted_url,
log_action
from sentence_transformers import SentenceTransformer
MODEL_NAME = "all-MiniLM-L6-v2" # leve
def index_html_url(db_path: str, url: str, model):
html = fetch_html(url)
if not html:
return False
text = extract_text_from_html(html)
if len(text) < 200:
return False
published = extract_publish_date(html)
source_id = insert_source(db_path, url, title=None, published=published)
chunks = chunk_text(text, chunk_size=600, overlap=100)
# embeddings (salvar opcionalmente em FAISS)
embeddings = model.encode(chunks, convert_to_numpy=True)
for idx, ch in enumerate(chunks):
insert_chunk(db_path, source_id, idx, ch)
log_action(db_path, 'index_url', url)
print(f"[index] url={url} chunks={len(chunks)}")
return True
def web_crawl_and_index(db_path: str, seed_file: str = 'dados/
seed_urls.txt'):
ensure_db(db_path)
5
model = SentenceTransformer(MODEL_NAME)
if not os.path.exists(seed_file):
print('[aviso] seed_urls.txt não encontrado; crie dados/seed_urls.txt com
URLs confiáveis')
return
with open(seed_file, 'r', encoding='utf-8') as f:
urls = [l.strip() for l in f.readlines() if l.strip()]
for url in urls:
try:
if not is_trusted_url(url):
print(f"[skip] url não confiável: {url}")
continue
index_html_url(db_path, url, model)
time.sleep(1)
except Exception as e:
print('erro indexando', url, e)
if __name__ == '__main__':
parser = argparse.ArgumentParser()
parser.add_argument('--db', default='db/conhecimento.db')
parser.add_argument('--mode', default='web')
args = parser.parse_args()
web_crawl_and_index(args.db)
