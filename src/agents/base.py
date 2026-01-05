from langchain_openai import ChatOpenAI

from src.config import settings
from src.tools import tools_list


class BancoAgilAgents:
    """Classe base para gerenciar os agentes."""

    def __init__(self, openai_api_key: str):
        self.llm = ChatOpenAI(
            model=settings.llm_model,
            temperature=settings.llm_temperature,
            api_key=openai_api_key
        )
        self.llm_with_tools = self.llm.bind_tools(tools_list)
