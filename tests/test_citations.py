import json
import pytest
from langchain_core.documents import Document
from langchain_core.prompts import PromptTemplate
from langchain_core.prompts.base import format_document

from citations import (
    CITATION_MARKER_KEY,
    Citation,
    annotate_documents_for_citation,
    cache_payload_to_result,
    citations_to_cache_payload,
    format_citation_label,
    resolve_answer_citations,
)


def build_citation(number: int) -> Citation:
    return Citation(
        number=number,
        label=f"Indian Constitution, PART {number}",
        snippet=f"passage {number}",
        source="https://example.gov/constitution.pdf",
    )


def build_part_document(
    page_content: str = "Article 21. Protection of life...",
) -> Document:
    """A chunk shaped like the 741 Part-level Constitution chunks."""
    return Document(
        page_content=page_content,
        metadata={
            "source": "https://example.gov/constitution.pdf",
            "source_name": "Indian Constitution",
            "country": "India",
            "db_owner": "LawGlance",
            "part": "PART III",
            "part_name": "Fundamental Rights",
        },
    )


def build_greeting_document(page_content: str = "Hello") -> Document:
    """A chunk shaped like the 27 small-talk chunks, which carry no legal identity."""
    return Document(
        page_content=page_content,
        metadata={
            "source": "english greeting words",
            "db_owner": "LawGlance",
            "language": "English",
        },
    )


def test_pairs_a_locator_with_its_name_sibling():
    metadata = {
        "source_name": "Indian Constitution",
        "country": "India",
        "db_owner": "LawGlance",
        "part": "PART III",
        "part_name": "Fundamental Rights",
    }

    assert format_citation_label(metadata) == (
        "Indian Constitution, PART III (Fundamental Rights)"
    )


def test_labels_a_schedule_chunk_without_a_name_sibling():
    metadata = {
        "source_name": "Indian Constitution",
        "country": "India",
        "db_owner": "LawGlance",
        "schedule": "schedule 1",
    }

    assert format_citation_label(metadata) == "Indian Constitution, schedule 1"


def test_labels_the_preamble_chunk():
    metadata = {
        "source_name": "Indian Constitution",
        "country": "India",
        "db_owner": "LawGlance",
        "preamble": "preamble",
    }

    assert format_citation_label(metadata) == "Indian Constitution, preamble"


def test_suppresses_chunks_carrying_no_identifying_metadata():
    """Small-talk chunks have only source/db_owner/language and are not citable."""
    metadata = {
        "source": "english greeting words",
        "db_owner": "LawGlance",
        "language": "English",
    }

    assert format_citation_label(metadata) is None


def test_suppresses_an_empty_metadata_dict():
    assert format_citation_label({}) is None


def test_falls_back_to_a_bare_title_when_no_locator_is_present():
    metadata = {"source_name": "Indian Constitution", "db_owner": "LawGlance"}

    assert format_citation_label(metadata) == "Indian Constitution"


def test_suppresses_a_locator_that_has_no_title_to_anchor_it():
    """A bare "PART III" names no document, so it cannot be verified."""
    metadata = {"part": "PART III", "db_owner": "LawGlance"}

    assert format_citation_label(metadata) is None


def test_never_treats_the_source_field_as_a_title():
    """`source` is a raw URL or an ingestion note, not a citable document name."""
    metadata = {
        "source": "https://example.gov/constitution.pdf",
        "db_owner": "LawGlance",
    }

    assert format_citation_label(metadata) is None


def test_generalises_to_a_corpus_with_its_own_schema():
    """A user-ingested act with section metadata needs no code change."""
    metadata = {
        "act": "Bharatiya Nyaya Sanhita",
        "section": "Section 103",
        "section_name": "Punishment for murder",
    }

    assert format_citation_label(metadata) == (
        "Bharatiya Nyaya Sanhita, Section 103 (Punishment for murder)"
    )


def test_prefers_the_most_specific_locator_when_several_are_present():
    metadata = {
        "source_name": "Indian Constitution",
        "article": "Article 21",
        "part": "PART III",
    }

    assert format_citation_label(metadata) == "Indian Constitution, Article 21"


@pytest.mark.parametrize(
    "metadata, expected",
    [
        (
            {"source_name": "Indian Constitution", "part": "PART  V"},
            "Indian Constitution, PART V",
        ),
        (
            {
                "source_name": "Indian Constitution",
                "part": "PART IV-A",
                "part_name": "Fundamental Duties ",
            },
            "Indian Constitution, PART IV-A (Fundamental Duties)",
        ),
        (
            {"source_name": "  Indian   Constitution  "},
            "Indian Constitution",
        ),
    ],
)
def test_normalises_inconsistent_whitespace(metadata, expected):
    assert format_citation_label(metadata) == expected


