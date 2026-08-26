from langgraph.graph import StateGraph, START, END
from backend.state import MessagesState
from backend.nodes import llm_call, tool_node, should_continue, final_answer

def agent_builder_graph(state: MessagesState):
    # Build workflow
    agent_builder = StateGraph(state)

    # Add nodes
    agent_builder.add_node("llm_call", llm_call)
    agent_builder.add_node("tool_node", tool_node)
    agent_builder.add_node("final_answer", final_answer )

    # Add edges to connect nodes
    agent_builder.add_edge(START, "llm_call")
    agent_builder.add_conditional_edges(
        "llm_call",
        should_continue,
        ["tool_node", "final_answer"]
    )

    agent_builder.add_edge("tool_node", "llm_call")
    agent_builder.add_edge("final_answer", END)


    return agent_builder