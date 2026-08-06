# Retrieval Eval Results

Measures the retriever config in `chains.py` (`search_type="similarity_score_threshold"`, `k=10`, `score_threshold=0.3`) against a small, human-verified golden QA set. Eval-only — no production code changed.

## Method

- 18 candidate chunks sampled from the ingested corpus (`chroma_db_legal_bot_part1`, 1006 chunks), filtered by a cheap heuristic (`eval/chunk_sampling.py`) for likely-self-contained, non-fragment text and a minimum length (to exclude ~27 short non-legal "greeting" entries seeded in the corpus for small talk).
- One candidate question drafted per chunk by `gpt-4o-mini` (`eval/qa_generation.py`), then manually reviewed against a 3-point checklist: the answer is explicit in the chunk, the chunk is self-contained (or at least the answer-bearing portion of it is), and the question isn't answerable by other chunks. 4 of 22 initial candidates were rejected and replaced on this basis; the final 18 all passed review.
- Each question run through the retriever in isolation (`eval/retrieval_eval.py`) — no LLM generation involved, this measures retrieval only.
- Scoring matches on exact `page_content` string equality — the pinned `langchain-chroma` version doesn't expose a stable chunk id on retrieval, so the retrieved chunk's text is the only reliable identity signal.

## Results

| Metric | Value |
|---|---|
| Recall@10 | 94.4% (17/18) |
| MRR | 0.789 |
| 95% CI (Wilson) on Recall@10 | 74.2% – 99.0% |

