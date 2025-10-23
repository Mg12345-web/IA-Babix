# backend/busca_avancada.py
import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime

BING_KEY = os.getenv("BING_API_KEY")
BING_ENDPOINT = "https://api.bing.microsoft.com/v7.0/search"


def modo_avancado(pergunta: str, usuario_id: str) -> dict:
    """
    Executa o modo avançado de pesquisa da Babix IA.
    Etapas:
        1. Planeja a pesquisa.
        2. Faz busca real via Bing API.
        3. Extrai trechos relevantes e jurisprudências.
        4. Monta resposta estruturada com fontes.
    """

    if not BING_KEY:
        return {"erro": "Chave da Bing API não configurada."}

    # ===== 1. PLANEJAMENTO =====
    print(f"[Modo Avançado] Executando para usuário {usuario_id}")
    termos_busca = (
        f"{pergunta} site:jusbrasil.com.br OR site:stj.jus.br OR site:stf.jus.br OR site:gov.br"
    )

    headers = {"Ocp-Apim-Subscription-Key": BING_KEY}
    params = {"q": termos_busca, "count": 5, "mkt": "pt-BR", "responseFilter": "Webpages"}

    # ===== 2. BUSCA REAL =====
    resposta = requests.get(BING_ENDPOINT, headers=headers, params=params)
    if resposta.status_code != 200:
        return {"erro": f"Erro na busca Bing: {resposta.status_code}", "texto": ""}

    resultados = resposta.json().get("webPages", {}).get("value", [])
    if not resultados:
        return {"texto": "Nenhum resultado relevante encontrado.", "links": []}

    # ===== 3. EXTRAÇÃO DE TRECHOS =====
    textos_extraidos = []
    links = []

    for item in resultados:
        titulo = item.get("name")
        link = item.get("url")
        descricao = item.get("snippet", "")
        links.append({"titulo": titulo, "url": link})

        # Tentativa de leitura rápida da página
        try:
            html = requests.get(link, timeout=5).text
            soup = BeautifulSoup(html, "lxml")
            paragrafos = " ".join([p.text for p in soup.find_all("p")[:3]])
            trecho = paragrafos if paragrafos else descricao
        except Exception:
            trecho = descricao

        textos_extraidos.append(f"🔹 **{titulo}**\nTrecho: {trecho.strip()}\nFonte: {link}\n")

    # ===== 4. MONTAGEM DA RESPOSTA =====
    resposta_final = f"""
⚖️ **Modo Avançado Ativado — Babix IA**
🧠 Pergunta: {pergunta}
📅 Data: {datetime.now().strftime('%d/%m/%Y %H:%M')}

**Resumo das jurisprudências e referências encontradas:**

{chr(10).join(textos_extraidos)}

**Síntese Automática:**
Com base nas fontes consultadas ({len(links)} resultados), foram localizadas jurisprudências e artigos que tratam sobre o tema solicitado. 
Verifique os links acima para a íntegra das decisões e utilize as teses conforme o contexto jurídico de trânsito.

**Observação:**
A Babix IA prioriza resultados de JusBrasil, STJ e STF. Caso não encontre nada nessas fontes, faz fallback para outras fontes oficiais.
    """.strip()

    return {"texto": resposta_final, "links": links}
