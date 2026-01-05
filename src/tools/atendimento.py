from typing import Any, Dict

from langchain_core.tools import tool


@tool
def encerrar_atendimento() -> Dict[str, Any]:
    """
    Encerra o atendimento ao cliente.

    Returns:
        Dict indicando que o atendimento foi encerrado
    """
    return {
        "sucesso": True,
        "encerrado": True,
        "mensagem": "Atendimento encerrado. Obrigado por utilizar o Banco Ágil!"
    }
