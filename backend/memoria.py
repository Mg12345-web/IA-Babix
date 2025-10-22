# backend/memoria.py

import sqlite3
from backend.utils import ensure_db

DB_PATH = "db/conhecimento.db"

class Memoria:
    def __init__(self, db_path=DB_PATH):
        ensure_db(db_path)
        self.db_path = db_path

    def list_sources(self):
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute(
            "SELECT id, url, domain, title, published, fetched_at "
            "FROM sources ORDER BY fetched_at DESC"
        )
        rows = cur.fetchall()
        conn.close()
        return rows

    def list_chunks(self, limit=200):
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute(
            "SELECT id, source_id, chunk_index, SUBSTR(text,1,800) "
            "FROM chunks ORDER BY rowid DESC LIMIT ?",
            (limit,),
        )
        rows = cur.fetchall()
        conn.close()
        return rows

    def get_chunk_text(self, chunk_id):
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute("SELECT text FROM chunks WHERE id=?", (chunk_id,))
        r = cur.fetchone()
        conn.close()
        return r[0] if r else None

    def list_learn_logs(self, limit=50):
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute(
            "SELECT timestamp, action, param "
            "FROM learn_log ORDER BY timestamp DESC LIMIT ?",
            (limit,),
        )
        rows = cur.fetchall()
        conn.close()
        return [{"timestamp": r[0], "action": r[1], "param": r[2]} for r in rows]
