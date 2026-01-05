"""Testes unitários para tools de câmbio."""
import responses
from unittest.mock import patch

from src.tools.cambio import consultar_cotacao_moeda


class TestConsultarCotacaoMoeda:
    """Testes para a tool consultar_cotacao_moeda."""

    @responses.activate
    def test_consulta_cotacao_usd_sucesso(self):
        """Testa consulta de cotação USD bem-sucedida."""
        responses.add(
            responses.GET,
            "https://api.exchangerate-api.com/v4/latest/USD",
            json={
                "base": "USD",
                "rates": {
                    "BRL": 5.25,
                    "EUR": 0.85
                }
            },
            status=200
        )

        result = consultar_cotacao_moeda.invoke({"moeda": "USD"})

        assert result["sucesso"] is True
        assert result["moeda"] == "USD"
        assert result["cotacao"] == 5.25
        assert "USD" in result["mensagem"]
        assert "5.25" in result["mensagem"]

    @responses.activate
    def test_consulta_cotacao_eur_sucesso(self):
        """Testa consulta de cotação EUR bem-sucedida."""
        responses.add(
            responses.GET,
            "https://api.exchangerate-api.com/v4/latest/EUR",
            json={
                "base": "EUR",
                "rates": {
                    "BRL": 6.10,
                    "USD": 1.18
                }
            },
            status=200
        )

        result = consultar_cotacao_moeda.invoke({"moeda": "EUR"})

        assert result["sucesso"] is True
        assert result["moeda"] == "EUR"
        assert result["cotacao"] == 6.10

    @responses.activate
    def test_consulta_cotacao_moeda_minuscula(self):
        """Testa que converte moeda para maiúscula."""
        responses.add(
            responses.GET,
            "https://api.exchangerate-api.com/v4/latest/USD",
            json={
                "base": "USD",
                "rates": {"BRL": 5.25}
            },
            status=200
        )

        result = consultar_cotacao_moeda.invoke({"moeda": "usd"})

        assert result["sucesso"] is True
        assert result["moeda"] == "USD"

    @responses.activate
    def test_consulta_cotacao_api_erro_404(self):
        """Testa tratamento de erro 404 da API."""
        responses.add(
            responses.GET,
            "https://api.exchangerate-api.com/v4/latest/XYZ",
            status=404
        )

        result = consultar_cotacao_moeda.invoke({"moeda": "XYZ"})

        assert result["sucesso"] is False
        assert "não foi possível obter a cotação" in result["mensagem"].lower()

    @responses.activate
    def test_consulta_cotacao_api_erro_500(self):
        """Testa tratamento de erro 500 da API."""
        responses.add(
            responses.GET,
            "https://api.exchangerate-api.com/v4/latest/USD",
            status=500
        )

        result = consultar_cotacao_moeda.invoke({"moeda": "USD"})

        assert result["sucesso"] is False

    @responses.activate
    def test_consulta_cotacao_timeout(self):
        """Testa tratamento de timeout."""
        responses.add(
            responses.GET,
            "https://api.exchangerate-api.com/v4/latest/USD",
            body=Exception("Timeout")
        )

        result = consultar_cotacao_moeda.invoke({"moeda": "USD"})

        assert result["sucesso"] is False
        assert "tente novamente" in result["mensagem"].lower()

    @responses.activate
    def test_consulta_cotacao_retry_mechanism(self):
        """Testa mecanismo de retry."""
        responses.add(
            responses.GET,
            "https://api.exchangerate-api.com/v4/latest/USD",
            status=500
        )
        responses.add(
            responses.GET,
            "https://api.exchangerate-api.com/v4/latest/USD",
            status=500
        )
        responses.add(
            responses.GET,
            "https://api.exchangerate-api.com/v4/latest/USD",
            json={
                "base": "USD",
                "rates": {"BRL": 5.25}
            },
            status=200
        )

        with patch('src.tools.cambio.time.sleep'):
            result = consultar_cotacao_moeda.invoke({"moeda": "USD"})

        assert result["sucesso"] is True
        assert result["cotacao"] == 5.25

    @responses.activate
    def test_consulta_cotacao_sem_brl_na_resposta(self):
        """Testa resposta sem BRL nas taxas."""
        responses.add(
            responses.GET,
            "https://api.exchangerate-api.com/v4/latest/USD",
            json={
                "base": "USD",
                "rates": {
                    "EUR": 0.85
                }
            },
            status=200
        )

        result = consultar_cotacao_moeda.invoke({"moeda": "USD"})

        assert result["sucesso"] is False

    @responses.activate
    def test_consulta_cotacao_resposta_invalida(self):
        """Testa resposta JSON inválida."""
        responses.add(
            responses.GET,
            "https://api.exchangerate-api.com/v4/latest/USD",
            json={"invalid": "response"},
            status=200
        )

        result = consultar_cotacao_moeda.invoke({"moeda": "USD"})

        assert result["sucesso"] is False

    @responses.activate
    def test_consulta_cotacao_default_usd(self):
        """Testa que usa USD como padrão."""
        responses.add(
            responses.GET,
            "https://api.exchangerate-api.com/v4/latest/USD",
            json={
                "base": "USD",
                "rates": {"BRL": 5.25}
            },
            status=200
        )

        result = consultar_cotacao_moeda.invoke({})

        assert result["sucesso"] is True
        assert result["moeda"] == "USD"
