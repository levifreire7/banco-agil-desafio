"""Testes de integração para os agentes."""
from unittest.mock import patch
from langchain_core.messages import HumanMessage, AIMessage

from src.agents.triagem import AgenteTriagem
from src.agents.credito import AgenteCredito
from src.agents.cambio import AgenteCambio
from src.agents.entrevista import AgenteEntrevista


class TestAgenteTriagem:
    """Testes de integração para o agente de triagem."""

    def test_triagem_solicita_cpf_inicial(self, mock_llm, mock_llm_with_tools, sample_agent_state):
        """Testa que solicita CPF no primeiro contato."""
        agente = AgenteTriagem(mock_llm, mock_llm_with_tools)

        sample_agent_state["messages"] = [HumanMessage(content="Olá")]
        response_msg = AIMessage(content="Por favor, informe seu CPF.")
        mock_llm_with_tools.invoke.return_value = response_msg

        result = agente.process(sample_agent_state)

        assert result["current_agent"] == "triagem"
        assert len(result["messages"]) > 0
        mock_llm_with_tools.invoke.assert_called_once()

    def test_triagem_extrai_cpf_da_mensagem(self, mock_llm, mock_llm_with_tools, sample_agent_state):
        """Testa que extrai CPF da mensagem do usuário."""
        agente = AgenteTriagem(mock_llm, mock_llm_with_tools)

        sample_agent_state["messages"] = [HumanMessage(content="Meu CPF é 12345678901")]
        response_msg = AIMessage(content="Agora informe sua data de nascimento.")
        mock_llm_with_tools.invoke.return_value = response_msg

        result = agente.process(sample_agent_state)

        assert result["temp_cpf"] == "12345678901"

    def test_triagem_autentica_com_cpf_e_data(self, mock_llm, mock_llm_with_tools,
                                               sample_agent_state, mock_database, sample_cliente):
        """Testa autenticação completa com CPF e data."""
        agente = AgenteTriagem(mock_llm, mock_llm_with_tools)

        sample_agent_state["messages"] = [
            HumanMessage(content="12345678901"),
            HumanMessage(content="1990-05-15")
        ]
        sample_agent_state["temp_cpf"] = "12345678901"

        with patch('src.tools.autenticacao.db', mock_database):
            result = agente.process(sample_agent_state)

        assert result["authenticated"] is True
        assert result["cpf"] == sample_cliente.cpf
        assert result["nome_cliente"] == sample_cliente.nome

    def test_triagem_redireciona_para_credito(self, mock_llm, mock_llm_with_tools,
                                                authenticated_agent_state):
        """Testa redirecionamento para agente de crédito."""
        agente = AgenteTriagem(mock_llm, mock_llm_with_tools)

        authenticated_agent_state["messages"].append(
            HumanMessage(content="Quero aumentar meu limite")
        )

        response = AIMessage(content="REDIRECIONAR: credito")
        response.tool_calls = []
        mock_llm_with_tools.invoke.return_value = response

        result = agente.process(authenticated_agent_state)

        assert result.get("pending_redirect") == "credito"

    def test_triagem_redireciona_para_cambio(self, mock_llm, mock_llm_with_tools,
                                               authenticated_agent_state):
        """Testa redirecionamento para agente de câmbio."""
        agente = AgenteTriagem(mock_llm, mock_llm_with_tools)

        authenticated_agent_state["messages"].append(
            HumanMessage(content="Qual a cotação do dólar?")
        )

        response = AIMessage(content="REDIRECIONAR: cambio")
        response.tool_calls = []
        mock_llm_with_tools.invoke.return_value = response

        result = agente.process(authenticated_agent_state)

        assert result.get("pending_redirect") == "cambio"

    def test_triagem_falha_autenticacao_incrementa_tentativas(self, mock_llm, mock_llm_with_tools,
                                                                sample_agent_state, mock_database):
        """Testa que incrementa contador de tentativas em falha."""
        agente = AgenteTriagem(mock_llm, mock_llm_with_tools)

        sample_agent_state["messages"] = [HumanMessage(content="99999999999 2000-01-01")]
        sample_agent_state["temp_cpf"] = "99999999999"

        with patch('src.tools.autenticacao.db', mock_database):
            result = agente.process(sample_agent_state)

        assert result["authentication_attempts"] == 1
        assert result.get("authenticated", False) is False

    def test_triagem_encerra_apos_3_tentativas(self, mock_llm, mock_llm_with_tools, sample_agent_state,
                                                 mock_database):
        """Testa que encerra atendimento após 3 tentativas falhas."""
        agente = AgenteTriagem(mock_llm, mock_llm_with_tools)

        sample_agent_state["messages"] = [HumanMessage(content="99999999999 2000-01-01")]
        sample_agent_state["temp_cpf"] = "99999999999"
        sample_agent_state["authentication_attempts"] = 2

        with patch('src.tools.autenticacao.db', mock_database):
            result = agente.process(sample_agent_state)

        assert result["authentication_attempts"] == 3
        assert result["should_end"] is True


