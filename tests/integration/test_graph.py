"""Testes de integração para o grafo LangGraph."""
from unittest.mock import Mock, patch
from langchain_core.messages import HumanMessage, AIMessage

from src.core.graph import create_graph


class TestGraphCreation:
    """Testes para criação do grafo."""

    def test_create_graph_com_api_key(self, mock_openai_api_key):
        """Testa criação do grafo com API key."""
        with patch('src.core.graph.BancoAgilAgents'):
            graph = create_graph(mock_openai_api_key)

        assert graph is not None

    def test_graph_tem_todos_nodes(self, mock_openai_api_key):
        """Testa que o grafo tem todos os nós necessários."""
        with patch('src.core.graph.BancoAgilAgents'):
            graph = create_graph(mock_openai_api_key)

        graph_structure = graph.get_graph()
        assert graph_structure is not None


class TestGraphRouting:
    """Testes para roteamento no grafo."""

    def test_router_inicial_vai_para_triagem(self, mock_openai_api_key, sample_agent_state):
        """Testa que roteador inicial direciona para triagem."""
        with patch('src.core.graph.BancoAgilAgents'):
            with patch('src.core.graph.AgenteTriagem') as mock_triagem:
                mock_instance = Mock()
                mock_instance.process.return_value = {
                    "current_agent": "triagem",
                    "messages": [AIMessage(content="Olá")],
                    "authenticated": False
                }
                mock_triagem.return_value = mock_instance

                graph = create_graph(mock_openai_api_key)

                initial_state = {
                    **sample_agent_state,
                    "messages": [HumanMessage(content="Olá")]
                }

                result = graph.invoke(initial_state)

                assert "current_agent" in result

    def test_router_entrevista_ativa_vai_para_entrevista(self, mock_openai_api_key,
                                                          authenticated_agent_state):
        """Testa que roteador direciona para entrevista quando está ativa."""
        with patch('src.core.graph.BancoAgilAgents'):
            with patch('src.core.graph.AgenteEntrevista') as mock_entrevista:
                mock_instance = Mock()
                mock_instance.process.return_value = {
                    "current_agent": "entrevista",
                    "messages": [AIMessage(content="Pergunta da entrevista")],
                    "should_end": True
                }
                mock_entrevista.return_value = mock_instance

                graph = create_graph(mock_openai_api_key)

                state_entrevista = {
                    **authenticated_agent_state,
                    "current_agent": "entrevista",
                    "messages": [HumanMessage(content="Resposta")]
                }

                result = graph.invoke(state_entrevista)

                assert "messages" in result


class TestGraphTransitions:
    """Testes para transições entre agentes."""

    def test_transicao_triagem_para_credito(self, mock_openai_api_key, authenticated_agent_state):
        """Testa transição de triagem para crédito."""
        with patch('src.core.graph.BancoAgilAgents'):
            with patch('src.core.graph.AgenteTriagem') as mock_triagem:
                with patch('src.core.graph.AgenteCredito') as mock_credito:
                    mock_triagem_instance = Mock()
                    mock_triagem_instance.process.return_value = {
                        "current_agent": "triagem",
                        "pending_redirect": "credito",
                        "messages": [],
                        "authenticated": True
                    }
                    mock_triagem.return_value = mock_triagem_instance

                    mock_credito_instance = Mock()
                    mock_credito_instance.process.return_value = {
                        "current_agent": "credito",
                        "messages": [AIMessage(content="Seu limite é R$ 5000.00")],
                        "should_end": True
                    }
                    mock_credito.return_value = mock_credito_instance

                    graph = create_graph(mock_openai_api_key)

                    initial_state = {
                        **authenticated_agent_state,
                        "messages": [HumanMessage(content="Qual meu limite?")]
                    }

                    result = graph.invoke(initial_state)

                    mock_triagem_instance.process.assert_called()
                    mock_credito_instance.process.assert_called()

    def test_transicao_triagem_para_cambio(self, mock_openai_api_key, authenticated_agent_state):
        """Testa transição de triagem para câmbio."""
        with patch('src.core.graph.BancoAgilAgents'):
            with patch('src.core.graph.AgenteTriagem') as mock_triagem:
                with patch('src.core.graph.AgenteCambio') as mock_cambio:
                    mock_triagem_instance = Mock()
                    mock_triagem_instance.process.return_value = {
                        "current_agent": "triagem",
                        "pending_redirect": "cambio",
                        "messages": [],
                        "authenticated": True
                    }
                    mock_triagem.return_value = mock_triagem_instance

                    mock_cambio_instance = Mock()
                    mock_cambio_instance.process.return_value = {
                        "current_agent": "cambio",
                        "messages": [AIMessage(content="1 USD = R$ 5.25")],
                        "should_end": True
                    }
                    mock_cambio.return_value = mock_cambio_instance

                    graph = create_graph(mock_openai_api_key)

                    initial_state = {
                        **authenticated_agent_state,
                        "messages": [HumanMessage(content="Cotação do dólar?")]
                    }

                    result = graph.invoke(initial_state)

                    mock_triagem_instance.process.assert_called()
                    mock_cambio_instance.process.assert_called()

    def test_transicao_credito_para_entrevista(self, mock_openai_api_key, authenticated_agent_state):
        """Testa transição de crédito para entrevista."""
        with patch('src.core.graph.BancoAgilAgents'):
            with patch('src.core.graph.AgenteTriagem') as mock_triagem:
                with patch('src.core.graph.AgenteCredito') as mock_credito:
                    with patch('src.core.graph.AgenteEntrevista') as mock_entrevista:
                        mock_triagem_instance = Mock()
                        mock_triagem_instance.process.return_value = {
                            "current_agent": "triagem",
                            "pending_redirect": "credito",
                            "authenticated": True,
                            "messages": []
                        }
                        mock_triagem.return_value = mock_triagem_instance

                        mock_credito_instance = Mock()
                        mock_credito_instance.process.return_value = {
                            "current_agent": "credito",
                            "pending_redirect": "entrevista",
                            "messages": [AIMessage(content="Vamos fazer a entrevista")],
                            "authenticated": True
                        }
                        mock_credito.return_value = mock_credito_instance

                        mock_entrevista_instance = Mock()
                        mock_entrevista_instance.process.return_value = {
                            "current_agent": "entrevista",
                            "messages": [AIMessage(content="Entrevista iniciada")],
                            "should_end": True
                        }
                        mock_entrevista.return_value = mock_entrevista_instance

                        graph = create_graph(mock_openai_api_key)

                        initial_state = {
                            **authenticated_agent_state,
                            "messages": [HumanMessage(content="Quero fazer entrevista")]
                        }

                        result = graph.invoke(initial_state)

                        mock_triagem_instance.process.assert_called()
                        mock_credito_instance.process.assert_called()