def test_preserves_roman_numeral_casing():
    """Titlecasing would turn PART III into "Part Iii"."""
    metadata = {"source_name": "Indian Constitution", "part": "PART XVII"}

    assert format_citation_label(metadata) == "Indian Constitution, PART XVII"


@pytest.mark.parametrize("empty_value", ["", "   ", None])
def test_treats_empty_values_as_absent_keys(empty_value):
    metadata = {"source_name": "Indian Constitution", "part": empty_value}

    assert format_citation_label(metadata) == "Indian Constitution"


def test_ignores_a_name_sibling_whose_locator_is_absent():
    metadata = {"source_name": "Indian Constitution", "part_name": "Fundamental Rights"}

    assert format_citation_label(metadata) == "Indian Constitution"


def test_coerces_non_string_metadata_values():
    """Chroma permits int metadata; a label must not crash on one."""
    metadata = {"source_name": "Indian Constitution", "chapter": 4}

    assert format_citation_label(metadata) == "Indian Constitution, 4"


def test_numbers_citable_documents_from_one():
    documents = [build_part_document("first"), build_part_document("second")]

    _, citations = annotate_documents_for_citation(documents)

    assert [c.number for c in citations] == [1, 2]


def test_embeds_the_number_and_label_in_the_marker():
    annotated, _ = annotate_documents_for_citation([build_part_document()])

    assert annotated[0].metadata[CITATION_MARKER_KEY] == (
        "[1] Indian Constitution, PART III (Fundamental Rights)"
    )


def test_gives_uncitable_documents_an_empty_marker_rather_than_omitting_the_key():
    """Every document needs the key, or the document_prompt raises on the missing one."""
    annotated, _ = annotate_documents_for_citation([build_greeting_document()])

    assert annotated[0].metadata[CITATION_MARKER_KEY] == ""


def test_excludes_uncitable_documents_from_the_citation_list():
    documents = [build_part_document(), build_greeting_document()]

    _, citations = annotate_documents_for_citation(documents)

    assert len(citations) == 1


def test_numbers_citable_documents_contiguously_across_suppressed_ones():
    documents = [
        build_greeting_document("Hello"),
        build_part_document("first legal chunk"),
        build_greeting_document("Hi"),
        build_part_document("second legal chunk"),
    ]

    annotated, citations = annotate_documents_for_citation(documents)

    assert [c.number for c in citations] == [1, 2]
    assert annotated[0].metadata[CITATION_MARKER_KEY] == ""
    assert annotated[1].metadata[CITATION_MARKER_KEY].startswith("[1] ")
    assert annotated[2].metadata[CITATION_MARKER_KEY] == ""
    assert annotated[3].metadata[CITATION_MARKER_KEY].startswith("[2] ")


def test_carries_the_verbatim_passage_as_the_snippet():
    passage = (
        "Article 21. No person shall be deprived of his life or personal liberty..."
    )

    _, citations = annotate_documents_for_citation([build_part_document(passage)])

    assert citations[0].snippet == passage


def test_carries_the_source_for_linking():
    _, citations = annotate_documents_for_citation([build_part_document()])

    assert citations[0].source == "https://example.gov/constitution.pdf"


def test_leaves_page_content_untouched():
    """PR1's eval matches chunks by exact page_content, so it must not drift."""
    passage = "Article 21. Protection of life and personal liberty."

    annotated, _ = annotate_documents_for_citation([build_part_document(passage)])

    assert annotated[0].page_content == passage


def test_does_not_mutate_the_input_documents():
    original = build_part_document()

    annotate_documents_for_citation([original])

    assert CITATION_MARKER_KEY not in original.metadata


def test_handles_an_empty_retrieval():
    annotated, citations = annotate_documents_for_citation([])

    assert annotated == []
    assert citations == []


def test_annotated_documents_never_raise_in_the_document_prompt():
    """Regression: format_document raises ValueError on any metadata key it cannot find.

    The greeting chunks lack source_name entirely, so a template referencing real
    metadata keys would crash on them. Precomputing one marker onto every document
    is what makes the template variable always resolvable.
    """
    document_prompt = PromptTemplate.from_template(
        "{" + CITATION_MARKER_KEY + "}\n{page_content}"
    )
    annotated, _ = annotate_documents_for_citation(
        [build_part_document(), build_greeting_document()]
    )

    rendered = [format_document(doc, document_prompt) for doc in annotated]

    assert rendered[0].startswith("[1] Indian Constitution")
    assert rendered[1] == "\nHello"


def test_a_naive_document_prompt_would_raise_on_greeting_chunks():
    """Pins down why the marker is precomputed rather than templated from metadata."""
    naive_prompt = PromptTemplate.from_template("[{source_name}] {page_content}")

    with pytest.raises(ValueError, match="source_name"):
        format_document(build_greeting_document(), naive_prompt)


