"""Matplotlib gallery retrieval (RAG) for prompt grounding.

This module retrieves a small number of relevant Matplotlib gallery examples
and provides a sanitized code snippet for prompt injection.

The goal is to improve LLM reliability by grounding generation in known-good
gallery patterns while keeping the prompt small and safe.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Sequence, Set

from gallery_loader import get_gallery_loader


_TOKEN_PATTERN = re.compile(r"[a-z0-9]+")

_STOPWORDS: Set[str] = {
    "a",
    "an",
    "and",
    "as",
    "at",
    "based",
    "by",
    "create",
    "data",
    "demo",
    "do",
    "draw",
    "example",
    "for",
    "from",
    "how",
    "i",
    "in",
    "it",
    "me",
    "my",
    "of",
    "on",
    "or",
    "plot",
    "please",
    "show",
    "the",
    "this",
    "to",
    "using",
    "with",
}


@dataclass(frozen=True)
class RetrievedExample:
    """A retrieved gallery example suitable for prompt injection."""

    title: str
    filename: str
    category: str
    code: str
    score: float


def gallery_rag_enabled() -> bool:
    """Return True if gallery RAG injection is enabled."""
    mode = os.getenv("PLOT_GALLERY_RAG_MODE", "auto").strip().lower()
    return mode not in {"off", "0", "false", "disabled"}


def retrieve_gallery_examples(query: str, limit: int = 3) -> List[RetrievedExample]:
    """Retrieve up to `limit` relevant Matplotlib gallery examples for a query."""
    normalized_query = " ".join((query or "").strip().lower().split())
    if not normalized_query:
        return []

    loader = get_gallery_loader()
    examples = loader.get_all_examples()
    query_tokens = _tokenize(normalized_query)
    if not query_tokens:
        return []

    scored: List[RetrievedExample] = []
    for example in examples:
        title = str(example.get("title", "") or "")
        filename = str(example.get("filename", "") or "")
        category = str(example.get("category", "") or "")
        code = str(example.get("code", "") or "")

        score = _score_example(normalized_query, query_tokens, title, filename)
        if score <= 0:
            continue

        sanitized_code = sanitize_gallery_code_for_prompt(code)
        if not sanitized_code:
            continue

        scored.append(
            RetrievedExample(
                title=title,
                filename=filename,
                category=category,
                code=sanitized_code,
                score=score,
            )
        )

    scored.sort(key=lambda item: item.score, reverse=True)
    return scored[: max(0, limit)]


def sanitize_gallery_code_for_prompt(
    code: str, max_lines: int = 120, max_chars: int = 6000
) -> str:
    """Reduce a gallery code sample to a compact, prompt-safe snippet."""
    if not code.strip():
        return ""

    lines = code.splitlines()
    output: List[str] = []

    in_docstring = False
    doc_delimiter: Optional[str] = None

    for raw_line in lines:
        line = raw_line.rstrip("\n")
        stripped = line.strip()

        if not in_docstring and (stripped.startswith('"""') or stripped.startswith("'''")):
            doc_delimiter = stripped[:3]
            if stripped.count(doc_delimiter) >= 2:
                continue
            in_docstring = True
            continue

        if in_docstring:
            if doc_delimiter and doc_delimiter in stripped:
                in_docstring = False
                doc_delimiter = None
            continue

        if stripped.startswith("import ") or stripped.startswith("from "):
            continue
        if "plt.show(" in stripped or stripped == "plt.show()":
            continue
        if "sphinx_gallery_thumbnail_number" in stripped:
            continue
        if stripped.startswith("# %%"):
            continue
        if stripped.startswith("# .."):
            continue

        output.append(line)
        if len(output) >= max_lines:
            break

    rendered = "\n".join(output).strip()
    if not rendered:
        return ""

    if len(rendered) > max_chars:
        rendered = f"{rendered[:max_chars].rstrip()}\n# ... truncated"
    return rendered


def _tokenize(text: str) -> Set[str]:
    tokens = {token for token in _TOKEN_PATTERN.findall(text.lower()) if token}
    return {token for token in tokens if token not in _STOPWORDS and len(token) >= 2}


def _score_example(
    normalized_query: str,
    query_tokens: Set[str],
    title: str,
    filename: str,
) -> float:
    title_lower = title.lower()
    filename_lower = filename.lower()

    title_tokens = _tokenize(title_lower)
    filename_tokens = _tokenize(filename_lower)

    overlap_title = len(query_tokens & title_tokens)
    overlap_filename = len(query_tokens & filename_tokens)

    score = 0.0
    if normalized_query and normalized_query in title_lower:
        score += 12.0

    score += overlap_title * 3.0
    score += overlap_filename * 1.0

    if "error" in query_tokens and "error" in title_tokens:
        score += 2.0
    if "band" in query_tokens and "band" in title_tokens:
        score += 2.0

    return score