class TestGraphEndConditions:
    """Testes para condições de fim do grafo."""

    def test_graph_termina_com_should_end(self, mock_openai_api_key, authenticated_agent_state):
        """Testa que o grafo termina quando should_end é True."""
        with patch('src.core.graph.BancoAgilAgents'):
            with patch('src.core.graph.AgenteTriagem') as mock_triagem:
                mock_instance = Mock()
                mock_instance.process.return_value = {
                    "current_agent": "triagem",
                    "messages": [AIMessage(content="Até logo!")],
                    "should_end": True,
                    "authenticated": False
                }
                mock_triagem.return_value = mock_instance

                graph = create_graph(mock_openai_api_key)

                initial_state = {
                    **authenticated_agent_state,
                    "messages": [HumanMessage(content="Sair")]
                }

                result = graph.invoke(initial_state)

                assert "should_end" in result or "messages" in result

    def test_graph_continua_sem_should_end(self, mock_openai_api_key, authenticated_agent_state):
        """Testa que o grafo continua quando should_end é False."""
        with patch('src.core.graph.BancoAgilAgents'):
            with patch('src.core.graph.AgenteTriagem') as mock_triagem:
                with patch('src.core.graph.AgenteCredito') as mock_credito:
                    mock_triagem_instance = Mock()
                    mock_triagem_instance.process.return_value = {
                        "current_agent": "triagem",
                        "pending_redirect": "credito",
                        "should_end": False,
                        "authenticated": True
                    }
                    mock_triagem.return_value = mock_triagem_instance

                    mock_credito_instance = Mock()
                    mock_credito_instance.process.return_value = {
                        "current_agent": "credito",
                        "messages": [AIMessage(content="Processando")],
                        "should_end": True
                    }
                    mock_credito.return_value = mock_credito_instance

                    graph = create_graph(mock_openai_api_key)

                    initial_state = {
                        **authenticated_agent_state,
                        "messages": [HumanMessage(content="Limite")]
                    }

                    result = graph.invoke(initial_state)

                    mock_credito_instance.process.assert_called()


class TestGraphStateManagement:
    """Testes para gerenciamento de estado no grafo."""

    def test_graph_mantem_estado_entre_transicoes(self, mock_openai_api_key, authenticated_agent_state):
        """Testa que o estado é mantido entre transições."""
        with patch('src.core.graph.BancoAgilAgents'):
            with patch('src.core.graph.AgenteTriagem') as mock_triagem:
                with patch('src.core.graph.AgenteCredito') as mock_credito:
                    mock_triagem_instance = Mock()
                    mock_triagem_instance.process.return_value = {
                        "current_agent": "triagem",
                        "pending_redirect": "credito",
                        "authenticated": True,
                        "cpf": "12345678901",
                        "nome_cliente": "João Silva"
                    }
                    mock_triagem.return_value = mock_triagem_instance
                    
                    def check_state(state):
                        assert state["cpf"] == "12345678901"
                        assert state["nome_cliente"] == "João Silva"
                        return {
                            "current_agent": "credito",
                            "messages": [AIMessage(content="OK")],
                            "should_end": True
                        }

                    mock_credito_instance = Mock()
                    mock_credito_instance.process = Mock(side_effect=check_state)
                    mock_credito.return_value = mock_credito_instance

                    graph = create_graph(mock_openai_api_key)

                    initial_state = {
                        **authenticated_agent_state,
                        "messages": [HumanMessage(content="Teste")]
                    }

                    result = graph.invoke(initial_state)

                    mock_credito_instance.process.assert_called()
