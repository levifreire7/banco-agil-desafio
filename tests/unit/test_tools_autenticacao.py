"""Testes unitários para tools de autenticação."""
from unittest.mock import Mock, patch

from src.tools.autenticacao import autenticar_cliente


class TestAutenticarCliente:
    """Testes para a tool autenticar_cliente."""

    def test_autenticacao_sucesso(self, mock_database, sample_cliente):
        """Testa autenticação bem-sucedida."""
        with patch('src.tools.autenticacao.db', mock_database):
            result = autenticar_cliente.invoke({
                "cpf": sample_cliente.cpf,
                "data_nascimento": sample_cliente.data_nascimento
            })

        assert result["sucesso"] is True
        assert "Bem-vindo(a)" in result["mensagem"]
        assert result["cliente"]["cpf"] == sample_cliente.cpf
        assert result["cliente"]["nome"] == sample_cliente.nome
        assert result["cliente"]["limite_credito"] == sample_cliente.limite_credito
        assert result["cliente"]["score"] == sample_cliente.score

    def test_autenticacao_cpf_incorreto(self, mock_database):
        """Testa autenticação com CPF incorreto."""
        with patch('src.tools.autenticacao.db', mock_database):
            result = autenticar_cliente.invoke({
                "cpf": "99999999999",
                "data_nascimento": "1990-05-15"
            })

        assert result["sucesso"] is False
        assert "incorretos" in result["mensagem"]
        assert result["cliente"] is None

    def test_autenticacao_data_incorreta(self, mock_database, sample_cliente):
        """Testa autenticação com data de nascimento incorreta."""
        with patch('src.tools.autenticacao.db', mock_database):
            result = autenticar_cliente.invoke({
                "cpf": sample_cliente.cpf,
                "data_nascimento": "1990-12-31"
            })

        assert result["sucesso"] is False
        assert "incorretos" in result["mensagem"]
        assert result["cliente"] is None

    def test_autenticacao_erro_database(self, mock_database, sample_cliente):
        """Testa tratamento de erro do database."""
        mock_database.autenticar_cliente = Mock(side_effect=Exception("Erro de BD"))

        with patch('src.tools.autenticacao.db', mock_database):
            result = autenticar_cliente.invoke({
                "cpf": sample_cliente.cpf,
                "data_nascimento": sample_cliente.data_nascimento
            })

        assert result["sucesso"] is False
        assert "Erro ao autenticar" in result["mensagem"]
        assert result["cliente"] is None

    def test_autenticacao_cpf_formato_valido(self, mock_database, sample_cliente):
        """Testa que aceita CPF com 11 dígitos."""
        with patch('src.tools.autenticacao.db', mock_database):
            result = autenticar_cliente.invoke({
                "cpf": sample_cliente.cpf,
                "data_nascimento": sample_cliente.data_nascimento
            })

        assert result["sucesso"] is True
        assert len(sample_cliente.cpf) == 11

    def test_autenticacao_retorna_todos_campos_cliente(self, mock_database, sample_cliente):
        """Testa que retorna todos os campos necessários do cliente."""
        with patch('src.tools.autenticacao.db', mock_database):
            result = autenticar_cliente.invoke({
                "cpf": sample_cliente.cpf,
                "data_nascimento": sample_cliente.data_nascimento
            })

        assert result["sucesso"] is True
        cliente = result["cliente"]
        assert "cpf" in cliente
        assert "nome" in cliente
        assert "limite_credito" in cliente
        assert "score" in cliente
