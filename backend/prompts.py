"""Prompts for the agentic backend.

Shared with the original Lawglance pipeline, so this module re-exports the
canonical prompts from the top-level `prompts` module instead of duplicating
them.
"""

from prompts import SYSTEM_PROMPT, QA_PROMPT

__all__ = ["SYSTEM_PROMPT", "QA_PROMPT"]
