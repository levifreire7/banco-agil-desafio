from typing import Annotated, Optional, Sequence, TypedDict

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    """Estado compartilhado entre todos os agentes."""
    messages: Annotated[Sequence[BaseMessage], add_messages]
    current_agent: str
    authenticated: bool
    cpf: Optional[str]
    nome_cliente: Optional[str]
    limite_credito: Optional[float]
    score: Optional[int]
    authentication_attempts: int
    pending_redirect: Optional[str]
    interview_data: Optional[dict]
    should_end: bool
    temp_cpf: Optional[str]
    temp_data_nascimento: Optional[str]
