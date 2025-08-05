import threading
import logging
from cache import RedisCache
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
        get_session_history(session_id: str) -> list:
            Retrieves or initializes the chat history for the given session ID.
        
        conversational(query: str, session_id: str, chat_history: Optional[list] = None) -> str:
            Handles the user query, checks for cached responses, invokes RAG pipeline if necessary,
            and returns an LLM-generated answer.

    Example:
        >>> from langchain.chat_models import ChatOpenAI
        >>> from langchain.vectorstores import Chroma
        >>> from lawglance import Lawglance
        >>> llm = ChatOpenAI()
        >>> vector_store = Chroma()
        >>> app = Lawglance(llm, embeddings, vector_store)
        >>> response = app.conversational("What is Article 21 of the Constitution?", session_id="user_123")
        >>> print(response)
        "Article 21 of the Indian Constitution guarantees the right to life and personal liberty..."

    Notes:
        - Chat history is stored in memory during runtime and synchronized with Redis for persistence.
        - Redis caching significantly improves performance by avoiding redundant LLM calls for repeated queries.
        - Thread safety is ensured when accessing or updating session histories using a class-level lock.
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

    def conversational(self, query, session_id, chat_history=None):
        cache_key = self.cache.make_cache_key(query, session_id)
        cached_answer = self.cache.get(cache_key)
        if cached_answer:
            logging.info(f"Cache hit for key: {cache_key}")
            return cached_answer
        logging.info(f"Cache miss for key: {cache_key}. Generating new answer.")
        rag_chain = get_rag_chain(self.llm, self.vector_store, SYSTEM_PROMPT, QA_PROMPT)
        get_session_history = self.get_session_history
        response = rag_chain.invoke(
            {"input": query, "chat_history": chat_history or []},
            config={"configurable": {"session_id": session_id}},
        )
        answer = response['answer']
        self.cache.set(cache_key, answer)
        return answer
