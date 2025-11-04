import os
import io
import json
from googleapiclient.discovery import build
from google.oauth2 import service_account
from googleapiclient.http import MediaIoBaseDownload
from sentence_transformers import SentenceTransformer
from chromadb import Client
from chromadb.config import Settings

# 🔹 ID da pasta do Drive (pode ajustar depois se quiser outra pasta)
DRIVE_FOLDER_ID = "1ZTrb0HdZ4yaRV4En77XzQ7izuqv-Xe38"

def get_drive_service():
    creds_json = os.getenv("GOOGLE_CREDENTIALS")
    if not creds_json:
        raise ValueError("❌ Variável GOOGLE_CREDENTIALS não configurada.")
    creds_dict = json.loads(creds_json)
    creds = service_account.Credentials.from_service_account_info(
        creds_dict,
        scopes=["https://www.googleapis.com/auth/drive.readonly"]
    )
    return build("drive", "v3", credentials=creds)

def baixar_arquivos_drive():
    service = get_drive_service()
    results = service.files().list(
        q=f"'{DRIVE_FOLDER_ID}' in parents and trashed=false",
        fields="files(id, name, mimeType)"
    ).execute()
    arquivos = results.get("files", [])
    print(f"📂 {len(arquivos)} arquivos encontrados no Drive.")

    for arquivo in arquivos:
        print(f"⬇️ Baixando: {arquivo['name']} ({arquivo['id']})")
        request = service.files().get_media(fileId=arquivo["id"])
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while not done:
            status, done = downloader.next_chunk()
        fh.seek(0)

        # 🔹 Salvar temporariamente
        local_path = f"/tmp/{arquivo['name']}"
        with open(local_path, "wb") as f:
            f.write(fh.read())

        # 🔹 Extrair texto básico
        if arquivo["mimeType"] == "application/pdf":
            from PyPDF2 import PdfReader
            reader = PdfReader(local_path)
            text = "\n".join([p.extract_text() or "" for p in reader.pages])
        elif arquivo["mimeType"] in [
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        ]:
            import docx
            doc = docx.Document(local_path)
            text = "\n".join([p.text for p in doc.paragraphs])
        else:
            print(f"⚠️ Tipo não suportado: {arquivo['mimeType']}")
            continue

        # 🔹 Enviar pro banco vetorial
        embedder = SentenceTransformer("all-MiniLM-L6-v2")
        embedding = embedder.encode([text])[0]

        chroma_client = Client(Settings(chroma_db_impl="duckdb+parquet", persist_directory="./chroma_db"))
        collection = chroma_client.get_or_create_collection(name="babix_docs")
        collection.add(documents=[text], embeddings=[embedding], metadatas=[{"name": arquivo["name"]}])

        print(f"✅ {arquivo['name']} indexado com sucesso!")

if __name__ == "__main__":
    baixar_arquivos_drive()
