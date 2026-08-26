from langchain.messages import AnyMessage
from typing_extensions import TypedDict, Annotated
import operator

from backend.citation import Citation


class MessagesState(TypedDict):
    messages: Annotated[list[AnyMessage], operator.add]
    llm_calls: int
    citations: Annotated[list[Citation], operator.add]
