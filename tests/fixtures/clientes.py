"""Fixtures de dados de clientes para testes."""
from data_models.models import Cliente


CLIENTE_SCORE_BAIXO = Cliente(
    cpf="11122233344",
    nome="Pedro Costa",
    data_nascimento="1995-03-10",
    limite_credito=1000.0,
    score=350
)

CLIENTE_SCORE_MEDIO = Cliente(
    cpf="12345678901",
    nome="João Silva",
    data_nascimento="1990-05-15",
    limite_credito=5000.0,
    score=650
)

CLIENTE_SCORE_ALTO = Cliente(
    cpf="98765432100",
    nome="Maria Santos",
    data_nascimento="1985-10-20",
    limite_credito=15000.0,
    score=850
)

CLIENTE_SCORE_MUITO_ALTO = Cliente(
    cpf="55566677788",
    nome="Ana Paula",
    data_nascimento="1988-07-25",
    limite_credito=30000.0,
    score=920
)

TODOS_CLIENTES = [
    CLIENTE_SCORE_BAIXO,
    CLIENTE_SCORE_MEDIO,
    CLIENTE_SCORE_ALTO,
    CLIENTE_SCORE_MUITO_ALTO,
]
