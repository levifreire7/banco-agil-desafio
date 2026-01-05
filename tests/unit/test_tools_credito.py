"""Testes unitários para tools de crédito."""
from unittest.mock import Mock, patch

from src.tools.credito import consultar_limite_credito, solicitar_aumento_limite


class TestConsultarLimiteCredito:
    """Testes para a tool consultar_limite_credito."""

    def test_consulta_limite_sucesso(self, mock_database, sample_cliente):
        """Testa consulta de limite bem-sucedida."""
        with patch('src.tools.credito.db', mock_database):
            result = consultar_limite_credito.invoke({"cpf": sample_cliente.cpf})

        assert result["sucesso"] is True
        assert result["limite_credito"] == sample_cliente.limite_credito
        assert result["score"] == sample_cliente.score
        assert "R$" in result["mensagem"]

    def test_consulta_limite_cliente_nao_encontrado(self, mock_database):
        """Testa consulta de limite para cliente inexistente."""
        with patch('src.tools.credito.db', mock_database):
            result = consultar_limite_credito.invoke({"cpf": "99999999999"})

        assert result["sucesso"] is False
        assert "não encontrado" in result["mensagem"]

    def test_consulta_limite_erro_database(self, mock_database, sample_cliente):
        """Testa tratamento de erro do database."""
        mock_database.obter_cliente = Mock(side_effect=Exception("Erro de BD"))

        with patch('src.tools.credito.db', mock_database):
            result = consultar_limite_credito.invoke({"cpf": sample_cliente.cpf})

        assert result["sucesso"] is False
        assert "Erro ao consultar limite" in result["mensagem"]


class TestSolicitarAumentoLimite:
    """Testes para a tool solicitar_aumento_limite."""

    def test_aumento_aprovado_score_alto(self, mock_database, sample_cliente_alto_score):
        """Testa aprovação de aumento para cliente com score alto."""
        with patch('src.tools.credito.db', mock_database):
            result = solicitar_aumento_limite.invoke({
                "cpf": sample_cliente_alto_score.cpf,
                "novo_limite": 20000.0
            })

        assert result["sucesso"] is True
        assert result["aprovado"] is True
        assert "aprovada" in result["mensagem"]
        assert "20000" in result["mensagem"]

    def test_aumento_rejeitado_score_baixo(self, mock_database, sample_cliente_baixo_score):
        """Testa rejeição de aumento para cliente com score baixo."""
        with patch('src.tools.credito.db', mock_database):
            result = solicitar_aumento_limite.invoke({
                "cpf": sample_cliente_baixo_score.cpf,
                "novo_limite": 10000.0
            })

        assert result["sucesso"] is True
        assert result["aprovado"] is False
        assert "rejeitada" in result["mensagem"]
        assert "score" in result["mensagem"].lower()

    def test_aumento_limite_menor_que_atual(self, mock_database, sample_cliente):
        """Testa solicitação de limite menor que o atual."""
        with patch('src.tools.credito.db', mock_database):
            result = solicitar_aumento_limite.invoke({
                "cpf": sample_cliente.cpf,
                "novo_limite": 3000.0
            })

        assert result["sucesso"] is False
        assert result["aprovado"] is False
        assert "maior que o atual" in result["mensagem"]

    def test_aumento_limite_igual_ao_atual(self, mock_database, sample_cliente):
        """Testa solicitação de limite igual ao atual."""
        with patch('src.tools.credito.db', mock_database):
            result = solicitar_aumento_limite.invoke({
                "cpf": sample_cliente.cpf,
                "novo_limite": sample_cliente.limite_credito
            })

        assert result["sucesso"] is False
        assert result["aprovado"] is False
        assert "maior que o atual" in result["mensagem"]

    def test_aumento_cliente_nao_encontrado(self, mock_database):
        """Testa solicitação de aumento para cliente inexistente."""
        with patch('src.tools.credito.db', mock_database):
            result = solicitar_aumento_limite.invoke({
                "cpf": "99999999999",
                "novo_limite": 10000.0
            })

        assert result["sucesso"] is False
        assert result["aprovado"] is False
        assert "não encontrado" in result["mensagem"]

    def test_aumento_registra_solicitacao(self, mock_database, sample_cliente):
        """Testa que a solicitação é registrada no database."""
        mock_database.criar_solicitacao_aumento = Mock(return_value="2024-01-01T10:00:00")

        with patch('src.tools.credito.db', mock_database):
            solicitar_aumento_limite.invoke({
                "cpf": sample_cliente.cpf,
                "novo_limite": 8000.0
            })

        mock_database.criar_solicitacao_aumento.assert_called_once()

    def test_aumento_atualiza_status_aprovado(self, mock_database, sample_cliente):
        """Testa que o status é atualizado para aprovado."""
        mock_database.atualizar_status_solicitacao = Mock()

        with patch('src.tools.credito.db', mock_database):
            result = solicitar_aumento_limite.invoke({
                "cpf": sample_cliente.cpf,
                "novo_limite": 8000.0
            })

        if result["aprovado"]:
            mock_database.atualizar_status_solicitacao.assert_called_once()
            call_args = mock_database.atualizar_status_solicitacao.call_args
            assert call_args[0][2] == 'aprovado'  # status

    def test_aumento_atualiza_status_rejeitado(self, mock_database, sample_cliente_baixo_score):
        """Testa que o status é atualizado para rejeitado."""
        mock_database.atualizar_status_solicitacao = Mock()

        with patch('src.tools.credito.db', mock_database):
            result = solicitar_aumento_limite.invoke({
                "cpf": sample_cliente_baixo_score.cpf,
                "novo_limite": 10000.0
            })

        assert result["aprovado"] is False
        mock_database.atualizar_status_solicitacao.assert_called_once()
        call_args = mock_database.atualizar_status_solicitacao.call_args
        assert call_args[0][2] == 'rejeitado'  # status

    def test_aumento_erro_database(self, mock_database, sample_cliente):
        """Testa tratamento de erro do database."""
        mock_database.obter_cliente = Mock(side_effect=Exception("Erro de BD"))

        with patch('src.tools.credito.db', mock_database):
            result = solicitar_aumento_limite.invoke({
                "cpf": sample_cliente.cpf,
                "novo_limite": 8000.0
            })

        assert result["sucesso"] is False
        assert result["aprovado"] is False
        assert "Erro ao processar" in result["mensagem"]

    def test_aumento_valida_score_limites(self, mock_database):
        """Testa validação de limites baseados em score."""
        with patch('src.tools.credito.db', mock_database):
            result = solicitar_aumento_limite.invoke({
                "cpf": "12345678901",
                "novo_limite": 9000.0
            })
            assert result["aprovado"] is True

            result = solicitar_aumento_limite.invoke({
                "cpf": "12345678901",
                "novo_limite": 15000.0
            })
            assert result["aprovado"] is False
