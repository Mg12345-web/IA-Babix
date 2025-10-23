# backend/usuarios.py
from datetime import datetime
from supabase import Client
import uuid


def registrar_usuario(supabase: Client, dados: dict) -> dict:
    """
    Registra um novo usuário na tabela 'usuarios' do Supabase.
    Espera receber: { "nome": ..., "email": ..., "senha": ..., "plano": ... }
    """

    try:
        nome = dados.get("nome")
        email = dados.get("email")
        senha = dados.get("senha")
        plano = dados.get("plano", "basico")

        # Evitar duplicidade de e-mails
        existente = supabase.table("usuarios").select("*").eq("email", email).execute()
        if existente.data:
            return {"erro": "E-mail já cadastrado."}

        usuario_id = str(uuid.uuid4())
        supabase.table("usuarios").insert({
            "id": usuario_id,
            "nome": nome,
            "email": email,
            "senha": senha,  # Em produção, ideal usar hash
            "plano": plano,
            "criado_em": datetime.now().isoformat()
        }).execute()

        return {"status": "ok", "mensagem": "Usuário registrado com sucesso!", "usuario_id": usuario_id}

    except Exception as e:
        return {"erro": str(e)}


def autenticar_usuario(supabase: Client, email: str, senha: str) -> dict | None:
    """
    Autentica um usuário pelo e-mail e senha.
    Retorna o dicionário do usuário se válido, ou None.
    """

    try:
        result = supabase.table("usuarios") \
            .select("*") \
            .eq("email", email) \
            .eq("senha", senha) \
            .limit(1) \
            .execute()

        if not result.data:
            return None

        usuario = result.data[0]
        usuario.pop("senha", None)  # segurança
        return usuario
    except Exception as e:
        print("Erro na autenticação:", e)
        return None


def verificar_limite_plano(plano: str, contador_uso: int) -> bool:
    """
    Define limites de uso para cada plano.
    Retorna True se o usuário ainda pode usar o modo avançado.
    """

    limites = {
        "basico": 0,       # sem acesso ao modo avançado
        "medio": 30,       # 30 buscas avançadas/mês
        "ilimitado": 9999  # sem limite
    }

    limite = limites.get(plano, 0)
    return contador_uso < limite


def registrar_uso(supabase: Client, usuario_id: str, tipo: str):
    """
    Registra cada uso (chat, modo avançado, documento, etc.) na tabela 'estatisticas'.
    """

    try:
        supabase.table("estatisticas").insert({
            "usuario_id": usuario_id,
            "tipo_uso": tipo,
            "data_hora": datetime.now().isoformat()
        }).execute()
    except Exception as e:
        print("Erro ao registrar uso:", e)
