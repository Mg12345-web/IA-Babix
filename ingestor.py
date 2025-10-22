import os
from dotenv import load_dotenv
from typing import List

# --- LangChain Components ---
from langchain_community.document_loaders import PyPDFLoader, WebBaseLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.schema import Document

# --- Vector Store (PostgreSQL com pgvector) ---
from langchain_community.vectorstores import PGVector
from langchain_community.embeddings import SentenceTransformerEmbeddings

# Carrega as variáveis de ambiente (chaves, credenciais do DB, etc.)
load_dotenv()

# --- 1. Configuração Global ---

# Modelo de Embedding (O "Entendimento" do Texto)
# Usaremos um modelo local de boa performance para Direito
EMBEDDING_MODEL = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2") 

# Conexão com o PostgreSQL do Railway
CONNECTION_STRING = PGVector.connection_string_from_db_params(
    driver="psycopg2",
    host=os.getenv("PGHOST"),
    port=int(os.getenv("PGPORT")),
    database=os.getenv("PGDATABASE"),
    user=os.getenv("PGUSER"),
    password=os.getenv("PGPASSWORD"),
)

# Nome da coleção no DB (como se fosse o nome da sua "Biblioteca de Trânsito")
COLLECTION_NAME = "direito_transito_brasileiro"

# Configuração do divisor de texto (Text Splitter)
TEXT_SPLITTER = RecursiveCharacterTextSplitter(
    # Chunk size: tamanho ideal para contexto (ex: 1500 caracteres)
    chunk_size=1500,
    # Overlap: permite que os chunks adjacentes tenham contexto sobre o anterior
    chunk_overlap=150,
    length_function=len,
    is_separator_regex=False,
)

# --- 2. Funções de Ingestão de Documentos ---

def load_and_split(loader_instance) -> List[Document]:
    """Carrega documentos usando um Loader e divide em chunks."""
    try:
        documents = loader_instance.load()
        # Adiciona metadados padronizados (fonte)
        for doc in documents:
            doc.metadata['source_type'] = type(loader_instance).__name__
        
        # Divide o documento em chunks
        return TEXT_SPLITTER.split_documents(documents)
    except Exception as e:
        print(f"Erro ao carregar ou dividir: {e}")
        return []

def ingest_pdf(url: str):
    """Processa um link direto para um PDF."""
    print(f"-> Ingerindo PDF: {url}")
    # Usa o PyPDFLoader para baixar e extrair o texto
    loader = PyPDFLoader(url)
    chunks = load_and_split(loader)
    return chunks

def ingest_webpage(url: str):
    """Processa uma página HTML (tabelas, textos de lei, etc.)."""
    print(f"-> Ingerindo WebPage: {url}")
    # Usa o WebBaseLoader, que utiliza BeautifulSoup para extração
    loader = WebBaseLoader(
        web_paths=(url,),
        # O parser 'lxml' é geralmente mais rápido, mas 'html5lib' é mais robusto
        bs_kwargs={"features": "html.parser"}, 
    )
    chunks = load_and_split(loader)
    return chunks

# --- 3. Funções de Armazenamento ---

def store_in_db(chunks: List[Document]):
    """Armazena os chunks no Vector Database (PostgreSQL/pgvector)."""
    if not chunks:
        print("Nenhum chunk para armazenar. Pulando o armazenamento.")
        return

    print(f"-> Armazenando {len(chunks)} chunks na coleção '{COLLECTION_NAME}'...")
    
    # O PGVector cria a tabela automaticamente se ela não existir
    PGVector.from_documents(
        embedding=EMBEDDING_MODEL,
        documents=chunks,
        connection_string=CONNECTION_STRING,
        collection_name=COLLECTION_NAME,
        # Importante: O 'pre_delete_collection=True' LIMPA a base antes de recarregar.
        # Use 'False' para adicionar novos documentos, use 'True' para atualizar.
        pre_delete_collection=False # Mantenha False para evitar apagar a base toda vez!
    )
    print("-> Armazenamento concluído com sucesso.")

# --- 4. O Fluxo Principal (O Estudo) ---

def main_ingestion():
    """Define a lista de fontes e executa o processo de ingestão."""
    
    # Sua lista de URLs, categorizada por tipo para o Loader
    sources_to_ingest = {
        # LINKS INICIAIS (Da sua base)
        "web": [
            "https://www.planalto.gov.br/ccivil_03/leis/l9503compilado.htm",  # CTB Compilado
            "https://www.planalto.gov.br/ccivil_03/_ato2019-2022/2020/lei/l14071.htm", # Alterações CTB
            # Adicione aqui todos os links do Planalto (Leis, Decretos) e as páginas do CETRAN
        ],
        "pdf": [
            "https://www.detran.am.gov.br/wp-content/uploads/2015/04/ctb.pdf",
            "https://www.gov.br/transportes/pt-br/assuntos/transito/conteudo-contran/resolucoes/Resolucao9852022.pdf", # Resolução 985/2022 (MBFT)
            # Adicione aqui os links para PDFs de Resoluções, Pareceres e Manuais (MBST)
        ],
        # ADICIONE AQUI MAIS FONTES IMPORTANTES (como as que listamos na resposta anterior)
        # Exemplo de link complementar (MBST Volume I):
        "pdf_complementar": [
            "https://www.gov.br/transportes/pt-br/assuntos/transito/arquivos-senatran/educacao/publicacoes/manual_vol_i_2.pdf", 
        ]
    }

    all_chunks = []

    # Processa todas as fontes web
    for url in sources_to_ingest["web"]:
        all_chunks.extend(ingest_webpage(url))

    # Processa todas as fontes PDF
    for url in sources_to_ingest["pdf"]:
        all_chunks.extend(ingest_pdf(url))

    # Processa as fontes complementares, se houver
    for url in sources_to_ingest.get("pdf_complementar", []):
         all_chunks.extend(ingest_pdf(url))

    # Etapa Final: Armazenar no Banco de Dados
    store_in_db(all_chunks)
    print("\n--- Processo de Ingestão (Estudo) Concluído ---")
    print(f"Total de Chunks armazenados: {len(all_chunks)}")

if __name__ == "__main__":
    # Garanta que todas as variáveis de ambiente do DB estejam setadas
    if not all(os.getenv(v) for v in ["PGHOST", "PGPORT", "PGDATABASE", "PGUSER", "PGPASSWORD"]):
        print("ERRO: Variáveis de ambiente do PostgreSQL (PGHOST, etc.) não estão configuradas.")
    else:
        main_ingestion()
