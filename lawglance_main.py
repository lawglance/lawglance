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