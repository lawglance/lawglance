import pytest
from langchain_core.documents import Document

from eval.golden_set import GoldenQAItem
from eval.metrics import recall_confidence_interval
from eval.retrieval_eval import run_retrieval_eval


def test_run_retrieval_eval_scores_against_retrieved_chunks():
    golden_set = [
        GoldenQAItem(question="q1", chunk_text="correct chunk 1"),
        GoldenQAItem(question="q2", chunk_text="correct chunk 2"),
    ]

    def fake_retrieve(question: str) -> list[Document]:
        if question == "q1":
            return [
                Document(page_content="correct chunk 1"),
                Document(page_content="other"),
            ]
        return [Document(page_content="unrelated")]

    results = run_retrieval_eval(golden_set, fake_retrieve)

    assert results.ranks == [1, None]
    assert results.recall == 0.5
    assert results.mrr == pytest.approx(0.5)
    assert results.recall_ci == recall_confidence_interval([1, None])
