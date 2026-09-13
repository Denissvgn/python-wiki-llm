"""Offline lexical retrieval with exact identity precedence and visible reasons."""

from __future__ import annotations

import hashlib
import math
import posixpath
import re
import unicodedata
from collections import Counter
from urllib.parse import unquote, urlsplit

RANKING_VERSION = "llm-wiki-search/lexical-v1"
MAX_SEARCH_PAGES = 10_000
MAX_SEARCH_BYTES = 64 * 1024 * 1024
_STOP_WORDS = frozenset(
    "a an and are as at be by for from how in is it of on or the this to with".split()
)
_WORDS = re.compile(r"[^\W_]+", re.UNICODE)
_SYMBOL = re.compile(r"^\|\s*`([\w.]+)`\s*\|", re.MULTILINE)
_LINK = re.compile(r"\]\(([^\s)]+)\)")


def _tokens(text):
    text = unicodedata.normalize("NFKC", text)
    text = re.sub(r"([a-z])([A-Z])", r"\1 \2", text).casefold()
    return [
        word[:-1] if len(word) > 4 and word.endswith("s") else word
        for word in _WORDS.findall(text)
        if word not in _STOP_WORDS
    ]


def rank_pages(
    pages,
    query: str,
    *,
    limit=20,
    max_pages=MAX_SEARCH_PAGES,
    max_bytes=MAX_SEARCH_BYTES,
) -> dict:
    """Consume page records once; retain compact matches and local link counts."""
    if not isinstance(query, str) or not query.strip() or len(query) > 4096:
        raise ValueError("Search query must contain 1–4096 characters")
    if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= 100:
        raise ValueError("Search limit must be between 1 and 100")
    terms = set(_tokens(query))
    needle = unicodedata.normalize("NFKC", query.strip()).casefold()
    matches, identities = [], []
    inbound = Counter()
    scanned_bytes = 0
    for page in pages:
        if len(identities) >= max_pages:
            raise ValueError(
                f"Search exceeds {max_pages} pages; restrict the wiki or kinds"
            )
        content, path = page["content"], page["path"]
        raw = content.encode("utf-8")
        scanned_bytes += len(raw)
        if scanned_bytes > max_bytes:
            raise ValueError(
                f"Search exceeds {max_bytes} UTF-8 bytes; restrict the wiki or kinds"
            )
        digest = hashlib.sha256(raw).hexdigest()
        identities.append((path, digest))
        links = set()
        for link in _LINK.findall(content):
            try:
                parsed = urlsplit(link)
            except ValueError:
                continue
            if parsed.scheme or parsed.netloc or not parsed.path:
                continue
            target = posixpath.normpath(
                posixpath.join(posixpath.dirname(path), unquote(parsed.path))
            )
            if not target.startswith(("../", "/")):
                links.add(target)
        inbound.update(links)
        words = Counter(_tokens(content))
        title = set(_tokens(page["title"]))
        path_terms = set(_tokens(path))
        matched = terms & (words.keys() | title | path_terms)
        exact_id = needle == page["id"].casefold()
        exact_path = needle == path.casefold()
        exact_symbol = needle in {
            symbol.casefold() for symbol in _SYMBOL.findall(content)
        }
        if not (
            exact_id
            or exact_path
            or exact_symbol
            or (terms and len(matched) >= max(1, math.ceil(len(terms) / 2)))
        ):
            continue
        score = 10000 * exact_id + 9000 * exact_path + 5000 * exact_symbol
        reasons = []
        for yes, reason in (
            (exact_id, "exact-page-id"),
            (exact_path, "exact-path"),
            (exact_symbol, "defined-symbol"),
        ):
            if yes:
                reasons.append(reason)
        if terms:
            score += 300 * len(matched) / len(terms)
            score += 60 * len(terms & title) + 30 * len(terms & path_terms)
            score += (
                4
                * sum(math.log1p(words[word]) for word in matched)
                / math.sqrt(1 + sum(words.values()) / 1000)
            )
            reasons.append("lexical:" + ",".join(sorted(matched)))
        if terms & title:
            reasons.append("title-match")
        if terms & path_terms:
            reasons.append("path-match")
        idx = content.casefold().find(needle)
        if idx >= 0:
            score += 20
            reasons.append("exact-phrase")
        else:
            idx = min(
                (
                    content.casefold().find(word)
                    for word in matched
                    if content.casefold().find(word) >= 0
                ),
                default=0,
            )
        start, end = (
            max(0, idx - 70),
            min(len(content), idx + max(len(query), 30) + 100),
        )
        snippet = re.sub(r"\s+", " ", content[start:end]).strip()
        result = {key: value for key, value in page.items() if key != "content"}
        result.update(
            score=score,
            reasons=reasons,
            snippet=snippet,
            provenance={"content_sha256": digest, "ranking": RANKING_VERSION},
        )
        matches.append(result)
    for match in matches:
        count = inbound[match["path"]]
        if count:
            match["score"] += min(10, math.log1p(count))
            match["reasons"].append(f"inbound-wiki-links:{count}")
        match["score"] = round(match["score"], 6)
    matches.sort(
        key=lambda item: (-item["score"], item["path"].casefold(), item["path"])
    )
    identity = hashlib.sha256()
    for path, digest in sorted(identities):
        identity.update(path.encode("utf-8") + b"\0" + digest.encode("ascii") + b"\n")
    total, returned = len(matches), min(len(matches), limit)
    bounds = {"total": total, "returned": returned, "truncated": total > returned}
    return {
        "query": query,
        "mode": "ranked",
        "ranking": RANKING_VERSION,
        "corpus_id": "sha256:" + identity.hexdigest(),
        "scanned": {"pages": len(identities), "bytes": scanned_bytes},
        "resource_limits": {"pages": max_pages, "bytes": max_bytes},
        "total": total,
        "returned": returned,
        "count": returned,
        "truncated": bounds["truncated"],
        "bounds": {"results": bounds},
        "results": matches[:limit],
    }
