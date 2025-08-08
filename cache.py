import redis
import hashlib
from langchain_community.chat_message_histories import RedisChatMessageHistory

class RedisCache:
    """
    RedisCache provides an interface for storing and retrieving cached LLM responses and chat histories 
    using a Redis backend. It also integrates with LangChain's RedisChatMessageHistory to persist chat sessions.

    Attributes:
        redis_client (redis.Redis): Redis client instance connected to the specified Redis server.

    Args:
        redis_url (str): The connection URL for the Redis server (e.g., "redis://localhost:6379/0").

    Methods:
        make_cache_key(query: str, session_id: str) -> str:
            Generates a unique SHA-256 cache key for a query-session pair.

        get(key: str) -> Optional[str]:
            Retrieves a cached value from Redis for the given key.

        set(key: str, value: str, ttl: Optional[int] = None) -> None:
            Stores a value in Redis with an optional time-to-live (TTL) in seconds.

        get_chat_history(session_id: str) -> RedisChatMessageHistory:
            Returns a RedisChatMessageHistory object for the given session ID using LangChain's chat history utility.

    Example:
        >>> cache = RedisCache("redis://localhost:6379/0")
        >>> key = cache.make_cache_key("What is AI?", "user123")
        >>> cache.set(key, "AI stands for Artificial Intelligence.")
        >>> print(cache.get(key))
        "AI stands for Artificial Intelligence."
        
        >>> chat_history = cache.get_chat_history("user123")
        >>> chat_history.add_user_message("Hello!")
        >>> messages = chat_history.messages
        >>> print(messages[0].content)
        "Hello!"

    Notes:
        - Keys are hashed for consistency and security using SHA-256.
        - Supports both persistent and time-limited (TTL) caching.
        - Relies on LangChain's RedisChatMessageHistory for managing ongoing conversation state.
    """
    def __init__(self, redis_url):
        self.redis_url = redis_url
        self.redis_client = redis.Redis.from_url(redis_url)

    def make_cache_key(self, query, session_id):
        key_raw = f"{session_id}:{query}"
        return "llm_cache:" + hashlib.sha256(key_raw.encode()).hexdigest()

    def get(self, key):
        value = self.redis_client.get(key)
        return value.decode("utf-8") if value else None

    def set(self, key, value, ttl=None):
        if ttl:
            self.redis_client.setex(key, ttl, value)
        else:
            self.redis_client.set(key, value)

    def get_chat_history(self, session_id):
        return RedisChatMessageHistory(session_id=session_id, url=self.redis_url)
