# watcher.py
import time
import requests
import os
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

API_URL = "https://ia-babix-production.up.railway.app/api/aprender"
DADOS_PATH = "dados"  # ← antes era backend/dados

class WatcherHandler(FileSystemEventHandler):
    def on_created(self, event):
        if not event.is_directory and event.src_path.endswith((".pdf", ".txt")):
            print(f"📄 Novo arquivo detectado: {event.src_path}")
            try:
                resp = requests.post(API_URL)
                print(f"🚀 Aprendizado disparado! Resposta: {resp.text}")
            except Exception as e:
                print(f"⚠️ Erro ao enviar para API: {e}")

if __name__ == "__main__":
    print("👀 Monitorando pasta:", DADOS_PATH)
    event_handler = WatcherHandler()
    observer = Observer()
    observer.schedule(event_handler, DADOS_PATH, recursive=False)
    observer.start()
    try:
        while True:
            time.sleep(5)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
