import os
import random

from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings

load_dotenv(".env.local")

TERMINAL_PUNCTUATION = ".!?"

# Corpus contains ~27 short non-legal greeting entries ("Hello", "How are you?") seeded for small talk.
MIN_CHUNK_LENGTH = 200

CHROMA_PERSIST_DIRECTORY = "chroma_db_legal_bot_part1"


def looks_self_contained(chunk_text: str) -> bool:
    """Cheap proxy for 'not visibly a mid-sentence fragment' — narrows the candidate pool, doesn't replace human review."""
    stripped = chunk_text.strip()
    if not stripped or len(stripped) < MIN_CHUNK_LENGTH:
        return False
    starts_clean = stripped[0].isupper() or stripped[0].isdigit()
    ends_clean = stripped[-1] in TERMINAL_PUNCTUATION
    return starts_clean and ends_clean


def load_all_chunk_texts(
    persist_directory: str = CHROMA_PERSIST_DIRECTORY,
) -> list[str]:
    """Real Chroma read; not unit tested, validated by a manual run."""
    embeddings = OpenAIEmbeddings(openai_api_key=os.getenv("OPENAI_API_KEY"))
    vector_store = Chroma(
        persist_directory=persist_directory, embedding_function=embeddings
    )
    return vector_store.get()["documents"]


def sample_clean_chunks(
    chunk_texts: list[str], n: int, seed: int | None = None
) -> list[str]:
    """Sample n chunks that pass looks_self_contained; raises if fewer than n qualify."""
    clean_chunks = [chunk for chunk in chunk_texts if looks_self_contained(chunk)]
    return random.Random(seed).sample(clean_chunks, n)
