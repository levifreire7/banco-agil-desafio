import logging
from typing import Dict, Any

from langchain_core.messages import AIMessage, SystemMessage

from src.core.state import AgentState
from src.tools.score import calcular_novo_score
from src.tools.atendimento import encerrar_atendimento

logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class AgenteEntrevista:
    """Agente de Entrevista de Crédito - Coleta dados e recalcula score de forma conversacional."""

    def __init__(self, llm, llm_with_tools):
        self.llm = llm
        self.llm_with_tools = llm_with_tools

    def process(self, state: AgentState) -> Dict[str, Any]:
        """Processa a requisição do agente de entrevista."""
        try:
            system_prompt = """Você é o Agente de Entrevista de Crédito do Banco Ágil.

Sua missão é conduzir uma entrevista conversacional e natural para coletar as seguintes informações do cliente:

INFORMAÇÕES NECESSÁRIAS:
1. renda_mensal: Renda mensal em reais (número)
2. tipo_emprego: Tipo de emprego (formal/autonomo/desempregado)
3. despesas_fixas: Despesas fixas mensais em reais (número)
4. num_dependentes: Número de dependentes (0, 1, 2, ou 3+)
5. tem_dividas: Se possui dívidas ativas (true/false)

INSTRUÇÕES:
- Conduza a conversa de forma natural e amigável
- Faça UMA pergunta por vez
- Adapte suas perguntas ao contexto da conversa
- Se o cliente fornecer múltiplas informações de uma vez, agradeça e colete
- Seja claro e objetivo
- Quando tiver TODAS as 5 informações, use a ferramenta 'calcular_novo_score' para calcular o novo score

IMPORTANTE:
- Extraia números considerando "mil", "k", "milhão", etc. (ex: "5 mil" = 5000, "3.5k" = 3500)
- Para tipo_emprego, aceite variações: CLT/carteira/registro = formal, autônomo/freelance/MEI = autonomo
- Para num_dependentes, se disser "3 ou mais", use 3
- Para tem_dividas, sim/tenho/possuo = true, não/sem/nenhuma = false
- Mantenha tom profissional mas acolhedor
- Após calcular o score, informe o resultado e diga "REDIRECIONAR: credito"
- Se o cliente desejar encerrar o atendimento, use a ferramenta encerrar_atendimento

Cliente: {nome}
CPF: {cpf}
"""

            messages = [
                SystemMessage(content=system_prompt.format(
                    nome=state.get("nome_cliente", ""),
                    cpf=state.get("cpf", "")
                ))
            ] + list(state["messages"])

            response = self.llm_with_tools.invoke(messages)

            updates = {"current_agent": "entrevista"}

            if response.tool_calls:
                for tool_call in response.tool_calls:
                    if tool_call["name"] == "calcular_novo_score":
                        args = tool_call["args"]
                        args["cpf"] = state["cpf"]
                        result = calcular_novo_score.invoke(args)

                        if result["sucesso"]:
                            updates["score"] = result["novo_score"]
                            updates["pending_redirect"] = "credito"

                            response = AIMessage(
                                content=result["mensagem"] +
                                        "\n\nVou redirecioná-lo de volta ao atendimento de crédito para reanalisar sua solicitação."
                            )
                        else:
                            response = AIMessage(content=result["mensagem"])

                    elif tool_call["name"] == "encerrar_atendimento":
                        result = encerrar_atendimento.invoke({})
                        updates["should_end"] = True
                        response = AIMessage(content=result["mensagem"])

            if hasattr(response, 'content') and response.content:
                if "REDIRECIONAR:" in response.content:
                    redirect_to = response.content.split("REDIRECIONAR:")[1].strip().split()[0]
                    updates["pending_redirect"] = redirect_to
                    clean_message = response.content.split("REDIRECIONAR:")[0].strip()
                    response = AIMessage(content=clean_message)

            updates["messages"] = [response]
            return updates
        except Exception as e:
            logger.error(f"Erro no agente de entrevista: {str(e)}", exc_info=True)
            return {
                "current_agent": "entrevista",
                "messages": [AIMessage(content="Desculpe, ocorreu um problema durante a entrevista. Por favor, tente novamente em alguns instantes ou retorne ao menu anterior.")],
                "pending_redirect": "credito"
            }
