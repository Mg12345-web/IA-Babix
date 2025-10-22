import os
import requests
import fitz  # PyMuPDF
from bs4 import BeautifulSoup
import re
import pickle
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

DATA_PATH = "backend/data/base_conhecimento.pkl"

# ======== FUNÇÃO: Extrair texto dos links ========

def extrair_texto_link(url):
    texto = ""
    try:
        if url.endswith(".pdf"):
            response = requests.get(url, timeout=15)
            pdf_data = fitz.open(stream=response.content, filetype="pdf")
            for page in pdf_data:
                texto += page.get_text()
        else:
            response = requests.get(url, timeout=15)
            soup = BeautifulSoup(response.text, "html.parser")
            texto = soup.get_text(separator=" ", strip=True)
        return limpar_texto(texto)
    except Exception as e:
        print(f"Erro ao processar {url}: {e}")
        return ""

# ======== FUNÇÃO: Limpeza básica ========

def limpar_texto(texto):
    texto = re.sub(r"\s+", " ", texto)
    texto = re.sub(r"[^\w\s.,;:º§/-]", "", texto)
    return texto.strip()

# ======== FUNÇÃO: Treinar base ========

def treinar_base(links):
    textos = []
    for link in links:
        print(f"Lendo {link} ...")
        textos.append(extrair_texto_link(link))

    print("Gerando embeddings locais...")
    vectorizer = TfidfVectorizer(stop_words="portuguese")
    X = vectorizer.fit_transform(textos)

    base = {"links": links, "textos": textos, "vetorizador": vectorizer, "vetores": X}
    os.makedirs(os.path.dirname(DATA_PATH), exist_ok=True)
    with open(DATA_PATH, "wb") as f:
        pickle.dump(base, f)
    print("✅ Base de conhecimento treinada e salva!")

# ======== FUNÇÃO: Responder perguntas ========

def responder(pergunta):
    if not os.path.exists(DATA_PATH):
        return "A base ainda não foi treinada. Por favor, execute o aprendizado primeiro."

    with open(DATA_PATH, "rb") as f:
        base = pickle.load(f)

    vetor_pergunta = base["vetorizador"].transform([pergunta])
    similaridades = cosine_similarity(vetor_pergunta, base["vetores"]).flatten()
    idx = similaridades.argmax()

    contexto = base["textos"][idx][:1200]
    fonte = base["links"][idx]

    resposta = (
        f"🧠 Encontrei um trecho relevante em: {fonte}\n\n"
        f"{contexto[:1000]}...\n\n"
        f"🔎 (Resposta baseada na base interna da TrafficLaw AI)"
    )
    return resposta
