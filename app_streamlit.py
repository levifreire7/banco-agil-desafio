from langchain_core.messages import HumanMessage
import streamlit as st

from src.config import settings
from src.core.graph import create_graph


def initialize_session_state():
    """Inicializa o estado da sessão do Streamlit."""
    if "messages" not in st.session_state:
        st.session_state.messages = []

    if "agent_state" not in st.session_state:
        st.session_state.agent_state = {
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
            "temp_data_nascimento": None
        }

    if "graph" not in st.session_state:
        if not settings.is_configured:
            st.error("ERRO: OPENAI_API_KEY não encontrada no arquivo .env")
            st.stop()
        st.session_state.graph = create_graph(settings.openai_api_key)

    if "chat_started" not in st.session_state:
        st.session_state.chat_started = False


def display_chat_messages():
    """Exibe as mensagens do chat."""
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])


def process_user_input(user_input: str):
    """Processa a entrada do usuário e obtém a resposta do chatbot."""
    previous_authenticated = st.session_state.agent_state.get("authenticated", False)
    previous_limite = st.session_state.agent_state.get("limite_credito")
    previous_score = st.session_state.agent_state.get("score")
    previous_nome = st.session_state.agent_state.get("nome_cliente")

    st.session_state.agent_state["messages"].append(HumanMessage(content=user_input))

    try:        
        result = st.session_state.graph.invoke(st.session_state.agent_state)
        st.session_state.agent_state = result

        current_authenticated = result.get("authenticated", False)
        current_limite = result.get("limite_credito")
        current_score = result.get("score")
        current_nome = result.get("nome_cliente")

        state_changed = (
            previous_authenticated != current_authenticated or
            previous_limite != current_limite or
            previous_score != current_score or
            previous_nome != current_nome
        )

        response = None
        if result["messages"]:
            last_message = result["messages"][-1]
            if hasattr(last_message, 'content') and last_message.content:
                response = last_message.content
            else:
                response = "Processando sua solicitação..."
        else:
            response = "Sem resposta - verificando estado..."

        return response, state_changed

    except Exception as e:
        return f"❌ Erro: Ocorreu um problema no atendimento: {str(e)}", False


def main():
    """Função principal da aplicação Streamlit."""
    st.set_page_config(
        page_title="Banco Ágil - Atendimento Inteligente",
        page_icon="🏦",
        layout="centered"
    )

    initialize_session_state()

    st.title("🏦 Banco Ágil")
    st.subheader("Sistema de Atendimento Inteligente")

    with st.sidebar:
        st.header("Informações")

        if st.session_state.agent_state["authenticated"]:
            st.success("✅ Autenticado")
            if st.session_state.agent_state["nome_cliente"]:
                st.info(f"👤 Cliente: {st.session_state.agent_state['nome_cliente']}")
            if st.session_state.agent_state["limite_credito"] is not None:
                st.info(f"💳 Limite: R$ {st.session_state.agent_state['limite_credito']:,.2f}")
            if st.session_state.agent_state["score"] is not None:
                st.info(f"📊 Score: {st.session_state.agent_state['score']}")
        else:
            st.warning("🔓 Não autenticado")

        st.divider()

        if st.button("🔄 Nova Conversa", use_container_width=True):
            st.session_state.messages = []
            st.session_state.agent_state = {
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
                "temp_data_nascimento": None
            }
            st.session_state.chat_started = False
            if "estado_limpo" in st.session_state:
                del st.session_state.estado_limpo
            st.rerun()

    if not st.session_state.chat_started:
        st.session_state.messages.append({
            "role": "assistant",
            "content": "Olá! Bem-vindo ao **Banco Ágil** 👋\n\nPara garantir sua segurança e acessar seus serviços, informe seu **CPF**."
        })
        st.session_state.chat_started = True

    display_chat_messages()

    if st.session_state.agent_state.get("should_end", False):
        if "estado_limpo" not in st.session_state:
            st.session_state.estado_limpo = True    
            st.session_state.agent_state.update({
                "authenticated": False,
                "cpf": None,
                "nome_cliente": None,
                "limite_credito": None,
                "score": None,
                "authentication_attempts": 0,
                "pending_redirect": None,
                "interview_data": None,
                "temp_cpf": None,
                "temp_data_nascimento": None
            })
            st.rerun()

        st.info("ℹ️ Atendimento encerrado. Clique em 'Nova Conversa' para iniciar um novo atendimento.")
        return

    if user_input := st.chat_input("Digite sua mensagem..."):    
        st.session_state.messages.append({
            "role": "user",
            "content": user_input
        })
        
        with st.chat_message("user"):
            st.markdown(user_input)
    
        with st.chat_message("assistant"):
            with st.spinner("Processando..."):
                response, state_changed = process_user_input(user_input)
            st.markdown(response)

        st.session_state.messages.append({
            "role": "assistant",
            "content": response
        })
    
        if state_changed or st.session_state.agent_state.get("should_end", False):
            st.rerun()


if __name__ == "__main__":
    main()
