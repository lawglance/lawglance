from langchain.messages import HumanMessage
from backend.state import MessagesState
from backend.graph import agent_builder_graph
from backend.config import cache, CACHE_TTL
from backend.citation import citations_to_cache_payload, cache_payload_to_result, Citation
from dotenv import load_dotenv
from pathlib import Path
import uuid


load_dotenv()

def agent_invoke(query: str, session_id: str | None = None):
    session_id = session_id or str(uuid.uuid4())
    cache_key = cache.make_cache_key(query)

    history = cache.get_chat_history(session_id)

    cached_payload = cache.get(cache_key)
    if cached_payload is not None:
        cached_answer, cached_citations = cache_payload_to_result(cached_payload)
        history.add_user_message(query)
        history.add_ai_message(cached_answer)
        return cached_answer, cached_citations, session_id

    # Compile the agent
    agent_builder = agent_builder_graph(state=MessagesState)
    agent = agent_builder.compile()

    # Invoke
    messages = history.messages + [HumanMessage(content=query)]
    result = agent.invoke({"messages": messages})
    for m in result["messages"]:
        m.pretty_print()

    answer = result["messages"][-1]
    citations = [Citation(**c) for c in answer.additional_kwargs.get("citations", [])]

    history.add_user_message(query)
    history.add_ai_message(answer.content)
    cache.set(
        cache_key,
        citations_to_cache_payload(answer.content, citations),
        ttl=CACHE_TTL,
    )

    return answer.content, citations, session_id


# if __name__ == "__main__":
#     query = input("Ask the question:")
#     agent_invoke(query=query)
