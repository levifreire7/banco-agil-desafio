import logging
import re
from typing import Any, Dict

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from src.core.state import AgentState
from src.tools.atendimento import encerrar_atendimento
from src.tools.autenticacao import autenticar_cliente

logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class AgenteTriagem:
    """Agente de Triagem - Autenticação e direcionamento."""

    def __init__(self, llm, llm_with_tools):
        self.llm = llm
        self.llm_with_tools = llm_with_tools

    def process(self, state: AgentState) -> Dict[str, Any]:
        """Processa a requisição do agente de triagem."""
        try:
            if state.get("authenticated", False):
                return self._process_authenticated(state)

            return self._process_authentication(state)
        except Exception as e:
            logger.error(f"Erro no agente de triagem: {str(e)}", exc_info=True)
            return {
                "current_agent": "triagem",
                "messages": [AIMessage(content="Desculpe, ocorreu um erro inesperado. Por favor, tente novamente em alguns instantes.")],
                "should_end": True
            }

    def _process_authenticated(self, state: AgentState) -> Dict[str, Any]:
        """Processa usuário já autenticado."""
        system_prompt = """Você é o Agente de Triagem do Banco Ágil.

O cliente já está autenticado como {nome}.

IMPORTANTE: Você NÃO deve responder às perguntas do cliente. Sua ÚNICA função é identificar a necessidade e redirecionar.

Identifique a necessidade do cliente e direcione IMEDIATAMENTE:
- Se pergunta sobre LIMITE DE CRÉDITO, AUMENTO DE LIMITE ou CRÉDITO → Responda APENAS: "REDIRECIONAR: credito"
- Se pergunta sobre COTAÇÃO, MOEDAS, CÂMBIO, DÓLAR, EURO → Responda APENAS: "REDIRECIONAR: cambio"
- Se quer ENCERRAR/SAIR → use a ferramenta encerrar_atendimento

NÃO responda às perguntas. NÃO tente ajudar. APENAS redirecione usando o formato exato acima.
IMPORTANTE: O agente de entrevista NÃO está disponível via triagem. Questões sobre entrevista ou score devem ir para crédito.
"""
        messages = [
            SystemMessage(content=system_prompt.format(nome=state.get("nome_cliente", "")))
        ] + list(state["messages"])

        response = self.llm_with_tools.invoke(messages)
        updates = {"current_agent": "triagem"}

        # Se o LLM tentou chamar uma ferramenta que não é de triagem, redireciona silenciosamente
        if response.tool_calls:
            for tool_call in response.tool_calls:
                tool_name = tool_call["name"]
                if tool_name == "consultar_limite_credito" or tool_name == "solicitar_aumento_limite":
                    updates["pending_redirect"] = "credito"
                    return updates
                elif tool_name == "consultar_cotacao_moeda":
                    updates["pending_redirect"] = "cambio"
                    return updates
                elif tool_name == "calcular_novo_score":
                    # Entrevista só pode ser acessada via agente de crédito
                    updates["pending_redirect"] = "credito"
                    return updates
                elif tool_name == "encerrar_atendimento":
                    result = encerrar_atendimento.invoke({})
                    updates["should_end"] = True
                    response = AIMessage(content=result["mensagem"])

        if hasattr(response, 'content') and "REDIRECIONAR:" in response.content:
            redirect_to = response.content.split("REDIRECIONAR:")[1].strip().split()[0]
            # Bloqueia redirecionamento direto para entrevista - deve ir via crédito
            if redirect_to == "entrevista":
                redirect_to = "credito"
            updates["pending_redirect"] = redirect_to
            clean_message = response.content.split("REDIRECIONAR:")[0].strip()
            return updates

        updates["messages"] = [response]
        return updates

    def _process_authentication(self, state: AgentState) -> Dict[str, Any]:
        """Processa autenticação do usuário."""
        cpf_temp = state.get("temp_cpf")
        data_temp = state.get("temp_data_nascimento")
        
        if len(state["messages"]) > 0:
            last_user_message = ""
            for msg in reversed(state["messages"]):
                if isinstance(msg, HumanMessage):
                    last_user_message = msg.content
                    break
            
            cpf_match = re.search(r'\b\d{11}\b', last_user_message)
            if cpf_match and not cpf_temp:
                cpf_temp = cpf_match.group(0)

            data_match = re.search(r'\b\d{4}-\d{2}-\d{2}\b', last_user_message)
            if data_match:
                data_temp = data_match.group(0)

        updates = {"current_agent": "triagem"}

        if cpf_temp and data_temp:
            result = autenticar_cliente.invoke({"cpf": cpf_temp, "data_nascimento": data_temp})

            if result["sucesso"]:
                updates["authenticated"] = True
                updates["cpf"] = result["cliente"]["cpf"]
                updates["nome_cliente"] = result["cliente"]["nome"]
                updates["limite_credito"] = result["cliente"]["limite_credito"]
                updates["score"] = result["cliente"]["score"]
                updates["authentication_attempts"] = 0
                updates["temp_cpf"] = None
                updates["temp_data_nascimento"] = None
                response = AIMessage(content=result["mensagem"] + "\n\nComo posso ajudá-lo hoje?")
            else:
                new_attempts = state.get("authentication_attempts", 0) + 1
                updates["authentication_attempts"] = new_attempts
                updates["temp_cpf"] = None
                updates["temp_data_nascimento"] = None

                if new_attempts >= 3:
                    updates["should_end"] = True
                    response = AIMessage(
                        content="Lamento, mas não foi possível autenticar seus dados após 3 tentativas. "
                               "Por favor, entre em contato com nossa central de atendimento. Até logo!"
                    )
                else:
                    response = AIMessage(
                        content=f"{result['mensagem']} Você tem mais {3 - new_attempts} tentativa(s). "
                               f"Por favor, informe seu CPF novamente."
                    )
        
        elif cpf_temp and not data_temp:            
            system_prompt_data = """Você é o Agente de Triagem do Banco Ágil.

O cliente já forneceu o CPF mas ainda NÃO completou a autenticação.

Suas responsabilidades:
- Agradecer pelo CPF e solicitar a data de nascimento no formato AAAA-MM-DD (exemplo: 1990-05-15)
- Se o cliente demonstrar que quer ENCERRAR/SAIR/CANCELAR o atendimento, use a ferramenta encerrar_atendimento
- Seja cordial e objetivo

IMPORTANTE: Analise a intenção do cliente. Se ele claramente quer sair, encerre. Caso contrário, solicite a data de nascimento."""

            messages_data = [SystemMessage(content=system_prompt_data)] + list(state["messages"])
            response_data = self.llm_with_tools.invoke(messages_data)
            
            if response_data.tool_calls:
                for tool_call in response_data.tool_calls:
                    if tool_call["name"] == "encerrar_atendimento":                        
                        result = encerrar_atendimento.invoke({})
                        updates["should_end"] = True
                        response = AIMessage(content=result["mensagem"])
                        updates["messages"] = [response]
                        return updates
            
            updates["temp_cpf"] = cpf_temp
            response = response_data        
        else:
            system_prompt = """Você é o Agente de Triagem do Banco Ágil.

O cliente ainda NÃO está autenticado.

Suas responsabilidades:
- Responda cordialmente ao cliente e peça o CPF (11 dígitos)
- Se o cliente demonstrar que quer ENCERRAR/SAIR/CANCELAR o atendimento, use a ferramenta encerrar_atendimento
- Seja educado mas objetivo

IMPORTANTE: Analise a intenção do cliente. Se ele claramente quer sair, encerre. Caso contrário, solicite o CPF."""

            messages = [SystemMessage(content=system_prompt)] + list(state["messages"])
            response = self.llm_with_tools.invoke(messages)
            
            if response.tool_calls:
                for tool_call in response.tool_calls:
                    if tool_call["name"] == "encerrar_atendimento":                        
                        result = encerrar_atendimento.invoke({})
                        updates["should_end"] = True
                        response = AIMessage(content=result["mensagem"])

        updates["messages"] = [response]
        return updates
