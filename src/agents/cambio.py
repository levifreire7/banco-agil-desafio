import logging
from typing import Dict, Any

from langchain_core.messages import AIMessage, SystemMessage

from src.core.state import AgentState
from src.tools.atendimento import encerrar_atendimento
from src.tools.cambio import consultar_cotacao_moeda

logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class AgenteCambio:
    """Agente de Câmbio - Consulta cotações."""

    def __init__(self, llm, llm_with_tools):
        self.llm = llm
        self.llm_with_tools = llm_with_tools

    def process(self, state: AgentState) -> Dict[str, Any]:
        """Processa a requisição do agente de câmbio."""
        try:
            system_prompt = """Você é o Agente de Câmbio do Banco Ágil.

Suas responsabilidades:
1. Consultar cotação de moedas usando 'consultar_cotacao_moeda'
2. Apresentar a cotação de forma clara
3. Perguntar se deseja consultar outra moeda ou encerrar

IMPORTANTE:
- Identifique a moeda que o cliente está perguntando (dólar=USD, euro=EUR, libra=GBP, etc.)
- Use a ferramenta consultar_cotacao_moeda com o código da moeda
- Seja cordial e objetivo
- Se o cliente desejar encerrar, use a ferramenta encerrar_atendimento
- Se o cliente perguntar sobre OUTROS ASSUNTOS (não relacionados a moedas), informe educadamente que você só atende consultas de câmbio

Cliente autenticado: {nome}
"""

            messages = [
                SystemMessage(content=system_prompt.format(
                    nome=state.get("nome_cliente", "")
                ))
            ] + list(state["messages"])

            response = self.llm_with_tools.invoke(messages)

            updates = {"current_agent": "cambio"}

            if response.tool_calls:
                for tool_call in response.tool_calls:
                    if tool_call["name"] == "consultar_cotacao_moeda":
                        result = consultar_cotacao_moeda.invoke(tool_call["args"])
                        response = AIMessage(
                            content=result["mensagem"] + "\n\nDeseja consultar outra moeda ou posso ajudar com algo mais?"
                        )

                    elif tool_call["name"] == "encerrar_atendimento":
                        result = encerrar_atendimento.invoke({})
                        updates["should_end"] = True
                        response = AIMessage(content=result["mensagem"])

            updates["messages"] = [response]
            return updates
        except Exception as e:
            logger.error(f"Erro no agente de câmbio: {str(e)}", exc_info=True)
            return {
                "current_agent": "cambio",
                "messages": [AIMessage(content="Desculpe, não foi possível consultar a cotação no momento. Por favor, tente novamente em alguns instantes.")],
                "should_end": False
            }
