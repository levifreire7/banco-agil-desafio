"""Fixtures de respostas mockadas do LLM para testes."""
from langchain_core.messages import AIMessage


TRIAGEM_SOLICITA_CPF = AIMessage(
    content="Olá! Bem-vindo ao Banco Ágil. Por favor, informe seu CPF para continuar."
)

TRIAGEM_SOLICITA_DATA = AIMessage(
    content="Obrigado! Agora, por favor, informe sua data de nascimento no formato AAAA-MM-DD."
)

TRIAGEM_AUTENTICADO = AIMessage(
    content="Cliente autenticado com sucesso. Bem-vindo(a), João Silva!\n\nComo posso ajudá-lo hoje?"
)

TRIAGEM_REDIRECIONA_CREDITO = AIMessage(
    content="REDIRECIONAR: credito"
)

TRIAGEM_REDIRECIONA_CAMBIO = AIMessage(
    content="REDIRECIONAR: cambio"
)

CREDITO_CONSULTA_LIMITE = AIMessage(
    content="Seu limite de crédito atual é R$ 5000.00"
)

CREDITO_AUMENTO_APROVADO = AIMessage(
    content="Solicitação aprovada! Seu novo limite é R$ 8000.00"
)

CREDITO_AUMENTO_REJEITADO = AIMessage(
    content="Solicitação rejeitada. Seu score atual (350) não permite este limite.\n\n"
            "Posso encaminhá-lo para uma entrevista de crédito que pode melhorar seu score. "
            "Deseja fazer a entrevista?"
)

CREDITO_REDIRECIONA_ENTREVISTA = AIMessage(
    content="REDIRECIONAR: entrevista"
)

CAMBIO_COTACAO_USD = AIMessage(
    content="1 USD = R$ 5.25"
)

CAMBIO_COTACAO_EUR = AIMessage(
    content="1 EUR = R$ 6.10"
)

ENTREVISTA_PERGUNTA_RENDA = AIMessage(
    content="Vou fazer algumas perguntas para calcular seu novo score.\n\n"
            "Qual é sua renda mensal?"
)

ENTREVISTA_PERGUNTA_EMPREGO = AIMessage(
    content="Há quanto tempo você está empregado? (em anos)"
)

ENTREVISTA_SCORE_CALCULADO = AIMessage(
    content="Entrevista concluída! Seu novo score foi calculado: 720\n\n"
            "Deseja solicitar um aumento de limite agora?"
)

ENCERRAMENTO = AIMessage(
    content="Obrigado por utilizar o Banco Ágil. Até logo!"
)

ERRO_GENERICO = AIMessage(
    content="Desculpe, ocorreu um erro inesperado. Por favor, tente novamente em alguns instantes."
)

ERRO_AUTENTICACAO = AIMessage(
    content="CPF ou data de nascimento incorretos. Você tem mais 2 tentativa(s). Por favor, informe seu CPF novamente."
)

ERRO_LIMITE_EXCEDIDO = AIMessage(
    content="Lamento, mas não foi possível autenticar seus dados após 3 tentativas. "
            "Por favor, entre em contato com nossa central de atendimento. Até logo!"
)


def create_tool_call_response(tool_name: str, args: dict, content: str = "") -> AIMessage:
    """Cria uma resposta do LLM com chamada de ferramenta."""
    response = AIMessage(content=content)
    response.tool_calls = [
        {
            "name": tool_name,
            "args": args,
            "id": f"test_{tool_name}_call"
        }
    ]
    return response


# Respostas com Tool Calls
def get_consultar_limite_response(cpf: str) -> AIMessage:
    """Retorna resposta mockada para consultar limite."""
    return create_tool_call_response(
        "consultar_limite_credito",
        {"cpf": cpf},
        ""
    )


def get_solicitar_aumento_response(cpf: str, novo_limite: float) -> AIMessage:
    """Retorna resposta mockada para solicitar aumento."""
    return create_tool_call_response(
        "solicitar_aumento_limite",
        {"cpf": cpf, "novo_limite": novo_limite},
        ""
    )


def get_consultar_cotacao_response(moeda: str = "USD") -> AIMessage:
    """Retorna resposta mockada para consultar cotação."""
    return create_tool_call_response(
        "consultar_cotacao_moeda",
        {"moeda": moeda},
        ""
    )


def get_encerrar_atendimento_response() -> AIMessage:
    """Retorna resposta mockada para encerrar atendimento."""
    return create_tool_call_response(
        "encerrar_atendimento",
        {},
        ""
    )


def get_calcular_score_response(cpf: str, interview_data: dict) -> AIMessage:
    """Retorna resposta mockada para calcular novo score."""
    return create_tool_call_response(
        "calcular_novo_score",
        {"cpf": cpf, "interview_data": interview_data},
        ""
    )
