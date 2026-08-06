from typing import Protocol

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from pydantic import BaseModel

from eval.golden_set import GoldenQAItem

load_dotenv(".env.local")

DEFAULT_MODEL = "gpt-4o-mini"

QA_DRAFT_PROMPT_TEMPLATE = (
    "Given the following passage from a legal text, write one question that this "
    "passage directly and uniquely answers. The question must be answerable using "
    "only the information in this passage.\n\nPassage:\n{chunk_text}"
)


class DraftedQuestion(BaseModel):
    question: str


class QuestionDraftingChain(Protocol):
    def invoke(self, prompt: str) -> DraftedQuestion: ...


def build_qa_generation_chain(model: str = DEFAULT_MODEL) -> QuestionDraftingChain:
    """Real LLM-backed chain; not unit tested, validated by a manual run."""
    return ChatOpenAI(model=model).with_structured_output(DraftedQuestion)


def draft_question_for_chunk(chunk_text: str, chain: QuestionDraftingChain) -> str:
    """Draft one candidate question whose answer lives in chunk_text."""
    prompt = QA_DRAFT_PROMPT_TEMPLATE.format(chunk_text=chunk_text)
    return chain.invoke(prompt).question


def generate_candidate_qa_items(
    chunk_texts: list[str], chain: QuestionDraftingChain
) -> list[GoldenQAItem]:
    """Draft one candidate GoldenQAItem per chunk, for human accept/edit review."""
    return [
        GoldenQAItem(
            question=draft_question_for_chunk(chunk_text, chain), chunk_text=chunk_text
        )
        for chunk_text in chunk_texts
    ]
