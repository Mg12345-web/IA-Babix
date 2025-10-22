import os
import requests
from langchain_community.document_loaders import WebBaseLoader, PyPDFLoader
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains import RetrievalQA
from langchain_openai import ChatOpenAI

BASE_PATH = "data/documentos_indexados"
DB_PATH = os.path.join(BASE_PATH, "chroma_db")

# Lista inicial de links (pode vir do .txt que você mandou)
LINKS_INICIAIS = [
    "https://www.planalto.gov.br/ccivil_03/leis/l9503compilado.htm",
    "https://www.gov.br/transportes/pt-br/assuntos/transito/conteudo-contran/resolucoes/Resolucao9852022.pdf",
    "https://www.planalto.gov.br/ccivil_03/_ato2019-2022/2020/lei/l14071.htm",
]

def carregar_base():
    os.makedirs(BASE_PATH, exist_ok=True)

    docs = []
    for link in LINKS_INICIAIS:
        try:
            if link.endswith(".pdf"):
                loader = PyPDFLoader(link)
            else:
                loader = WebBaseLoader(link)
            docs.extend(loader.load())
        except Exception as e:
            print(f"Erro ao carregar {link}: {e}")

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    textos = text_splitter.split_documents(docs)

    embeddings = OpenAIEmbeddings()
    db = Chroma.from_documents(textos, embeddings, persist_directory=DB_PATH)
    db.persist()

def responder_usuario(pergunta: str) -> str:
    embeddings = OpenAIEmbeddings()
    db = Chroma(persist_directory=DB_PATH, embedding_function=embeddings)
    retriever = db.as_retriever(search_kwargs={"k": 4})
    
    modelo = ChatOpenAI(temperature=0.3, model="gpt-4o-mini")
    qa_chain = RetrievalQA.from_chain_type(modelo, retriever=retriever)
    resposta = qa_chain.run(pergunta)
    return resposta