**n=18 is a directional signal, not a precise estimate** — the confidence interval above spans ~25 points. This sample size was a deliberate choice (see PR description / issue #15 discussion): cheap enough to fully human-verify each item, sized to catch a gross retrieval failure, not to pin down whether true recall is 90% or 98%.

## Failure analysis

**One miss** (question: *"What topics are included in the Eleventh Schedule under Article 243G?"*) — the retriever's top 10 never surfaced the actual Eleventh Schedule chunk. Instead it returned content from the Fifth, Sixth, and Seventh Schedules plus other Article 243-series provisions. This looks like a real, specific weakness: the Constitution has several structurally similar numbered schedules (lists of topics/subjects), and a generically-phrased "what topics are in Schedule X" question doesn't discriminate well between them at the embedding level.

**One near-miss** (question about the Rajasthan Colonisation Act) — retrieved, but at rank 9, just inside the `k=10` cutoff. A slightly harder phrasing of the same question would plausibly drop below the threshold or outside `k=10` entirely.

## Scope

No changes to `chains.py`/`prompts.py`/`lawglance_main.py`. No parameter sweep over `k`/`score_threshold` in this PR — reported at the current config only, per the staged plan; a sweep is a reasonable follow-up if there's interest.

---

# Citation Eval Results

Added by the citation-grounded answers change. Measures whether the inline `[n]` markers in a generated answer actually correspond to passages that were retrieved for that answer. Run over the **same 18 golden items**, unchanged and not re-labelled — `eval/citation_eval.py` reuses the existing `GoldenQAItem.chunk_text` field, so `golden_qa.json` needed no schema change.

## Method

- Each question is run end-to-end through `Lawglance.conversational()` (retrieval **and** generation), unlike the retrieval eval above which skipped the LLM.
- **Each question runs in a fresh session id.** This is required, not incidental: with a shared session, answers are contaminated by a pre-existing multi-turn defect (see note below), and every metric here would be measuring the wrong question's answer.
- Chunk identity is still exact `page_content` string equality, matching the retrieval eval's convention.

## Results

| Metric | Value | What it means |
|---|---|---|
| `citation_validity_rate` | **100%** (all emitted markers) | every `[n]` in an answer resolves to a passage actually retrieved for that answer |
| `answer_citation_coverage` | **94.4%** (17/18) | fraction of questions whose answer carries at least one valid marker |
| `golden_chunk_citation_rate` | **66.7%** (12/18) | fraction of questions where the cited passage is the exact labelled golden chunk — **see failure analysis before reading this as an error rate; the corrected figure is 88.9%** |

**`citation_validity_rate` is the headline number.** Zero fabricated markers across the whole set — no answer ever cited a passage that wasn't in its own retrieved context. This is the property the feature exists to guarantee, and it's structurally enforced (markers are resolved against the retrieved set before display and before caching, so an unmatched marker is stripped rather than shown).

## Failure analysis

**The one coverage gap is the Eleventh Schedule question** — the same item the retrieval eval above misses. It produced zero citations because the golden chunk was never retrieved. That consistency is a good sign: citations fail exactly where retrieval fails, and nowhere else.

**`golden_chunk_citation_rate` should not be read as a 33% error rate.** It requires the model to cite the one specific chunk a human labelled, and chunk boundaries in this corpus overlap. All six non-matching items were checked individually, testing whether the answer string occurs in the labelled chunk, the cited chunk, or both:

| Question | Answer text in labelled chunk | in cited chunk | Assessment |
|---|---|---|---|
| Who appoints the Chief Minister…? | yes | yes | same text in both chunks — citation correct |
| Title of the act amending the Rajasthan Colonisation Act (1984)? | yes | yes | same text in both chunks — citation correct |
| Title of the Tamil Nadu Second Amendment Act of 1974? | yes | yes | same text in both chunks — citation correct |
| Title of the act for West Bengal Act 33 of 1981? | yes | yes | same text in both chunks — citation correct |
| What does the passage include regarding the welfare of labour? | yes | **no** | genuine divergence — see below |
| What topics are in the Eleventh Schedule under Article 243G? | yes | — (no citations) | retrieval miss, not a citation failure |

**Four of the six are boundary artifacts, not errors.** The answer text is physically present in *both* the labelled chunk and the cited one, because ingestion produced overlapping chunks. Three of these four are Ninth Schedule act-title lookups — the Ninth Schedule is a long enumerated list of act names running across several overlapping chunks, so multiple chunks genuinely contain any given entry. Citing either is correct by any reasonable standard.

Counting an answer as correct when the chunk it cites demonstrably contains the answer, the corrected figure is **16/18 (88.9%)**, against 12/18 on strict chunk identity.

**The two real gaps are unrelated to each other:**

1. *Eleventh Schedule* — a retrieval failure, the same item the retrieval eval above misses. No chunk was available to cite.
2. *"What does the passage include regarding the welfare of labour?"* — the model cited Part IV (Directive Principles), while the label is the Seventh Schedule Concurrent List. Both concern labour welfare, but they are different text. The question is phrased relative to a particular passage, so more than one part of the corpus answers it reasonably; it's a candidate for tightening when the set is next revised.

So this metric is best read as a *retrieval-agreement* signal rather than a correctness score. It is reported because it is cheap and reuses existing labels, not because a low value implies bad citations. Both the overlapping-chunk artifact and the question above are worth revisiting when the golden set is next revised — which is also where the suggestion to stratify by source law fits, since the Ninth Schedule skew is what concentrates this ambiguity.

## What these numbers do and don't prove

They prove **every citation points at a passage the model was actually given**. They do **not** prove the cited passage supports the specific claim it's attached to — that is faithfulness, it needs labelled claim/evidence pairs the current golden set doesn't have, and it's out of scope here.

Related and worth stating plainly: answers also mention article numbers ("Article 14", "Article 32") in prose, read out of chunk text. **Those are model-generated and unverified** — only the bracketed `[n]` markers are checked against retrieved passages. The UI states this distinction directly beneath the citations rather than leaving users to assume more grounding than exists.

**Note on the multi-turn defect:** while running this eval, answers in a shared session were found to lag one question behind. This reproduces on unmodified `main` with none of these changes applied — `{input}` is part of `SYSTEM_PROMPT`, and `chains.py` places the system message before `MessagesPlaceholder("chat_history")`. It is pre-existing and out of scope for this change, but it's the reason each eval question uses its own session.
