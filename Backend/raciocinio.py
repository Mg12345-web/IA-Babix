# backend/raciocinio.py
import re
from datetime import datetime

def gerar_resposta(mensagem: str) -> str:
    """
    Analisa a mensagem do usuário, identifica padrões (artigos do CTB, infrações, nulidades)
    e gera uma resposta jurídica estruturada.
    """

    texto = mensagem.lower().strip()
    resposta = ""

    # ===== 1. Identificar artigos do CTB =====
    padrao_artigo = re.findall(r"(art\.?\s*\d+)", texto)
    artigos = ", ".join(padrao_artigo) if padrao_artigo else "não especificado"

    # ===== 2. Reconhecimento de temas comuns =====
    if "lei seca" in texto or "álcool" in texto:
        resposta = (
            "Parece que você está tratando de uma autuação relacionada à Lei Seca. "
            "Lembre-se de verificar se o agente estava devidamente credenciado, "
            "se o etilômetro possuía aferição do Inmetro válida e se o termo de recusa foi oferecido. "
            "Caso algum desses elementos falte, há vício formal no auto de infração."
        )
    elif "recusa" in texto:
        resposta = (
            "Em casos de recusa ao teste do etilômetro, conforme o art. 165-A do CTB, "
            "é essencial verificar se houve oferta formal do teste e se o condutor foi informado "
            "das consequências legais. A ausência dessa formalidade torna o auto nulo."
        )
    elif "suspensão" in texto or "cassação" in texto:
        resposta = (
            "Quando há suspensão ou cassação da CNH, é necessário verificar se o processo administrativo "
            "respeitou o contraditório e a ampla defesa, conforme o art. 5º, LV, da Constituição Federal. "
            "O descumprimento desses princípios invalida o ato punitivo."
        )
    elif "erro" in texto or "placa" in texto or "veículo" in texto:
        resposta = (
            "Se houver erro na placa, no veículo ou no campo de observações do AIT, "
            "temos vício formal insanável (art. 280 CTB). Isso compromete a validade da autuação."
        )
    else:
        resposta = (
            "Com base nas informações fornecidas, recomenda-se verificar se o Auto de Infração "
            "atende aos requisitos do art. 280 do CTB e das Resoluções do CONTRAN correspondentes. "
            "Erros formais ou falta de elementos obrigatórios podem ensejar nulidade."
        )

    # ===== 3. Montar resposta estruturada =====
    modelo = f"""
🧾 **Análise Jurídica Automatizada — Babix IA**
📅 Data: {datetime.now().strftime('%d/%m/%Y %H:%M')}

**Artigos mencionados:** {artigos}

**Análise:**  
{resposta}

**Sugestão:**  
Consulte também a Resolução 432/2013 (CONTRAN) e verifique se o Auto contém todas as informações exigidas.
    """.strip()

    return modelo
