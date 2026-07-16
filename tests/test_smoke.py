"""Smoke tests that verify core modules import and wire together without needing live API keys or a Redis server."""

import prompts
import chains
import cache
import lawglance_main


def test_prompts_defined():
    assert prompts.SYSTEM_PROMPT
    assert prompts.QA_PROMPT


def test_get_rag_chain_is_callable():
    assert callable(chains.get_rag_chain)


def test_redis_cache_key_is_deterministic():
    # redis.Redis.from_url() doesn't connect eagerly, so this needs no live Redis server.
    redis_cache = cache.RedisCache("redis://localhost:6379/0")
    key_a = redis_cache.make_cache_key("what is article 21?", "session-1")
    key_b = redis_cache.make_cache_key("what is article 21?", "session-1")
    assert key_a == key_b


def test_lawglance_class_importable():
    assert hasattr(lawglance_main, "Lawglance")
