from src.tools.atendimento import encerrar_atendimento
from src.tools.autenticacao import autenticar_cliente
from src.tools.cambio import consultar_cotacao_moeda
from src.tools.credito import consultar_limite_credito, solicitar_aumento_limite
from src.tools.score import calcular_novo_score

tools_list = [
    autenticar_cliente,
    consultar_limite_credito,
    solicitar_aumento_limite,
    calcular_novo_score,
    consultar_cotacao_moeda,
    encerrar_atendimento
]

__all__ = [
    'autenticar_cliente',
    'consultar_limite_credito',
    'solicitar_aumento_limite',
    'calcular_novo_score',
    'consultar_cotacao_moeda',
    'encerrar_atendimento',
    'tools_list'
]
