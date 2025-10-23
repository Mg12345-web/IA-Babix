# backend/jurisprudencia.py
import requests
from bs4 import BeautifulSoup

def extrair_jurisprudencias(links: list) -> list:
    """
    Acessa os links retornados pelo modo avançado e extrai ementas ou resumos
    de decisões jurídicas do JusBrasil, STJ e STF.
    Retorna uma lista de dicionários com 'titulo', 'ementa' e 'fonte'.
    """
    jurisprudencias = []

    for item in links:
        url = item.get("url")
        titulo = item.get("titulo", "Sem título")

        try:
            html = requests.get(url, timeout=8).text
            soup = BeautifulSoup(html, "lxml")

            # ===== Extração por domínio =====
            if "jusbrasil" in url:
                ementa = ""
                blocos = soup.find_all("p")
                for p in blocos[:5]:
                    texto = p.text.strip()
                    if "EMENTA" in texto.upper() or len(texto) > 120:
                        ementa += texto + " "
                if not ementa:
                    ementa = "Ementa não localizada. Acesse o link completo para leitura integral."

            elif "stj.jus.br" in url or "stf.jus.br" in url:
                ementa_tag = soup.find("div", class_="ementa")
                if ementa_tag:
                    ementa = ementa_tag.text.strip()
                else:
                    ementa = "Decisão localizada, mas ementa não pôde ser extraída automaticamente."

            else:
                paragrafos = soup.find_all("p")
                ementa = " ".join(p.text for p in paragrafos[:4])[:600]

            jurisprudencias.append({
                "titulo": titulo,
                "ementa": ementa.strip(),
                "fonte": url
            })

        except Exception as e:
            print("Erro ao extrair jurisprudência:", e)
            jurisprudencias.append({
                "titulo": titulo,
                "ementa": "Erro ao acessar o link.",
                "fonte": url
            })

    return jurisprudencias


def montar_resumo(jurisprudencias: list) -> str:
    """
    Gera um resumo textual de todas as jurisprudências extraídas.
    """
    if not jurisprudencias:
        return "Nenhuma jurisprudência relevante foi encontrada."

    texto_final = "📚 **Resumo das Jurisprudências Localizadas:**\n\n"
    for i, j in enumerate(jurisprudencias, 1):
        texto_final += f"**{i}. {j['titulo']}**\n"
        texto_final += f"{j['ementa']}\n"
        texto_final += f"🔗 Fonte: {j['fonte']}\n\n"

    texto_final += "\n🧠 *Análise automatizada pela Babix IA — cruzamento com JusBrasil, STJ e STF.*"
    return texto_final
