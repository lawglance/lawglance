# Contributing to LawGlance

LawGlance answers legal questions for people who often have nowhere else to ask. That shapes how we build: an answer that sounds right but isn't grounded in the statute is worse than no answer at all. Everything below follows from that.

First time here? The fastest way in is to [open an issue](https://github.com/lawglance/lawglance/issues) describing a question the assistant got wrong, with the question text and what it should have said. That's a genuinely useful contribution and needs no setup.

- [Ways to contribute](#ways-to-contribute)
- [Quick start](#quick-start)
- [How the project fits together](#how-the-project-fits-together)
- [Conversation state](#conversation-state)
- [Development workflow](#development-workflow)
- [The bar for changes that affect answers](#the-bar-for-changes-that-affect-answers)
- [Opening a pull request](#opening-a-pull-request)
- [Review process](#review-process)
- [Security and secrets](#security-and-secrets)
- [Responsible use](#responsible-use)
- [Community](#community)

## Ways to contribute

| | |
| --- | --- |
| **Report a bad answer** | The highest-value bug report in this project. Include the question, the answer you got, and the provision you expected. No setup needed. |
| **Expand legal coverage** | New statutes mean new ingestion and a new slice of the golden set. Open an issue first — corpus changes affect every answer. |
| **Improve retrieval or the agent** | Changes under `backend/` are held to the eval bar described below. |
| **Strengthen the evals** | The golden set is 18 human-verified items. Growing it carefully is one of the most useful things anyone can do here. |
| **Docs and onboarding** | If something in this file was wrong or confusing, fixing it counts. |

Please comment on an issue before starting non-trivial work, so two people don't build the same thing.

## Quick start

**Prerequisites:** Python 3.11, [uv](https://docs.astral.sh/uv/), an OpenAI API key, and Redis (see below).

```bash
git clone https://github.com/lawglance/lawglance.git
cd lawglance
uv sync
```

Create a `.env` file in the repo root with your key:

```bash
OPENAI_API_KEY=sk-your-key-here
```

Then start the app:

```bash
uv run streamlit run app.py     # http://127.0.0.1:8501
```

**Redis is required to run the app.** It stores the chat transcript the UI replays and the cached answers. The Python client connects lazily, so a missing Redis doesn't fail at startup — it fails on your first question with a connection error, which is a confusing first five minutes if you don't know to expect it.

```bash
docker run -d --name lawglance-redis -p 6379:6379 redis:7
redis-cli ping    # PONG
```

Plain Redis 6 or 7 is fine; we use only ordinary key and list commands. That would change if the LangGraph checkpointer ever moves onto Redis, which needs the RedisJSON and RediSearch modules — built into Redis 8, otherwise Redis Stack.

### Environment variables

| Variable | Default | Used for |
| --- | --- | --- |
| `OPENAI_API_KEY` | — | chat model and embeddings |
| `REDIS_URL` | `redis://localhost:6379/0` | chat transcript and answer cache |
| `CACHE_TTL` | `3600` | seconds a cached answer stays valid |

One wart to know about: the app and backend call `load_dotenv()`, which reads `.env`, while the modules under `eval/` call `load_dotenv(".env.local")`. If you plan to run evals, put your key in **both** files. Unifying this is a good first PR. Both filenames are gitignored — never commit either.

### Running the API instead of the UI

```bash
uv run uvicorn backend.main:app --reload
curl "http://127.0.0.1:8000/query?query=What+is+Article+21%3F"
```

## How the project fits together

```
app.py                       Streamlit chat UI — the live entry point
backend/                     the agentic pipeline everything user-facing runs through
  retrieval.py                 agent_invoke() — the public entry point
  graph.py, nodes.py           the LangGraph loop: llm_call -> tool_node -> final_answer
  tools.py                     retrieve_docs, the only tool the agent can call
  config.py                    model, embeddings, vector store, Redis, checkpointer
  cache.py, citation.py        thin wrappers over the root-level modules
  main.py                      optional FastAPI wrapper over the same agent
citations.py                 citation numbering, labelling, and answer resolution
eval/                        retrieval and citation evals, plus the golden QA set
tests/                       unit tests (no network, no Redis, no API key)
chroma_db_legal_bot_part1/   the ingested corpus, committed to the repo
src/                         the ingestion notebook that rebuilds that corpus
config/prompts.yaml          prompts for the legacy chain
lawglance_main.py,
chains.py, prompts.py        the original single-chain RAG pipeline
```

Two things commonly trip people up.

**There are two pipelines, and only one is live.** `app.py` runs against `backend/`. The original chain (`lawglance_main.py`, `chains.py`) is kept for reference and is still what parts of `eval/` measure. If you change retrieval behaviour, be explicit about which pipeline you changed.

**The vector store is a committed binary.** Merely running the app touches `chroma_db_legal_bot_part1/chroma.sqlite3`, so it will show up as modified in `git status`. Don't commit that noise — run `git checkout -- chroma_db_legal_bot_part1/` before you stage. Real corpus changes are a deliberate, separately-discussed PR.

## Conversation state

The backend keeps conversation state in two places, and they are not interchangeable:

- **The LangGraph checkpointer** (`memory` in `backend/config.py`) is the agent's memory. Every `agent_invoke` call passes `{"configurable": {"thread_id": session_id}}`, and the checkpointer reloads that thread's state before the graph runs.
- **Redis** (`backend/cache.py`) holds the transcript the UI replays on rerun, plus the answer cache. It is a record of the conversation, not the agent's working memory.

Three things are easy to get wrong here:

- **Pass only the new message to `agent.invoke`.** The `messages` channel in `backend/state.py` reduces with `operator.add`, so re-sending the stored transcript appends it a second time and the thread grows on every turn.
- **The compiled graph is a module-level singleton** in `backend/retrieval.py`. `compile()` holds no per-conversation state — the `thread_id` selects it — so don't rebuild the graph per request.
- **`thread_id` is mandatory** once a checkpointer is attached. A `configurable` without it fails inside the checkpointer with `KeyError: 'thread_id'`.

Known gaps, if you're looking for something to pick up (claim an issue first):

- `MemorySaver` is process-local, so agent memory is lost on restart while the Redis transcript survives. A durable checkpointer — SQLite locally, Redis or Postgres for multi-process deployments — is the fix.
- The answer cache is keyed by question text alone, shared across sessions, and returns before the graph runs. A follow-up question can hit another conversation's entry, and a cache hit never reaches the thread.
- `final_answer` in `backend/nodes.py` builds its context and citations from every turn in state, and citation numbering restarts on each tool call, so numbers can collide across turns.
- Nothing trims or summarises message history, and threads are never evicted.

## Development workflow

Branch from `main`, and keep one logical change per branch.

```bash
uv run pytest tests/ -v              # unit tests
uv run ruff check .                  # lint
uv run ruff format .                 # format
```

The test suite is pure unit tests — no Redis, no API key, no network — which is why CI runs it with no services. Please keep it that way: stub external calls rather than adding a service to CI. If you touch `citations.py`, `eval/`, or anything else already covered, add cases alongside the existing ones.

CI runs on every PR: tests, `ruff check .`, `ruff format --check .`, a gitleaks secret scan, and CodeQL. Run the first three locally before pushing — at minimum over the files you touched.

## The bar for changes that affect answers

Retrieval quality, prompts, and the agent loop are measured, not argued about. `eval/RESULTS.md` records the current numbers: Recall@10 of 94.4% and MRR of 0.789 over 18 human-verified golden questions.

If your change could move those numbers, report them before and after, and say which pipeline you measured. Two caveats, both documented in `eval/RESULTS.md`:

- **n=18 is a directional signal.** The 95% confidence interval on Recall@10 spans roughly 25 points. It will catch a gross regression; it will not tell you whether 94% became 96%.
- **Scoring is exact `page_content` string equality**, because the pinned `langchain-chroma` doesn't expose a stable chunk id on retrieval. Chunking changes therefore invalidate comparisons against previously recorded results.

Answers must stay grounded. Every claim in a generated answer should trace to a retrieved passage, inline `[n]` markers must resolve to passages actually retrieved for that answer, and markers the retrieval never supported are stripped rather than shown. A change that makes the model more fluent but less traceable will not be merged.

## Opening a pull request

Use the PR template — it pre-fills the sections below.

- **What it does** — the change, and the issue it relates to (`Related to #N`, `Closes #N`).
- **What it doesn't do** — explicit non-goals, especially for one step of a staged effort.
- **Production code path** — say plainly whether you touched the live request path (`app.py`, `backend/`, `chains.py`, `prompts.py`, `lawglance_main.py`) and what the behaviour change is. If you touched memory or caching, describe what happens on a follow-up question and after an app restart; those are the two paths that break quietly.
- **Test plan** — what you ran and what you saw, including eval numbers where relevant.
- **New dependencies** — justified in the description. We keep the footprint deliberately lean.

Keep PRs focused. A large diff that mixes a bug fix, a refactor, and a new feature takes far longer to review than the same work split into three.

## Review process

- We aim to respond within a few days. If it has been longer, a polite nudge on the PR is completely fine.
- One maintainer approval and green CI are required to merge.
- We squash-merge, so don't worry about tidying your commit history — just keep each message informative.
- Review comments are about the code, not about you. If feedback reads as terse, assume brevity rather than hostility, and feel free to push back with reasoning.

## Security and secrets

No API keys, credentials, or personal data in any commit — including test fixtures and example configs. Use placeholders. The gitleaks job catches most mistakes, but it is a backstop, not a substitute for reading your own diff.

Found a vulnerability? Please don't open a public issue. Report it privately through this repository's [security advisories](https://github.com/lawglance/lawglance/security/advisories).

## Responsible use

LawGlance provides legal *information*, not legal advice, and it is still in a pilot phase. Please don't remove or weaken the in-app disclaimers, don't add features that present output as a substitute for a lawyer, and be careful about the provenance of any legal text added to the corpus.

Statutory text is the backbone of this project; commentary, headnotes, and third-party annotations often are not freely licensed. If you are adding sources, say in the PR where they came from and under what terms.

## Community

Be kind, assume good faith, and keep discussion focused on the work. Many contributors here are early in their careers or new to open source; a patient answer costs little and is often what keeps someone contributing. Harassment or demeaning behaviour is not welcome and will be acted on by the maintainers.

Questions? Open a discussion or comment on the relevant issue. Thanks for helping make legal knowledge more accessible.
