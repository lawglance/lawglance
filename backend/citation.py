"""Citation labelling and numbering for retrieval-grounded answers.

Labels are built from whatever metadata keys a retrieved chunk happens to carry, so
the module works against any ingested corpus rather than the seeded Constitution
schema. Chunks with no identifying metadata are not citable.
"""

import json
import re
from dataclasses import asdict, dataclass
from typing import Any, Mapping

from langchain_core.documents import Document

# An optional leading space is consumed so stripping an unsupported marker does not
# leave a doubled space behind.
_MARKER_PATTERN = re.compile(r" ?\[(\d+)\]")

TITLE_KEYS = ("source_name", "title", "document_title", "act", "statute", "law")

LOCATOR_KEYS = (
    "article",
    "section",
    "clause",
    "rule",
    "regulation",
    "part",
    "chapter",
    "schedule",
    "preamble",
)

CITATION_MARKER_KEY = "citation_marker"


@dataclass(frozen=True)
class Citation:
    """A numbered, verifiable reference to one retrieved chunk."""

    number: int
    label: str
    snippet: str
    source: str | None


def _normalise(value: Any) -> str | None:
    """Collapse whitespace and treat blanks as absent; casing is preserved."""
    if value is None:
        return None
    text = " ".join(str(value).split())
    return text or None


def _first_present(
    metadata: Mapping[str, Any], keys: tuple[str, ...]
) -> tuple[str | None, str | None]:
    for key in keys:
        value = _normalise(metadata.get(key))
        if value is not None:
            return key, value
    return None, None


def format_citation_label(metadata: Mapping[str, Any]) -> str | None:
    """Human-readable label for a chunk, or None if it carries no identifying metadata."""
    _, title = _first_present(metadata, TITLE_KEYS)
    if title is None:
        return None

    locator_key, locator = _first_present(metadata, LOCATOR_KEYS)
    if locator is None:
        return title

    locator_name = _normalise(metadata.get(f"{locator_key}_name"))
    if locator_name is not None:
        return f"{title}, {locator} ({locator_name})"
    return f"{title}, {locator}"


def annotate_documents_for_citation(
    documents: list[Document],
) -> tuple[list[Document], list[Citation]]:
    """Copy documents with a citation_marker in metadata, numbering the citable ones."""
    annotated: list[Document] = []
    citations: list[Citation] = []

    for document in documents:
        label = format_citation_label(document.metadata)
        marker = ""

        if label is not None:
            citation = Citation(
                number=len(citations) + 1,
                label=label,
                snippet=document.page_content,
                source=_normalise(document.metadata.get("source")),
            )
            citations.append(citation)
            marker = f"[{citation.number}] {citation.label}"

        annotated.append(
            Document(
                page_content=document.page_content,
                metadata={**document.metadata, CITATION_MARKER_KEY: marker},
            )
        )

    return annotated, citations


def resolve_answer_citations(
    answer: str, citations: list[Citation]
) -> tuple[str, list[Citation]]:
    """Strip markers the retrieval never supported and drop citations the answer never used."""
    citations_by_number = {citation.number: citation for citation in citations}
    cited_numbers: set[int] = set()

    def keep_or_strip(match: re.Match[str]) -> str:
        number = int(match.group(1))
        if number not in citations_by_number:
            return ""
        cited_numbers.add(number)
        return match.group(0)

    resolved = _MARKER_PATTERN.sub(keep_or_strip, answer)
    kept = [citations_by_number[number] for number in sorted(cited_numbers)]
    return resolved, kept


def citations_to_cache_payload(answer: str, citations: list[Citation]) -> str:
    """Serialise an answer and its citations for cache storage."""
    return json.dumps(
        {"answer": answer, "citations": [asdict(c) for c in citations]},
        ensure_ascii=False,
    )


def cache_payload_to_result(payload: str) -> tuple[str, list[Citation]]:
    """Restore an answer and its citations from a cache payload."""
    data = json.loads(payload)
    return data["answer"], [Citation(**item) for item in data["citations"]]
