from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain.chat_models import init_chat_model
from dotenv import load_dotenv
from pathlib import Path
import os

from backend.cache import RedisCache

DATA = Path(__file__).resolve().parent.parent

load_dotenv()

model = init_chat_model("openai:gpt-5.5", temperature=0)
embeddings = OpenAIEmbeddings()
vector_store = Chroma(
    embedding_function=embeddings,
    persist_directory=str(DATA / "chroma_db_legal_bot_part1"),
)

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
CACHE_TTL = int(os.getenv("CACHE_TTL", "3600"))
cache = RedisCache(REDIS_URL)
