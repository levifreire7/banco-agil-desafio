from dataclasses import dataclass


@dataclass
class Cliente:
    """Modelo de dados para Cliente."""
    cpf: str
    nome: str
    data_nascimento: str
    limite_credito: float
    score: int


@dataclass
class SolicitacaoAumento:
    """Modelo de dados para Solicitação de Aumento de Limite."""
    cpf_cliente: str
    data_hora_solicitacao: str
    limite_atual: float
    novo_limite_solicitado: float
    status_pedido: str


@dataclass
class ScoreLimite:
    """Modelo de dados para Score e Limite permitido."""
    score_minimo: int
    score_maximo: int
    limite_maximo: float
