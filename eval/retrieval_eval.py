import os
from dataclasses import dataclass
from typing import Callable

from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_core.vectorstores import VectorStoreRetriever
from langchain_openai import OpenAIEmbeddings

from eval.chunk_sampling import CHROMA_PERSIST_DIRECTORY
from eval.golden_set import GoldenQAItem
from eval.metrics import (
    mean_reciprocal_rank,
    rank_of_correct_chunk,
    recall,
    recall_confidence_interval,
)

load_dotenv(".env.local")

# Must match chains.py's get_rag_chain retriever config exactly — PR1 measures this config, not a different one.
RETRIEVER_SEARCH_TYPE = "similarity_score_threshold"
RETRIEVER_SEARCH_KWARGS = {"k": 10, "score_threshold": 0.3}


@dataclass
class EvalResults:
    recall: float
    mrr: float
    ranks: list[int | None]
    recall_ci: tuple[float, float]


def build_real_retriever(
    persist_directory: str = CHROMA_PERSIST_DIRECTORY,
) -> VectorStoreRetriever:
    """Real Chroma-backed retriever; not unit tested, validated by a manual run."""
    embeddings = OpenAIEmbeddings(openai_api_key=os.getenv("OPENAI_API_KEY"))
    vector_store = Chroma(
        persist_directory=persist_directory, embedding_function=embeddings
    )
    return vector_store.as_retriever(
        search_type=RETRIEVER_SEARCH_TYPE, search_kwargs=RETRIEVER_SEARCH_KWARGS
    )


def run_retrieval_eval(
    golden_set: list[GoldenQAItem],
    retrieve_fn: Callable[[str], list[Document]],
) -> EvalResults:
    """Score retrieve_fn against golden_set, matching on exact page_content."""
    ranks = [
        rank_of_correct_chunk(
            [doc.page_content for doc in retrieve_fn(item.question)],
            item.chunk_text,
        )
        for item in golden_set
    ]
    return EvalResults(
        recall=recall(ranks),
        mrr=mean_reciprocal_rank(ranks),
        ranks=ranks,
        recall_ci=recall_confidence_interval(ranks),
    )
