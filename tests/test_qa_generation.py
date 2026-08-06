from eval.qa_generation import (
    DraftedQuestion,
    draft_question_for_chunk,
    generate_candidate_qa_items,
)


class FakeChain:
    def __init__(self, question: str):
        self.question = question
        self.last_prompt = None

    def invoke(self, prompt: str) -> DraftedQuestion:
        self.last_prompt = prompt
        return DraftedQuestion(question=self.question)


def test_draft_question_for_chunk_returns_chain_output():
    chain = FakeChain(question="What does Article 1 declare India to be?")

    question = draft_question_for_chunk("India, that is Bharat.", chain)

    assert question == "What does Article 1 declare India to be?"


def test_draft_question_for_chunk_passes_chunk_text_into_prompt():
    chain = FakeChain(question="irrelevant")

    draft_question_for_chunk("India, that is Bharat.", chain)

    assert "India, that is Bharat." in chain.last_prompt


def test_generate_candidate_qa_items_pairs_each_chunk_with_its_drafted_question():
    chain = FakeChain(question="What does this passage declare?")
    chunk_texts = ["India, that is Bharat.", "Parliament may admit new States."]

    items = generate_candidate_qa_items(chunk_texts, chain)

    assert [item.chunk_text for item in items] == chunk_texts
    assert all(item.question == "What does this passage declare?" for item in items)
