from typing import Dict, Any

from langchain_core.tools import tool

from src.data_models.database import Database

db = Database()


@tool
def calcular_novo_score(cpf: str, renda_mensal: float, tipo_emprego: str,
                       despesas_fixas: float, num_dependentes: int,
                       tem_dividas: bool) -> Dict[str, Any]:
    """
    Calcula novo score de crédito baseado em dados financeiros do cliente.

    Args:
        cpf: CPF do cliente
        renda_mensal: Renda mensal do cliente
        tipo_emprego: 'formal', 'autonomo' ou 'desempregado'
        despesas_fixas: Despesas fixas mensais
        num_dependentes: Número de dependentes (0, 1, 2, ou 3+)
        tem_dividas: Se possui dívidas ativas (True/False)

    Returns:
        Dict com novo_score (int) e mensagem
    """
    try:
        peso_renda = 30
        peso_emprego = {
            "formal": 300,
            "autonomo": 200,
            "desempregado": 0
        }
        peso_dependentes = {
            0: 100,
            1: 80,
            2: 60,
        }
        peso_dividas = {
            True: -100,
            False: 100
        }

        if num_dependentes >= 3:
            peso_dep = 30
        else:
            peso_dep = peso_dependentes[num_dependentes]

        tipo_emprego = tipo_emprego.lower()
        if tipo_emprego not in peso_emprego:
            tipo_emprego = "desempregado"

        score = (
            (renda_mensal / (despesas_fixas + 1)) * peso_renda +
            peso_emprego[tipo_emprego] +
            peso_dep +
            peso_dividas[tem_dividas]
        )

        score = max(0, min(1000, int(score)))

        db.atualizar_score(cpf, score)

        return {
            "sucesso": True,
            "novo_score": score,
            "mensagem": f"Score atualizado com sucesso! Seu novo score é {score}."
        }
    except Exception as e:
        return {
            "sucesso": False,
            "mensagem": f"Erro ao calcular score: {str(e)}"
        }
