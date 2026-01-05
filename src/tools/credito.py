from typing import Dict, Any

from langchain_core.tools import tool

from src.data_models.database import Database

db = Database()


@tool
def consultar_limite_credito(cpf: str) -> Dict[str, Any]:
    """
    Consulta o limite de crédito disponível do cliente.

    Args:
        cpf: CPF do cliente

    Returns:
        Dict com limite_credito (float) e score (int)
    """
    try:
        cliente = db.obter_cliente(cpf)
        if cliente:
            return {
                "sucesso": True,
                "limite_credito": cliente.limite_credito,
                "score": cliente.score,
                "mensagem": f"Seu limite de crédito atual é R$ {cliente.limite_credito:.2f}"
            }
        else:
            return {
                "sucesso": False,
                "mensagem": "Cliente não encontrado"
            }
    except Exception as e:
        return {
            "sucesso": False,
            "mensagem": f"Erro ao consultar limite: {str(e)}"
        }


@tool
def solicitar_aumento_limite(cpf: str, novo_limite: float) -> Dict[str, Any]:
    """
    Solicita aumento de limite de crédito seguindo o fluxo:
    1. Registra solicitação com status 'pendente'
    2. Verifica se é permitido pelo score
    3. Atualiza status para 'aprovado' ou 'rejeitado'

    Args:
        cpf: CPF do cliente
        novo_limite: Novo limite de crédito solicitado

    Returns:
        Dict com sucesso (bool), aprovado (bool) e mensagem
    """
    try:
        cliente = db.obter_cliente(cpf)
        if not cliente:
            return {
                "sucesso": False,
                "aprovado": False,
                "mensagem": "Cliente não encontrado"
            }

        if novo_limite <= cliente.limite_credito:
            return {
                "sucesso": False,
                "aprovado": False,
                "mensagem": f"O novo limite deve ser maior que o atual (R$ {cliente.limite_credito:.2f})"
            }

        # 1. Registra a solicitação com status 'pendente'
        data_hora = db.criar_solicitacao_aumento(cpf, cliente.limite_credito, novo_limite)

        # 2. Verifica se o limite é permitido para o score do cliente
        permitido = db.verificar_limite_permitido(cliente.score, novo_limite)

        # 3. Atualiza o status da solicitação baseado na verificação
        if permitido:
            db.atualizar_status_solicitacao(
                cpf,
                data_hora,
                'aprovado',
                atualizar_limite=True,
                novo_limite=novo_limite
            )
            return {
                "sucesso": True,
                "aprovado": True,
                "mensagem": f"Solicitação aprovada! Seu novo limite é R$ {novo_limite:.2f}"
            }
        else:
            db.atualizar_status_solicitacao(cpf, data_hora, 'rejeitado')
            return {
                "sucesso": True,
                "aprovado": False,
                "mensagem": f"Solicitação rejeitada. Seu score atual ({cliente.score}) não permite este limite."
            }
    except Exception as e:
        return {
            "sucesso": False,
            "aprovado": False,
            "mensagem": f"Erro ao processar solicitação: {str(e)}"
        }