def test_keeps_markers_backed_by_a_retrieved_chunk():
    citations = [build_citation(1), build_citation(2)]

    answer, _ = resolve_answer_citations("Equality is protected [1].", citations)

    assert answer == "Equality is protected [1]."


def test_strips_a_marker_no_retrieved_chunk_supports():
    """The model can invent [7] when only three chunks were numbered."""
    citations = [build_citation(1)]

    answer, _ = resolve_answer_citations("Life is protected [7].", citations)

    assert answer == "Life is protected."


def test_drops_citations_the_answer_never_used():
    citations = [build_citation(1), build_citation(2), build_citation(3)]

    _, kept = resolve_answer_citations("Only the second matters [2].", citations)

    assert [c.number for c in kept] == [2]


def test_keeps_original_numbers_so_markers_still_resolve():
    """Renumbering would break the [n] already written into the answer text."""
    citations = [build_citation(1), build_citation(2), build_citation(3)]

    answer, kept = resolve_answer_citations("Cites the third [3].", citations)

    assert answer == "Cites the third [3]."
    assert kept[0].number == 3


def test_handles_adjacent_markers():
    citations = [build_citation(1), build_citation(2)]

    answer, kept = resolve_answer_citations("Both apply [1][2].", citations)

    assert answer == "Both apply [1][2]."
    assert [c.number for c in kept] == [1, 2]


def test_handles_multi_digit_markers():
    citations = [build_citation(n) for n in range(1, 13)]

    answer, kept = resolve_answer_citations("The twelfth chunk [12].", citations)

    assert answer == "The twelfth chunk [12]."
    assert [c.number for c in kept] == [12]


def test_leaves_non_numeric_brackets_alone():
    """Legal quotations contain bracketed text that is not a citation marker."""
    citations = [build_citation(1)]

    answer, _ = resolve_answer_citations("The Act [sic] applies [1].", citations)

    assert answer == "The Act [sic] applies [1]."


def test_deduplicates_a_chunk_cited_more_than_once():
    citations = [build_citation(1), build_citation(2)]

    _, kept = resolve_answer_citations("First [1] and again [1].", citations)

    assert [c.number for c in kept] == [1]


def test_returns_no_citations_when_the_answer_cites_nothing():
    citations = [build_citation(1), build_citation(2)]

    answer, kept = resolve_answer_citations("I cannot answer that.", citations)

    assert answer == "I cannot answer that."
    assert kept == []


def test_returns_no_citations_when_nothing_citable_was_retrieved():
    answer, kept = resolve_answer_citations("Hello there [1].", [])

    assert answer == "Hello there."
    assert kept == []


def test_orders_kept_citations_by_number():
    citations = [build_citation(1), build_citation(2), build_citation(3)]

    _, kept = resolve_answer_citations("Third [3] then first [1].", citations)

    assert [c.number for c in kept] == [1, 3]


def test_strips_a_trailing_marker_without_leaving_whitespace():
    answer, _ = resolve_answer_citations("Unsupported claim [4]", [])

    assert answer == "Unsupported claim"


def test_round_trips_an_answer_through_the_cache_payload():
    payload = citations_to_cache_payload(
        "Equality is protected [1].", [build_citation(1)]
    )

    answer, _ = cache_payload_to_result(payload)

    assert answer == "Equality is protected [1]."


def test_round_trips_every_citation_field():
    original = build_citation(2)

    _, restored = cache_payload_to_result(
        citations_to_cache_payload("a [2].", [original])
    )

    assert restored == [original]


def test_round_trips_an_answer_with_no_citations():
    _, restored = cache_payload_to_result(citations_to_cache_payload("Hello.", []))

    assert restored == []


def test_round_trips_a_citation_without_a_source():
    original = Citation(number=1, label="Some Act", snippet="text", source=None)

    _, restored = cache_payload_to_result(
        citations_to_cache_payload("a [1].", [original])
    )

    assert restored[0].source is None


def test_round_trips_legal_text_containing_newlines_and_unicode():
    """Constitution passages carry footnote markers and hard line breaks."""
    snippet = "PART III\nArticle 21. — No person shall be deprived…"
    original = Citation(
        number=1, label="Indian Constitution", snippet=snippet, source=None
    )

    _, restored = cache_payload_to_result(
        citations_to_cache_payload("a [1].", [original])
    )

    assert restored[0].snippet == snippet


def test_writes_an_inspectable_json_payload():
    """Cached values should be readable with redis-cli when debugging."""
    payload = citations_to_cache_payload("answer [1].", [build_citation(1)])

    assert json.loads(payload)["answer"] == "answer [1]."
