import hashlib

from cache import RedisCache as _SessionScopedRedisCache


class RedisCache(_SessionScopedRedisCache):
    """RedisCache variant for the agentic backend, keyed by query only.

    Inherits connection handling, get/set, and chat-history access from
    cache.RedisCache unchanged. Only make_cache_key differs: the agent's
    tool-use loop makes the same question cacheable across sessions, so the
    session_id is dropped from the key (unlike the base class, which scopes
    the cache key to session_id + query).

    Attributes:
        redis_client (redis.Redis): Redis client instance connected to the specified Redis server.

    Args:
        redis_url (str): The connection URL for the Redis server (e.g., "redis://localhost:6379/0").

    Methods:
        make_cache_key(query: str) -> str:
            Generates a unique SHA-256 cache key for a query, independent of session.

        get(key: str) -> Optional[str]:
            Retrieves a cached value from Redis for the given key.

        set(key: str, value: str, ttl: Optional[int] = None) -> None:
            Stores a value in Redis with an optional time-to-live (TTL) in seconds.

        get_chat_history(session_id: str) -> RedisChatMessageHistory:
            Returns a RedisChatMessageHistory object for the given session ID using LangChain's chat history utility.

    Example:
        >>> cache = RedisCache("redis://localhost:6379/0")
        >>> key = cache.make_cache_key("What is AI?")
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
        - Cache key omits session_id, so the same question hits the cache
          regardless of which session asked it.
        - Relies on LangChain's RedisChatMessageHistory for managing ongoing conversation state.
    """

    def make_cache_key(self, query):
        return "llm_cache_v2:" + hashlib.sha256(query.encode()).hexdigest()
