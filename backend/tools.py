# Define vector store
from backend.config import embeddings, vector_store
from backend.citation import annotate_documents_for_citation, CITATION_MARKER_KEY
from langchain.tools import tool
from pathlib import Path


@tool(response_format="content_and_artifact")
def retrieve_docs(query:str):
    """
    This function retrieve relevant docs from the vector store based on similarity search.
    Args:
        query:str User question for a semantic search , it should not be a keyword search. should be a full sentence search
    """

    result = vector_store.similarity_search(query, k=5)
    annotated_docs, citations = annotate_documents_for_citation(result)
    content = "\n\n".join(
        f"{doc.metadata[CITATION_MARKER_KEY]}\n{doc.page_content}".strip()
        for doc in annotated_docs
    )

    return content, citations

