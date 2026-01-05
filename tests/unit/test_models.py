"""Testes unitários para modelos de dados."""
import pytest

from src.data_models.models import Cliente, SolicitacaoAumento, ScoreLimite


class TestCliente:
    """Testes para o modelo Cliente."""

    def test_criar_cliente_valido(self):
        """Testa criação de cliente com dados válidos."""
        cliente = Cliente(
            cpf="12345678901",
            nome="João Silva",
            data_nascimento="1990-05-15",
            limite_credito=5000.0,
            score=650
        )

        assert cliente.cpf == "12345678901"
        assert cliente.nome == "João Silva"
        assert cliente.data_nascimento == "1990-05-15"
        assert cliente.limite_credito == 5000.0
        assert cliente.score == 650

    def test_cliente_campos_obrigatorios(self):
        """Testa que todos os campos são obrigatórios."""
        with pytest.raises(TypeError):
            Cliente(cpf="12345678901")

    def test_cliente_tipos_corretos(self):
        """Testa que os tipos de dados estão corretos."""
        cliente = Cliente(
            cpf="12345678901",
            nome="João Silva",
            data_nascimento="1990-05-15",
            limite_credito=5000.0,
            score=650
        )

        assert isinstance(cliente.cpf, str)
        assert isinstance(cliente.nome, str)
        assert isinstance(cliente.data_nascimento, str)
        assert isinstance(cliente.limite_credito, float)
        assert isinstance(cliente.score, int)

    def test_cliente_limite_negativo(self):
        """Testa criação de cliente com limite negativo."""
        cliente = Cliente(
            cpf="12345678901",
            nome="João Silva",
            data_nascimento="1990-05-15",
            limite_credito=-1000.0,
            score=650
        )
        assert cliente.limite_credito == -1000.0

    def test_cliente_score_fora_range(self):
        """Testa criação de cliente com score fora do range."""
        cliente = Cliente(
            cpf="12345678901",
            nome="João Silva",
            data_nascimento="1990-05-15",
            limite_credito=5000.0,
            score=1500
        )
        assert cliente.score == 1500


class TestSolicitacaoAumento:
    """Testes para o modelo SolicitacaoAumento."""

    def test_criar_solicitacao_valida(self):
        """Testa criação de solicitação com dados válidos."""
        solicitacao = SolicitacaoAumento(
            cpf_cliente="12345678901",
            data_hora_solicitacao="2024-01-01T10:00:00",
            limite_atual=5000.0,
            novo_limite_solicitado=8000.0,
            status_pedido="pendente"
        )

        assert solicitacao.cpf_cliente == "12345678901"
        assert solicitacao.data_hora_solicitacao == "2024-01-01T10:00:00"
        assert solicitacao.limite_atual == 5000.0
        assert solicitacao.novo_limite_solicitado == 8000.0
        assert solicitacao.status_pedido == "pendente"

    def test_solicitacao_status_aprovado(self):
        """Testa solicitação com status aprovado."""
        solicitacao = SolicitacaoAumento(
            cpf_cliente="12345678901",
            data_hora_solicitacao="2024-01-01T10:00:00",
            limite_atual=5000.0,
            novo_limite_solicitado=8000.0,
            status_pedido="aprovado"
        )

        assert solicitacao.status_pedido == "aprovado"

    def test_solicitacao_status_rejeitado(self):
        """Testa solicitação com status rejeitado."""
        solicitacao = SolicitacaoAumento(
            cpf_cliente="12345678901",
            data_hora_solicitacao="2024-01-01T10:00:00",
            limite_atual=5000.0,
            novo_limite_solicitado=8000.0,
            status_pedido="rejeitado"
        )

        assert solicitacao.status_pedido == "rejeitado"


class TestScoreLimite:
    """Testes para o modelo ScoreLimite."""

    def test_criar_score_limite_valido(self):
        """Testa criação de score limite com dados válidos."""
        score_limite = ScoreLimite(
            score_minimo=500,
            score_maximo=699,
            limite_maximo=10000.0
        )

        assert score_limite.score_minimo == 500
        assert score_limite.score_maximo == 699
        assert score_limite.limite_maximo == 10000.0

    def test_score_limite_range_baixo(self):
        """Testa range de score baixo."""
        score_limite = ScoreLimite(
            score_minimo=0,
            score_maximo=499,
            limite_maximo=5000.0
        )

        assert score_limite.score_minimo == 0
        assert score_limite.limite_maximo == 5000.0

    def test_score_limite_range_alto(self):
        """Testa range de score alto."""
        score_limite = ScoreLimite(
            score_minimo=850,
            score_maximo=1000,
            limite_maximo=50000.0
        )

        assert score_limite.score_minimo == 850
        assert score_limite.limite_maximo == 50000.0

    def test_score_limite_tipos_corretos(self):
        """Testa que os tipos de dados estão corretos."""
        score_limite = ScoreLimite(
            score_minimo=500,
            score_maximo=699,
            limite_maximo=10000.0
        )

        assert isinstance(score_limite.score_minimo, int)
        assert isinstance(score_limite.score_maximo, int)
        assert isinstance(score_limite.limite_maximo, float)
