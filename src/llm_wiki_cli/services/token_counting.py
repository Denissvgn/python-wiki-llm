"""Trusted host counters. No repository-discovered code or network loading."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Protocol


class TokenCounter(Protocol):
    identity: str
    exact: bool

    def count(self, text: str) -> int: ...


class EstimatedCounter:
    identity = "utf8-ceil-div4/v1"
    exact = False

    def count(self, text: str) -> int:
        return (len(text.encode("utf-8")) + 3) // 4


class LocalTokenizerCounter:
    """Count raw text using immutable local tokenizer JSON, without framing."""

    exact = True

    def __init__(self, path: str | Path):
        try:
            import tokenizers
        except ImportError as exc:
            raise ValueError("Exact counting needs agent-wiki-cli[tokens] installed.") from exc
        raw = Path(path).read_bytes()
        self._tokenizer = tokenizers.Tokenizer.from_str(raw.decode("utf-8"))
        # Saved truncation must never hide overflow; padding is not raw text.
        self._tokenizer.no_truncation()
        self._tokenizer.no_padding()
        digest = hashlib.sha256(raw).hexdigest()
        self.identity = f"tokenizers/{tokenizers.__version__}:sha256:{digest}:raw-v1"

    def count(self, text: str) -> int:
        return len(self._tokenizer.encode(text, add_special_tokens=False).ids)