class TestAgenteCredito:
    """Testes de integração para o agente de crédito."""

    def test_credito_consulta_limite(self, mock_llm, mock_llm_with_tools,
                                      authenticated_agent_state, mock_database):
        """Testa consulta de limite de crédito."""
        agente = AgenteCredito(mock_llm, mock_llm_with_tools)

        authenticated_agent_state["messages"].append(
            HumanMessage(content="Qual meu limite?")
        )

        response = AIMessage(content="")
        response.tool_calls = [{
            "name": "consultar_limite_credito",
            "args": {"cpf": authenticated_agent_state["cpf"]},
            "id": "test_call"
        }]
        mock_llm_with_tools.invoke.return_value = response

        with patch('src.agents.credito.consultar_limite_credito') as mock_tool:
            mock_tool.invoke.return_value = {
                "sucesso": True,
                "limite_credito": 5000.0,
                "score": 650,
                "mensagem": "Seu limite de crédito atual é R$ 5000.00"
            }

            result = agente.process(authenticated_agent_state)

        assert result["current_agent"] == "credito"
        mock_tool.invoke.assert_called_once()

    def test_credito_solicita_aumento_aprovado(self, mock_llm, mock_llm_with_tools,
                                                 authenticated_agent_state):
        """Testa solicitação de aumento aprovada."""
        agente = AgenteCredito(mock_llm, mock_llm_with_tools)

        authenticated_agent_state["messages"].append(
            HumanMessage(content="Quero aumentar para 8000")
        )

        response = AIMessage(content="")
        response.tool_calls = [{
            "name": "solicitar_aumento_limite",
            "args": {"novo_limite": 8000.0},
            "id": "test_call"
        }]
        mock_llm_with_tools.invoke.return_value = response

        with patch('src.agents.credito.solicitar_aumento_limite') as mock_tool:
            mock_tool.invoke.return_value = {
                "sucesso": True,
                "aprovado": True,
                "mensagem": "Solicitação aprovada! Seu novo limite é R$ 8000.00"
            }

            result = agente.process(authenticated_agent_state)

        assert result["limite_credito"] == 8000.0
        assert "aprovada" in result["messages"][0].content.lower()

    def test_credito_solicita_aumento_rejeitado_oferece_entrevista(self, mock_llm, mock_llm_with_tools,
                                                                     authenticated_agent_state):
        """Testa que oferece entrevista quando aumento é rejeitado."""
        agente = AgenteCredito(mock_llm, mock_llm_with_tools)

        authenticated_agent_state["messages"].append(
            HumanMessage(content="Quero aumentar para 15000")
        )

        response = AIMessage(content="")
        response.tool_calls = [{
            "name": "solicitar_aumento_limite",
            "args": {"novo_limite": 15000.0},
            "id": "test_call"
        }]
        mock_llm_with_tools.invoke.return_value = response

        with patch('src.agents.credito.solicitar_aumento_limite') as mock_tool:
            mock_tool.invoke.return_value = {
                "sucesso": True,
                "aprovado": False,
                "mensagem": "Solicitação rejeitada. Seu score atual não permite este limite."
            }

            result = agente.process(authenticated_agent_state)

        assert "entrevista" in result["messages"][0].content.lower()

    def test_credito_redireciona_para_entrevista(self, mock_llm, mock_llm_with_tools,
                                                   authenticated_agent_state):
        """Testa redirecionamento para entrevista."""
        agente = AgenteCredito(mock_llm, mock_llm_with_tools)

        authenticated_agent_state["messages"].append(
            HumanMessage(content="Sim, quero fazer a entrevista")
        )

        response = AIMessage(content="REDIRECIONAR: entrevista")
        response.tool_calls = []
        mock_llm_with_tools.invoke.return_value = response

        result = agente.process(authenticated_agent_state)

        assert result.get("pending_redirect") == "entrevista"


