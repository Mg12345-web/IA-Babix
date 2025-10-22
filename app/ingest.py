
import hashlib, re, time, requests
from bs4 import BeautifulSoup
from .db import upsert_source, insert_document, insert_chunks

HEADERS = {
    "User-Agent": "TrafficLawAI/0.1 (+https://example.com; contato@trafficlaw.local)"
}

def clean_text(html):
    soup = BeautifulSoup(html, "html.parser")
    # remove scripts/styles/navs
    for tag in soup(["script","style","noscript","header","footer","nav","aside"]):
        tag.decompose()
    text = soup.get_text(separator=" ")
    # normalize spaces
    text = re.sub(r"\s+", " ", text).strip()
    return text

def chunk_text(text, max_len=1200, overlap=120):
    words = text.split()
    chunks = []
    start = 0
    while start < len(words):
        end = min(start + max_len, len(words))
        chunk = " ".join(words[start:end])
        chunks.append(chunk)
        if end == len(words): break
        start = end - overlap
        if start < 0: start = 0
    return chunks

def fetch_and_index(url, timeout=20):
    try:
        r = requests.get(url, headers=HEADERS, timeout=timeout, allow_redirects=True)
        status = r.status_code
        content = r.text if r.ok else ""
    except Exception as e:
        status = None
        content = ""
    content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest() if content else None
    title = None
    text_content = ""
    if content:
        # extract title
        try:
            soup = BeautifulSoup(content, "html.parser")
            title = soup.title.string.strip() if soup.title else url
        except Exception:
            title = url
        text_content = clean_text(content)

    source_id = upsert_source(url, title=title, status="fetched" if content else "error",
                              http_status=status, content_hash=content_hash)
    if text_content:
        insert_document(source_id, text_content)
        chunks = chunk_text(text_content)
        insert_chunks(source_id, chunks)
    return {"url": url, "status": status or 0, "title": title, "length": len(text_content)}
