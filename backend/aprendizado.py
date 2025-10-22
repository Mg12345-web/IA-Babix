# aprendizado.py
import argparse
import os
import time
from utils import (
    fetch_html, extract_text_from_html, extract_publish_date,
    chunk_text, ensure_db, insert_source, insert_chunk,
    is_trusted_url, log_action
)
from sentence_transformers import SentenceTransformer
from googleapiclient.discovery import build

MODEL_NAME = "all-MiniLM-L6-v2"
API_KEY = os.getenv("GOOGLE_API_KEY")
CX = os.getenv("GOOGLE_CX")  # ID do Custom Search Engine
TRUSTED_DOMAINS = {"planalto.gov.br","gov.br","stj.jus.br","stf.jus.br","detran.gov.br"}

def search_web(query, num=10):
    service = build("customsearch", "v1", developerKey=API_KEY)
    res = service.cse().list(q=query, cx=CX, num=num).execute()
    return [item["link"] for item in res.get("items", [])]

def index_query(db_path: str, query: str, model):
    urls = search_web(query, num=10)
    for url in urls:
        domain = url.split("/")[2]
        if not is_trusted_url(domain):
            continue
        html = fetch_html(url)
        if not html:
            continue
        text = extract_text_from_html(html)
        if len(text) < 200:
            continue
        published = extract_publish_date(html)
        source_id = insert_source(db_path, url, title=None, published=published)
        chunks = chunk_text(text, chunk_size=600, overlap=100)
        embeddings = model.encode(chunks, convert_to_numpy=True)
        for idx, ch in enumerate(chunks):
            insert_chunk(db_path, source_id, idx, ch)
        log_action(db_path, 'index_query', query)
        print(f"[index] query={query} url={url} chunks={len(chunks)}")
    return True

def main():
    parser = argparse.ArgumentParser(description="Indexa web por query de GT")
    parser.add_argument("--db", default="db/conhecimento.db")
    parser.add_argument("--query", required=True, help="Termos de busca")
    args = parser.parse_args()
    ensure_db(args.db)
    model = SentenceTransformer(MODEL_NAME)
    index_query(args.db, args.query, model)

if __name__ == "__main__":
    main()
