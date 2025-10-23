# backend/memoria.py
from datetime import datetime

def salvar_memoria(supabase, usuario_id: str, pergunta: str, resposta: str):
    """
    Salva uma nova interação (pergunta + resposta) na tabela 'memorias' do Supabase.
    """
    try:
        supabase.table("memorias").insert({
            "usuario_id": usuario_id,
            "pergunta": pergunta,
            "resposta": resposta,
            "criado_em": datetime.now().isoformat()
        }).execute()
    except Exception as e:
        print("Erro ao salvar memória:", e)


def buscar_memoria(supabase, usuario_id: str, pergunta: str) -> str | None:
    """
    Busca respostas anteriores semelhantes à pergunta atual.
    Retorna a resposta mais recente se encontrar algo parecido.
    """
    try:
        result = supabase.table("memorias") \
            .select("*") \
            .eq("usuario_id", usuario_id) \
            .ilike("pergunta", f"%{pergunta[:20]}%") \
            .order("criado_em", desc=True) \
            .limit(1) \
            .execute()

        if result.data:
            return result.data[0]["resposta"]
        return None
    except Exception as e:
        print("Erro ao buscar memória:", e)
        return None
