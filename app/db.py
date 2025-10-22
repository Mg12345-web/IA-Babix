
import os, sqlite3, time

DB_PATH = os.path.join(os.path.dirname(__file__), "trafficlaw.db")

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_conn()
    cur = conn.cursor()
    # Sources (unique URL)
    cur.execute('''CREATE TABLE IF NOT EXISTS sources(
        id INTEGER PRIMARY KEY,
        url TEXT UNIQUE,
        title TEXT,
        fetched_at INTEGER,
        status TEXT,
        http_status INTEGER,
        hash TEXT
    )''')

    # Raw documents
    cur.execute('''CREATE TABLE IF NOT EXISTS documents(
        id INTEGER PRIMARY KEY,
        source_id INTEGER,
        content TEXT,
        FOREIGN KEY(source_id) REFERENCES sources(id)
    )''')

    # Chunks for retrieval
    cur.execute('''CREATE TABLE IF NOT EXISTS chunks(
        id INTEGER PRIMARY KEY,
        source_id INTEGER,
        chunk_index INTEGER,
        text TEXT,
        FOREIGN KEY(source_id) REFERENCES sources(id)
    )''')

    # Full-text virtual table (FTS5) mirroring chunks
    cur.execute('''CREATE VIRTUAL TABLE IF NOT EXISTS chunks_fts USING fts5(
        text, source_id UNINDEXED, chunk_id UNINDEXED, content=''
    )''')

    conn.commit()
    conn.close()

def upsert_source(url, title=None, status="new", http_status=None, content_hash=None):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("INSERT INTO sources(url, title, fetched_at, status, http_status, hash) VALUES(?,?,?,?,?,?) "
                "ON CONFLICT(url) DO UPDATE SET title=excluded.title, fetched_at=excluded.fetched_at, "
                "status=excluded.status, http_status=excluded.http_status, hash=excluded.hash",
                (url, title, int(time.time()), status, http_status, content_hash))
    conn.commit()
    cur.execute("SELECT id FROM sources WHERE url=?", (url,))
    row = cur.fetchone()
    conn.close()
    return row['id'] if row else None

def insert_document(source_id, content):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("INSERT INTO documents(source_id, content) VALUES(?,?)", (source_id, content))
    doc_id = cur.lastrowid
    conn.commit()
    conn.close()
    return doc_id

def insert_chunks(source_id, chunks):
    conn = get_conn()
    cur = conn.cursor()
    for i, text in enumerate(chunks):
        cur.execute("INSERT INTO chunks(source_id, chunk_index, text) VALUES(?,?,?)", (source_id, i, text))
        chunk_id = cur.lastrowid
        cur.execute("INSERT INTO chunks_fts(rowid, text, source_id, chunk_id) VALUES(?,?,?,?)",
                    (chunk_id, text, source_id, chunk_id))
    conn.commit()
    conn.close()

def search_fts(query, limit=8):
    conn = get_conn()
    cur = conn.cursor()
    # Use BM25 ranking built into FTS5
    cur.execute("""
        SELECT c.id as chunk_id, c.source_id, s.url, s.title,
               snippet(chunks_fts, 0, '<b>', '</b>', '…', 12) as snippet,
               rank
        FROM (SELECT rowid, bm25(chunks_fts) as rank FROM chunks_fts
              WHERE chunks_fts MATCH ?) r
        JOIN chunks c ON c.id = r.rowid
        JOIN sources s ON s.id = c.source_id
        ORDER BY r.rank ASC
        LIMIT ?
    """, (query, limit))
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows
