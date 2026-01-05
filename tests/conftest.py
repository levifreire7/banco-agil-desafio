"""Configurações e fixtures compartilhadas para todos os testes."""
import os
import tempfile
from typing import Generator
from unittest.mock import Mock

import pytest
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from src.data_models.database import Database
from src.data_models.models import Cliente


@pytest.fixture
def temp_data_dir() -> Generator[str, None, None]:
    """Cria um diretório temporário para arquivos de dados de teste."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def sample_cliente() -> Cliente:
    """Retorna um cliente de exemplo para testes."""
    return Cliente(
        cpf="12345678901",
        nome="João Silva",
        data_nascimento="1990-05-15",
        limite_credito=5000.0,
        score=650
    )


@pytest.fixture
def sample_cliente_alto_score() -> Cliente:
    """Retorna um cliente com score alto para testes."""
    return Cliente(
        cpf="98765432100",
        nome="Maria Santos",
        data_nascimento="1985-10-20",
        limite_credito=15000.0,
        score=850
    )


@pytest.fixture
def sample_cliente_baixo_score() -> Cliente:
    """Retorna um cliente com score baixo para testes."""
    return Cliente(
        cpf="11122233344",
        nome="Pedro Costa",
        data_nascimento="1995-03-10",
        limite_credito=1000.0,
        score=350
    )


@pytest.fixture
def mock_database(temp_data_dir, sample_cliente) -> Database:
    """Retorna uma instância de Database com dados de teste."""
    db = Database(base_path=temp_data_dir)

    # Cria arquivo de clientes
    clientes_file = os.path.join(temp_data_dir, "clientes.csv")
    with open(clientes_file, 'w', encoding='utf-8') as f:
        f.write("cpf,nome,data_nascimento,limite_credito,score\n")
        f.write(f"{sample_cliente.cpf},{sample_cliente.nome},{sample_cliente.data_nascimento},"
                f"{sample_cliente.limite_credito},{sample_cliente.score}\n")
        f.write("98765432100,Maria Santos,1985-10-20,15000.0,850\n")
        f.write("11122233344,Pedro Costa,1995-03-10,1000.0,350\n")

    # Cria arquivo de score_limite
    score_limite_file = os.path.join(temp_data_dir, "score_limite.csv")
    with open(score_limite_file, 'w', encoding='utf-8') as f:
        f.write("score_minimo,score_maximo,limite_maximo\n")
        f.write("0,499,5000.0\n")
        f.write("500,699,10000.0\n")
        f.write("700,849,20000.0\n")
        f.write("850,1000,50000.0\n")

    return db


@pytest.fixture
def mock_llm():
    """Retorna um mock do LLM para testes."""
    llm = Mock()
    llm.invoke = Mock(return_value=AIMessage(content="Resposta mockada do LLM"))
    return llm


@pytest.fixture
def mock_llm_with_tools():
    """Retorna um mock do LLM com tools para testes."""
    llm = Mock()
    response = AIMessage(content="Resposta mockada do LLM com tools")
    response.tool_calls = []
    llm.invoke = Mock(return_value=response)
    return llm


@pytest.fixture
def sample_agent_state():
    """Retorna um estado inicial de agente para testes."""
    return {
        "messages": [],
        "current_agent": "triagem",
        "authenticated": False,
        "cpf": None,
        "nome_cliente": None,
        "limite_credito": None,
        "score": None,
        "authentication_attempts": 0,
        "pending_redirect": None,
        "interview_data": None,
        "should_end": False,
        "temp_cpf": None,
        "temp_data_nascimento": None,
    }


@pytest.fixture
def authenticated_agent_state(sample_cliente):
    """Retorna um estado de agente autenticado para testes."""
    return {
        "messages": [HumanMessage(content="Olá")],
        "current_agent": "triagem",
        "authenticated": True,
        "cpf": sample_cliente.cpf,
        "nome_cliente": sample_cliente.nome,
        "limite_credito": sample_cliente.limite_credito,
        "score": sample_cliente.score,
        "authentication_attempts": 0,
        "pending_redirect": None,
        "interview_data": None,
        "should_end": False,
        "temp_cpf": None,
        "temp_data_nascimento": None,
    }


@pytest.fixture
def mock_openai_api_key(monkeypatch):
    """Define uma API key fake para testes."""
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-fake-key-for-testing")
    return "sk-test-fake-key-for-testing"


@pytest.fixture
def sample_human_message():
    """Retorna uma mensagem humana de exemplo."""
    return HumanMessage(content="Olá, preciso de ajuda")


@pytest.fixture
def sample_ai_message():
    """Retorna uma mensagem AI de exemplo."""
    return AIMessage(content="Como posso ajudá-lo?")


@pytest.fixture
def sample_system_message():
    """Retorna uma mensagem de sistema de exemplo."""
    return SystemMessage(content="Você é um assistente útil")
