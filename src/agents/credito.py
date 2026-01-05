import logging
from typing import Dict, Any

from langchain_core.messages import SystemMessage, AIMessage

from src.core.state import AgentState
from src.tools.atendimento import encerrar_atendimento
from src.tools.credito import consultar_limite_credito, solicitar_aumento_limite

logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class AgenteCredito:
    """Agente de Crédito - Consulta e aumento de limite."""

    def __init__(self, llm, llm_with_tools):
        self.llm = llm
        self.llm_with_tools = llm_with_tools

    def process(self, state: AgentState) -> Dict[str, Any]:
        """Processa a requisição do agente de crédito."""
        try:
            system_prompt = """Você é o Agente de Crédito do Banco Ágil.

Suas responsabilidades:
1. Consultar limite de crédito atual usando 'consultar_limite_credito'
2. Processar solicitações de aumento de limite usando 'solicitar_aumento_limite'
3. Se a solicitação for rejeitada, oferecer redirecionamento para entrevista de crédito

REGRAS DE USO DAS FERRAMENTAS:
- Use 'consultar_limite_credito' APENAS quando o cliente pergunta "qual é meu limite?" ou "quanto tenho de limite?"
- Use 'solicitar_aumento_limite' quando o cliente PEDE/SOLICITA um aumento de limite (ex: "quero aumentar para X", "aumente meu limite para X", "pode aumentar para X")
- NUNCA use 'consultar_limite_credito' quando o cliente está pedindo um aumento - vá direto para 'solicitar_aumento_limite'

IMPORTANTE:
- CPF do cliente: {cpf}
- Seja claro sobre o motivo de aprovação ou rejeição
- Se rejeitado, explique que pode fazer entrevista para melhorar score
- Para redirecionar à entrevista, responda "REDIRECIONAR: entrevista"
- Se o cliente desejar encerrar, use a ferramenta encerrar_atendimento
- Seja cordial e objetivo

Cliente autenticado: {nome}
"""

            messages = [
                SystemMessage(content=system_prompt.format(
                    cpf=state.get("cpf", ""),
                    nome=state.get("nome_cliente", "")
                ))
            ] + list(state["messages"])

            response = self.llm_with_tools.invoke(messages)

            updates = {"current_agent": "credito"}

            if response.tool_calls:
                tool_results = []
                for tool_call in response.tool_calls:
                    if tool_call["name"] == "consultar_limite_credito":
                        result = consultar_limite_credito.invoke({"cpf": state["cpf"]})
                        tool_results.append(result["mensagem"])
                        response = AIMessage(content=result["mensagem"])

                    elif tool_call["name"] == "solicitar_aumento_limite":
                        args = tool_call["args"]
                        args["cpf"] = state["cpf"]
                        result = solicitar_aumento_limite.invoke(args)

                        if result["aprovado"]:
                            updates["limite_credito"] = args["novo_limite"]
                            response = AIMessage(content=result["mensagem"])
                        else:
                            response = AIMessage(
                                content=result["mensagem"] + "\n\n" +
                                "Posso encaminhá-lo para uma entrevista de crédito que pode melhorar seu score. "
                                "Deseja fazer a entrevista?"
                            )

                    elif tool_call["name"] == "encerrar_atendimento":
                        result = encerrar_atendimento.invoke({})
                        updates["should_end"] = True
                        response = AIMessage(content=result["mensagem"])

            if hasattr(response, 'content') and response.content:
                if "REDIRECIONAR:" in response.content:
                    redirect_to = response.content.split("REDIRECIONAR:")[1].strip().split()[0]
                    updates["pending_redirect"] = redirect_to
                    clean_message = response.content.split("REDIRECIONAR:")[0].strip()
                    return updates
            else:
                if not response.content:
                    response = AIMessage(content="Processando sua solicitação...")

            updates["messages"] = [response]
            return updates
        except Exception as e:
            logger.error(f"Erro no agente de crédito: {str(e)}", exc_info=True)
            return {
                "current_agent": "credito",
                "messages": [AIMessage(content="Desculpe, tivemos um problema ao processar sua solicitação de crédito. Por favor, tente novamente em alguns instantes ou entre em contato com nossa central.")],
                "should_end": False
            }
