import os
import json
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import io

def connect_to_drive():
    """Cria uma conexão com o Google Drive usando a variável do Railway"""
    creds_data = os.getenv("GOOGLE_CREDENTIALS")

    if not creds_data:
        raise ValueError("❌ Variável GOOGLE_CREDENTIALS não encontrada no ambiente.")

    # Converte o texto JSON da variável em dicionário Python
    creds_dict = json.loads(creds_data)

    # Cria as credenciais a partir do dicionário
    creds = service_account.Credentials.from_service_account_info(creds_dict, scopes=["https://www.googleapis.com/auth/drive.readonly"])

    # Conecta na API do Google Drive
    service = build("drive", "v3", credentials=creds)
    print("✅ Conectado ao Google Drive com sucesso!")
    return service


def listar_arquivos_drive(service, quantidade=10):
    """Lista os primeiros arquivos encontrados no Drive jurídico"""
    results = service.files().list(
        pageSize=quantidade,
        fields="files(id, name, mimeType)"
    ).execute()

    arquivos = results.get("files", [])
    if not arquivos:
        print("Nenhum arquivo encontrado.")
    else:
        print("🗂 Arquivos disponíveis:")
        for f in arquivos:
            print(f"{f['name']} ({f['id']})")
    return arquivos
