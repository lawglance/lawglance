from dataclasses import asdict
from langchain.messages import SystemMessage, ToolMessage, AIMessage, HumanMessage
from backend.state import MessagesState
from typing import Literal
from backend.tools import retrieve_docs
from backend.config import model
from backend.citation import resolve_answer_citations
from backend.prompts import SYSTEM_PROMPT, QA_PROMPT


# Define tools
#--------------
tools = [retrieve_docs]
tools_by_name = {tool.name: tool for tool in tools}
model_with_tools = model.bind_tools(tools)

# LLM mode
#---------
def llm_call(state: dict):
    """LLM decides whether to call a tool or not"""

    return {
        "messages": [
            model_with_tools.invoke(
                [
                    SystemMessage(
                        content=SYSTEM_PROMPT
                    )
                ]
                + state["messages"]
            )
        ],
        "llm_calls": state.get('llm_calls', 0) + 1
    }



# Tool Node
#-----------
def tool_node(state: dict):
    """Performs the tool call"""

    result = []
    new_citations = []
    for tool_call in state["messages"][-1].tool_calls:
        tool = tools_by_name[tool_call["name"]]
        tool_message = tool.invoke(tool_call)
        result.append(tool_message)
        if tool_message.artifact:
            new_citations.extend(tool_message.artifact)
    return {"messages": result, "citations": new_citations}

# Final answer Node
#------------------

def final_answer(state: dict):
    """Produce final answer once tool loop is done, with deterministic citations"""

    messages = state["messages"]

    context = "\n".join(m.content for m in messages if isinstance(m, ToolMessage))
    question = next(
        m.content for m in reversed(messages) if isinstance(m, HumanMessage)
    )

    qa_prompt = QA_PROMPT.format(context=context, input=question)

    result = model.invoke(messages + [HumanMessage(content=qa_prompt)])

    resolved_answer, kept_citations = resolve_answer_citations(
        result.content, state.get("citations", [])
    )
    sources = "\n".join(f"[{c.number}] {c.label}" for c in kept_citations)
    content = (
        f"{resolved_answer}\n\nSources:\n{sources}" if kept_citations else resolved_answer
    )

    return {
        "messages": [
            AIMessage(
                content=content,
                additional_kwargs={"citations": [asdict(c) for c in kept_citations]},
            )
        ]
    }





def should_continue(state: MessagesState) -> Literal["tool_node", "final_answer"]:
    """Decide if we should continue the loop or stop based upon whether the LLM made a tool call"""

    messages = state["messages"]
    last_message = messages[-1]

    # If the LLM makes a tool call, then perform an action
    if last_message.tool_calls:
        return "tool_node"

    return "final_answer"