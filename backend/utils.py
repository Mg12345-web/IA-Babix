# utils.py
import requests
from bs4 import BeautifulSoup
import hashlib
import datetime
import re
import os
import sqlite3
from typing import List, Dict, Tuple, Optional
HEADERS = {
"User-Agent": "BabixCrawler/1.0 (+https://suaorg.com)"
}
TRUSTED_DOMAINS = [
"planalto.gov.br", "gov.br", "stj.jus.br", "stf.jus.br",
"jusbrasil.com.br",
"senatran.gov.br", "detran.gov.br"
]
def slugify_url(url: str) -> str:
return hashlib.sha1(url.encode('utf-8')).hexdigest()
def fetch_html(url: str, timeout=12) -> Optional[str]:
try:
r = requests.get(url, headers=HEADERS, timeout=timeout)
r.raise_for_status()
return r.text
except Exception as e:
print(f"[fetch_html] erro ao buscar {url}: {e}")
return None
2
def extract_text_from_html(html: str) -> str:
soup = BeautifulSoup(html, "html.parser")
for tag in soup(["script", "style", "header", "footer", "nav", "aside",
"form"]):
tag.decompose()
text = soup.get_text(separator="\n")
text = re.sub(r'\n\s+\n', '\n', text)
text = re.sub(r'[ \t]+', ' ', text)
text = text.strip()
return text
def extract_publish_date(html: str) -> Optional[str]:
soup = BeautifulSoup(html, "html.parser")
metas = soup.find_all("meta")
for m in metas:
prop = (m.get("property") or "").lower()
name = (m.get("name") or "").lower()
if prop in ("article:published_time", "og:updated_time",
"article:modified_time"):
return m.get("content")
if name in ("date", "dcterms.date", "dc.date", "pubdate"):
return m.get("content")
txt = soup.get_text()
m = re.search(r'(\d{1,2}\s+de\s+[A-Za-z]+\.?\s+\d{4})', txt)
if m:
return m.group(1)
return None
def is_trusted_url(url: str) -> bool:
for d in TRUSTED_DOMAINS:
if d.lower() in url.lower():
return True
return False
def chunk_text(text: str, chunk_size: int = 800, overlap: int = 150) ->
List[str]:
words = text.split()
chunks = []
i = 0
while i < len(words):
chunk = " ".join(words[i:i+chunk_size])
chunks.append(chunk)
i += chunk_size - overlap
return chunks
# SQLite helpers
def ensure_db(path: str):
os.makedirs(os.path.dirname(path), exist_ok=True)
conn = sqlite3.connect(path)
3
cur = conn.cursor()
cur.execute("""
 CREATE TABLE IF NOT EXISTS sources (
 id TEXT PRIMARY KEY,
 url TEXT,
 domain TEXT,
 title TEXT,
 published TEXT,
 fetched_at TEXT
 );
 """)
cur.execute("""
 CREATE TABLE IF NOT EXISTS chunks (
 id TEXT PRIMARY KEY,
 source_id TEXT,
 chunk_index INTEGER,
 text TEXT,
 embedding BLOB,
 FOREIGN KEY(source_id) REFERENCES sources(id)
 );
 """)
cur.execute("""
 CREATE TABLE IF NOT EXISTS learn_log (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 timestamp TEXT,
 action TEXT,
 info TEXT
 );
 """)
conn.commit()
conn.close()
def insert_source(db_path: str, url: str, title: str = "", published: str =
None) -> str:
sid = slugify_url(url)
conn = sqlite3.connect(db_path)
cur = conn.cursor()
cur.execute("INSERT OR IGNORE INTO sources
(id,url,domain,title,published,fetched_at) VALUES (?,?,?,?,?,?)",
(sid, url, re.sub(r'https?://(www\.)?','',url).split('/')[0],
title, published, datetime.datetime.utcnow().isoformat()))
conn.commit()
conn.close()
return sid
def insert_chunk(db_path: str, source_id: str, idx: int, text: str):
cid = f"{source_id}-{idx}"
conn = sqlite3.connect(db_path)
cur = conn.cursor()
cur.execute("INSERT OR IGNORE INTO chunks (id,source_id,chunk_index,text)
4
VALUES (?,?,?,?)",
(cid, source_id, idx, text))
conn.commit()
conn.close()
def log_action(db_path: str, action: str, info: str = ""):
conn = sqlite3.connect(db_path)
cur = conn.cursor()
cur.execute("INSERT INTO learn_log (timestamp,action,info) VALUES
(?,?,?)",
(datetime.datetime.utcnow().isoformat(), action, info))
conn.commit()
conn.close()
