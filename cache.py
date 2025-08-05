import redis
import hashlib
from langchain_community.chat_message_histories import RedisChatMessageHistory

class RedisCache:
    def __init__(self, redis_url):
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
        return RedisChatMessageHistory(session_id=session_id, url=self.redis_client.connection_pool.connection_kwargs['host'])