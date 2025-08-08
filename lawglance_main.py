import threading
import logging
from cache import RedisCache
from langchain.schema import HumanMessage, AIMessage
from chains import get_rag_chain
from prompts import SYSTEM_PROMPT, QA_PROMPT

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s',
    handlers=[logging.StreamHandler()]
)

class Lawglance:
    """
    Lawglance is a conversational AI interface that leverages a retrieval-augmented generation (RAG) pipeline 
    to answer user queries based on vector search and LLM responses. It supports Redis-based caching to improve 
    performance and stores session-based chat histories in memory.

    Attributes:
        llm: An instance of the language model to use (e.g., OpenAI, Anthropic, etc.).
        embeddings: Embedding model used for vectorization of text.
        vector_store: A vector store (e.g., Chroma, FAISS) used for semantic retrieval.
        cache: Instance of RedisCache for caching responses and chat histories.

    Args:
        llm (BaseLanguageModel): The LLM to generate responses.
        embeddings (Embeddings): Embedding model used for vector search.
        vector_store (VectorStore): A vector store instance to fetch relevant documents.
        redis_url (str): Redis connection string. Defaults to "redis://localhost:6379/0".

    Methods:
        get_session_history(session_id: str) -> RedisChatMessageHistory:
            Retrieves or initializes the chat history for the given session ID.
        
        conversational(query: str, session_id: str) -> Tuple[str, list]:
            Handles the user query, checks for cached responses, invokes RAG pipeline if necessary,
            updates history, and returns answer and updated messages.
    """
    store = {}
    store_lock = threading.Lock()

    def __init__(self, llm, embeddings, vector_store, redis_url="redis://localhost:6379/0"):
        self.llm = llm
        self.embeddings = embeddings
        self.vector_store = vector_store
        self.cache = RedisCache(redis_url)

    def get_session_history(self, session_id):
        with Lawglance.store_lock:
            if session_id not in Lawglance.store:
                Lawglance.store[session_id] = self.cache.get_chat_history(session_id)
                logging.info(f"Created new chat history for session_id: {session_id}")
            else:
                logging.debug(f"Using existing chat history for session_id: {session_id}")
        return Lawglance.store[session_id]

    def conversational(self, query, session_id):
        """
        Handles a query from a user within a session:
        - Uses Redis-based history for retrieval.
        - Returns cached response if available.
        - Otherwise, runs full RAG pipeline and updates history.

        Returns:
            Tuple[str, list]: (LLM answer, updated message list)
        """
        cache_key = self.cache.make_cache_key(query, session_id)
        cached_answer = self.cache.get(cache_key)
        if cached_answer:
            logging.info(f"Cache hit for key: {cache_key}")
            chat_history = self.get_session_history(session_id).messages
            return cached_answer, chat_history

        logging.info(f"Cache miss for key: {cache_key}. Generating new answer.")

        rag_chain = get_rag_chain(self.llm, self.vector_store, SYSTEM_PROMPT, QA_PROMPT)

        chat_history_obj = self.get_session_history(session_id)
        messages = chat_history_obj.messages

        response = rag_chain.invoke(
            {"input": query, "chat_history": messages},
            config={"configurable": {"session_id": session_id}},
        )

        answer = response['answer']

        # Update chat history
        chat_history_obj.add_user_message(query)
        chat_history_obj.add_ai_message(answer)

        # Cache the answer
        self.cache.set(cache_key, answer)

        return answer, chat_history_obj.messages
