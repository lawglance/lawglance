"""Citation labelling and numbering for retrieval-grounded answers.

The agentic backend shares the same citation model as the original
Lawglance pipeline, so this module re-exports the canonical implementation
from the top-level `citations` module instead of duplicating it.
"""

from citations import (
    CITATION_MARKER_KEY,
    LOCATOR_KEYS,
    TITLE_KEYS,
    Citation,
    annotate_documents_for_citation,
    cache_payload_to_result,
    citations_to_cache_payload,
    format_citation_label,
    resolve_answer_citations,
)

__all__ = [
    "CITATION_MARKER_KEY",
    "LOCATOR_KEYS",
    "TITLE_KEYS",
    "Citation",
    "annotate_documents_for_citation",
    "cache_payload_to_result",
    "citations_to_cache_payload",
    "format_citation_label",
    "resolve_answer_citations",
]
