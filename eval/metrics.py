import math


def rank_of_correct_chunk(
    retrieved_chunk_ids: list[str], correct_chunk_id: str
) -> int | None:
    """1-indexed position of correct_chunk_id in retrieved_chunk_ids, or None if absent."""
    if correct_chunk_id not in retrieved_chunk_ids:
        return None
    return retrieved_chunk_ids.index(correct_chunk_id) + 1


def recall(ranks: list[int | None]) -> float:
    """Fraction of ranks that are not None."""
    if not ranks:
        raise ValueError("ranks must not be empty")
    return sum(1 for r in ranks if r is not None) / len(ranks)


def mean_reciprocal_rank(ranks: list[int | None]) -> float:
    """Average of 1/rank across ranks, treating None as 0."""
    if not ranks:
        raise ValueError("ranks must not be empty")
    return sum(1 / r if r is not None else 0 for r in ranks) / len(ranks)


def recall_confidence_interval(ranks: list[int | None]) -> tuple[float, float]:
    """95% Wilson score interval for recall — more reliable than the normal approximation at small n."""
    z = 1.96
    n = len(ranks)
    p_hat = recall(ranks)
    denominator = 1 + z**2 / n
    center = (p_hat + z**2 / (2 * n)) / denominator
    half_width = (z / denominator) * math.sqrt(
        p_hat * (1 - p_hat) / n + z**2 / (4 * n**2)
    )
    return center - half_width, center + half_width
