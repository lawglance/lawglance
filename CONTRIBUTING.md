# Contributing to LawGlance

Thanks for your interest in contributing! This doc covers how to get set up, what we expect from a PR, and how review works.

## Getting started

```bash
git clone https://github.com/<your-fork>/lawglance.git
cd lawglance
uv sync
```

Copy `.env.example` to `.env` and fill in your own API key:

```bash
cp .env.example .env
```

Never commit `.env` — it's gitignored.

## Running tests

```bash
uv run pytest tests/ -v
```

All PRs must pass CI (tests + lint + secret scan) before merge. Please run tests locally before opening a PR.

## Before you open a PR

- **Check open issues first.** If you're planning a non-trivial change, open or comment on an issue describing what you want to do before writing code. This avoids duplicated work and lets us flag scope issues early.
- **Keep PRs focused.** One logical change per PR. If your change touches multiple unrelated things, split it up.
- **Know what's in scope.** Current roadmap and staged priorities are tracked in the issues (see #15 for the retrieval → citations → groundedness guardrail staging, for example). If your PR doesn't map to an open issue or discussion, expect it to take longer to review or be asked to open an issue first.

## PR expectations

Every PR should include:
- **What it does** — a clear description of the change
- **What it doesn't do** — explicit non-goals, especially if it's part of a larger staged effort
- **Test plan** — what you tested, how, and any results (screenshots, eval numbers, etc. where relevant)
- **Related issues** — link with `Related to #N` or `Closes #N`

Use the PR template — it'll pre-fill these sections for you.

## Scope guidelines

- Changes to production code paths (`chains.py`, `prompts.py`, `lawglance_main.py`) get closer scrutiny than eval-only, docs-only, or test-only additions. Call out clearly in your PR description if you touched any of these files and why.
- New dependencies should be justified in the PR description — we keep the dependency footprint intentionally lean.
- No API keys, credentials, or secrets in any commit, including in test fixtures or example configs. Use placeholders.

## Review process

- We aim to give an initial response within a few days. If it's been longer, a polite nudge on the PR is completely fine.
- CI must pass (tests, lint, secret scan) before we'll merge.
- At least one maintainer approval is required.
- We default to squash-merge to keep `main` history clean, so don't worry about tidying up your commit history — just make sure each commit message is informative in case we need to reference it later.

## Code style

We use `ruff` for linting and formatting:

```bash
uv run ruff check .
uv run ruff format .
```

## Questions

Open a discussion or comment on the relevant issue. Thanks again for contributing!