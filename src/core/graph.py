import os

from langgraph.graph import StateGraph, START, END

from src.agents.base import BancoAgilAgents
from src.agents.cambio import AgenteCambio
from src.agents.credito import AgenteCredito
from src.agents.entrevista import AgenteEntrevista
from src.agents.triagem import AgenteTriagem
from src.core.state import AgentState


def create_graph(openai_api_key: str):
    """Cria o grafo de estados do LangGraph com os agentes."""

    base_agents = BancoAgilAgents(openai_api_key)

    agente_triagem = AgenteTriagem(base_agents.llm, base_agents.llm_with_tools)
    agente_credito = AgenteCredito(base_agents.llm, base_agents.llm_with_tools)
    agente_entrevista = AgenteEntrevista(base_agents.llm, base_agents.llm_with_tools)
    agente_cambio = AgenteCambio(base_agents.llm, base_agents.llm_with_tools)

    def triagem_node(state: AgentState) -> AgentState:
        """Nó do agente de triagem."""
        updates = agente_triagem.process(state)
        new_state = {**state, **updates}
        if "pending_redirect" in updates:
            new_state["pending_redirect"] = updates["pending_redirect"]
        else:
            new_state["pending_redirect"] = None
        return new_state

    def credito_node(state: AgentState) -> AgentState:
        """Nó do agente de crédito."""
        updates = agente_credito.process(state)
        new_state = {**state, **updates}
        if "pending_redirect" in updates:
            new_state["pending_redirect"] = updates["pending_redirect"]
        else:
            new_state["pending_redirect"] = None
        return new_state

    def entrevista_node(state: AgentState) -> AgentState:
        """Nó do agente de entrevista."""
        updates = agente_entrevista.process(state)
        new_state = {**state, **updates}
        if "pending_redirect" in updates:
            new_state["pending_redirect"] = updates["pending_redirect"]
        else:
            new_state["pending_redirect"] = None
        return new_state

    def cambio_node(state: AgentState) -> AgentState:
        """Nó do agente de câmbio."""
        updates = agente_cambio.process(state)
        new_state = {**state, **updates}
        if "pending_redirect" in updates:
            new_state["pending_redirect"] = updates["pending_redirect"]
        else:
            new_state["pending_redirect"] = None
        return new_state

    def router_node(state: AgentState) -> AgentState:
        """Nó roteador inicial - decide para qual agente direcionar."""
        # Router simples: apenas verifica se está em entrevista ativa
        # Caso contrário, sempre vai para triagem que faz o roteamento real
        return state

    workflow = StateGraph(AgentState)

    workflow.add_node("router", router_node)
    workflow.add_node("triagem", triagem_node)
    workflow.add_node("credito", credito_node)
    workflow.add_node("entrevista", entrevista_node)
    workflow.add_node("cambio", cambio_node)

    workflow.add_edge(START, "router")

    # Router decide: entrevista se está em processo de entrevista, senão triagem
    workflow.add_conditional_edges(
        "router",
        lambda state: (
            "entrevista" if state.get("current_agent") == "entrevista" else
            "triagem"
        ),
        {
            "triagem": "triagem",
            "entrevista": "entrevista"
        }
    )

    workflow.add_conditional_edges(
        "triagem",
        lambda state: (
            "end" if state.get("should_end") else
            "credito" if state.get("pending_redirect") == "credito" else
            "cambio" if state.get("pending_redirect") == "cambio" else
            "end"
        ),
        {
            "credito": "credito",
            "cambio": "cambio",
            "end": END
        }
    )

    workflow.add_conditional_edges(
        "credito",
        lambda state: "entrevista" if state.get("pending_redirect") == "entrevista" else ("end" if state.get("should_end") else "end"),
        {
            "entrevista": "entrevista",
            "end": END
        }
    )

    workflow.add_conditional_edges(
        "entrevista",
        lambda state: (
            "credito" if state.get("pending_redirect") == "credito" else
            "end" if state.get("should_end") else
            "end"
        ),
        {
            "credito": "credito",
            "end": END
        }
    )

    workflow.add_conditional_edges(
        "cambio",
        lambda state: "end" if state.get("should_end") else "end",
        {
            "end": END
        }
    )

    return workflow.compile()

key = os.getenv("OPENAI_API_KEY")
graph = create_graph(key)