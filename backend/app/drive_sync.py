import os, io, json
from googleapiclient.discovery import build
from google.oauth2 import service_account
from googleapiclient.http import MediaIoBaseDownload

from sentence_transformers import SentenceTransformer
import chromadb

# Use pasta de persistência configurável
CHROMA_DIR = os.getenv("CHROMA_DIR", "./dados/chroma")
DRIVE_FOLDER_ID = os.getenv("DRIVE_FOLDER_ID", "1ZTrb0HdZ4yaRV4En77XzQ7izuqv-Xe38")

_embedder = None
def get_embedder():
    global _embedder
    if _embedder is None:
        _embedder = SentenceTransformer("all-MiniLM-L6-v2")
    return _embedder

def get_drive_service():
    creds_json = os.getenv("GOOGLE_CREDENTIALS")
    if not creds_json:
        raise ValueError("❌ Variável GOOGLE_CREDENTIALS não configurada.")
    creds = service_account.Credentials.from_service_account_info(
        json.loads(creds_json),
        scopes=["https://www.googleapis.com/auth/drive.readonly"]
    )
    return build("drive", "v3", credentials=creds)

def extract_text(local_path, mime):
    if mime == "application/pdf":
        from PyPDF2 import PdfReader
        reader = PdfReader(local_path)
        return "\n".join([(p.extract_text() or "") for p in reader.pages]).strip()

    if mime in ("application/vnd.openxmlformats-officedocument.wordprocessingml.document",):
        import docx
        doc = docx.Document(local_path)
        return "\n".join([p.text for p in doc.paragraphs]).strip()

    return ""  # tipos não suportados

def get_chroma():
    os.makedirs(CHROMA_DIR, exist_ok=True)
    # ✅ CORREÇÃO: Usa PersistentClient para evitar conflito
    client = chromadb.PersistentClient(path=CHROMA_DIR)
    return client.get_or_create_collection("babix_docs")

def baixar_arquivos_drive():
    """Função que indexa arquivos do Google Drive"""
    try:
        svc = get_drive_service()

        results = svc.files().list(
            q=f"'{DRIVE_FOLDER_ID}' in parents and trashed=false",
            fields="files(id,name,mimeType,modifiedTime)"
        ).execute()

        files = results.get("files", [])
        print(f"📂 {len(files)} arquivos encontrados no Drive.")

        if not files:
            print("⚠️ Nenhum arquivo encontrado. Verifique se DRIVE_FOLDER_ID está correto.")
            return

        col = get_chroma()
        embedder = get_embedder()

        for f in files:
            file_id = f["id"]
            name = f["name"]
            mime = f["mimeType"]
            print(f"⬇️ Baixando: {name} ({mime})")

            request = svc.files().get_media(fileId=file_id)
            buf = io.BytesIO()
            downloader = MediaIoBaseDownload(buf, request)
            done = False
            while not done:
                _, done = downloader.next_chunk()
            buf.seek(0)

            tmp = f"/tmp/{name}"
            with open(tmp, "wb") as out:
                out.write(buf.read())

            text = extract_text(tmp, mime)
            if not text:
                print(f"⚠️ Ignorado (tipo não suportado ou vazio): {name}")
                continue

            print(f"🔄 Gerando embedding para: {name}")
            embedding = embedder.encode([text])[0]
            
            col.add(
                documents=[text],
                embeddings=[embedding],
                metadatas=[{"name": name, "mime": mime}],
                ids=[file_id]  # evita duplicar
            )
            print(f"✅ Indexado: {name}")

        print("✅ Ingestão concluída e persistida em", CHROMA_DIR)
        
    except Exception as e:
        print(f"❌ Erro na ingestão: {str(e)}")
        import traceback
        traceback.print_exc()
