from typing import Any, Dict

from langchain_core.tools import tool

from src.data_models.database import Database

db = Database()


@tool
def autenticar_cliente(cpf: str, data_nascimento: str) -> Dict[str, Any]:
    """
    Autentica um cliente verificando CPF e data de nascimento.

    Args:
        cpf: CPF do cliente (apenas números, 11 dígitos)
        data_nascimento: Data de nascimento no formato YYYY-MM-DD

    Returns:
        Dict com sucesso (bool), mensagem (str) e dados do cliente se autenticado
    """
    try:
        cliente = db.autenticar_cliente(cpf, data_nascimento)
        if cliente:
            return {
                "sucesso": True,
                "mensagem": f"Cliente autenticado com sucesso. Bem-vindo(a), {cliente.nome}!",
                "cliente": {
                    "cpf": cliente.cpf,
                    "nome": cliente.nome,
                    "limite_credito": cliente.limite_credito,
                    "score": cliente.score
                }
            }
        else:
            return {
                "sucesso": False,
                "mensagem": "CPF ou data de nascimento incorretos.",
                "cliente": None
            }
    except Exception as e:
        return {
            "sucesso": False,
            "mensagem": f"Erro ao autenticar: {str(e)}",
            "cliente": None
        }