class TestAgenteCambio:
    """Testes de integração para o agente de câmbio."""

    def test_cambio_consulta_cotacao_usd(self, mock_llm, mock_llm_with_tools,
                                          authenticated_agent_state):
        """Testa consulta de cotação USD."""
        agente = AgenteCambio(mock_llm, mock_llm_with_tools)

        authenticated_agent_state["messages"].append(
            HumanMessage(content="Qual a cotação do dólar?")
        )

        response = AIMessage(content="")
        response.tool_calls = [{
            "name": "consultar_cotacao_moeda",
            "args": {"moeda": "USD"},
            "id": "test_call"
        }]
        mock_llm_with_tools.invoke.return_value = response

        with patch('src.agents.cambio.consultar_cotacao_moeda') as mock_tool:
            mock_tool.invoke.return_value = {
                "sucesso": True,
                "moeda": "USD",
                "cotacao": 5.25,
                "mensagem": "1 USD = R$ 5.25"
            }

            result = agente.process(authenticated_agent_state)

        assert result["current_agent"] == "cambio"
        mock_tool.invoke.assert_called_once()

    def test_cambio_consulta_cotacao_eur(self, mock_llm, mock_llm_with_tools,
                                          authenticated_agent_state):
        """Testa consulta de cotação EUR."""
        agente = AgenteCambio(mock_llm, mock_llm_with_tools)

        authenticated_agent_state["messages"].append(
            HumanMessage(content="Quanto está o euro?")
        )

        response = AIMessage(content="")
        response.tool_calls = [{
            "name": "consultar_cotacao_moeda",
            "args": {"moeda": "EUR"},
            "id": "test_call"
        }]
        mock_llm_with_tools.invoke.return_value = response

        with patch('src.agents.cambio.consultar_cotacao_moeda') as mock_tool:
            mock_tool.invoke.return_value = {
                "sucesso": True,
                "moeda": "EUR",
                "cotacao": 6.10,
                "mensagem": "1 EUR = R$ 6.10"
            }

            result = agente.process(authenticated_agent_state)

        assert result["current_agent"] == "cambio"


class TestAgenteEntrevista:
    """Testes de integração para o agente de entrevista."""

    def test_entrevista_inicia_perguntas(self, mock_llm, mock_llm_with_tools,
                                          authenticated_agent_state):
        """Testa início do questionário de entrevista."""
        agente = AgenteEntrevista(mock_llm, mock_llm_with_tools)

        authenticated_agent_state["current_agent"] = "entrevista"
        authenticated_agent_state["messages"].append(
            HumanMessage(content="Sim, quero fazer a entrevista")
        )

        response = AIMessage(content="Vou fazer algumas perguntas. Qual sua renda mensal?")
        response.tool_calls = []
        mock_llm_with_tools.invoke.return_value = response

        result = agente.process(authenticated_agent_state)

        assert result["current_agent"] == "entrevista"
        assert len(result["messages"]) > 0

    def test_entrevista_calcula_novo_score(self, mock_llm, mock_llm_with_tools,
                                            authenticated_agent_state):
        """Testa cálculo de novo score após entrevista."""
        agente = AgenteEntrevista(mock_llm, mock_llm_with_tools)

        authenticated_agent_state["current_agent"] = "entrevista"
        authenticated_agent_state["interview_data"] = {
            "renda_mensal": 5000.0,
            "tempo_emprego": 3
        }

        response = AIMessage(content="")
        response.tool_calls = [{
            "name": "calcular_novo_score",
            "args": {
                "cpf": authenticated_agent_state["cpf"],
                "interview_data": authenticated_agent_state["interview_data"]
            },
            "id": "test_call"
        }]
        mock_llm_with_tools.invoke.return_value = response

        with patch('src.agents.entrevista.calcular_novo_score') as mock_tool:
            mock_tool.invoke.return_value = {
                "sucesso": True,
                "novo_score": 720,
                "mensagem": "Seu novo score é 720"
            }

            result = agente.process(authenticated_agent_state)

        mock_tool.invoke.assert_called_once()

    def test_entrevista_redireciona_para_credito(self, mock_llm, mock_llm_with_tools,
                                                   authenticated_agent_state):
        """Testa redirecionamento para crédito após entrevista."""
        agente = AgenteEntrevista(mock_llm, mock_llm_with_tools)

        authenticated_agent_state["current_agent"] = "entrevista"
        authenticated_agent_state["messages"].append(
            HumanMessage(content="Sim, quero solicitar aumento agora")
        )

        response = AIMessage(content="REDIRECIONAR: credito")
        response.tool_calls = []
        mock_llm_with_tools.invoke.return_value = response

        result = agente.process(authenticated_agent_state)

        assert result.get("pending_redirect") == "credito"
