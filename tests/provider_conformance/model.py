"""Evidence contracts and comparisons, independent of provider implementation."""

from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass
import hashlib
import json
from pathlib import Path
from typing import Any, Callable


class Incomplete(RuntimeError):
    """A required input/capability cannot establish an assessment result."""


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_json(value: Any) -> bytes:
    return (
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
        + "\n"
    ).encode()


def read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise Incomplete(f"Cannot read JSON input {path}: {error}") from error


def require_hash(path: Path, expected: str) -> None:
    try:
        actual = digest(path.read_bytes())
    except OSError as error:
        raise Incomplete(f"Missing input: {path}") from error
    if actual != expected.removeprefix("sha256:"):
        raise Incomplete(f"Source/artifact provenance changed: {path}")


def require_installed_archive(metadata: dict, expected: str) -> None:
    archive = metadata.get("archive_info", {})
    actual = archive.get("hashes", {}).get("sha256")
    if actual is None and archive.get("hash", "").startswith("sha256="):
        actual = archive["hash"].split("=", 1)[1]
    if actual != expected:
        raise Incomplete("Installed distribution does not match the frozen artifact")


@dataclass(frozen=True)
class Finding:
    fact: str
    representation: str
    status: str
    reason: str
    expected: Any = None
    observed: Any = None
    reference: str | None = None

    def payload(self) -> dict[str, Any]:
        return asdict(self)


def identities(records: list[dict]) -> list[tuple[str, str, str, int]]:
    """Scope and occurrence are part of identity, even for equal spellings."""
    counts: Counter = Counter()
    result = []
    for record in records:
        owner = record.get("owner", "")
        if owner and record.get("owner_occurrence", 1) > 1:
            owner += "#" + str(record["owner_occurrence"])
        key = (owner, record["kind"], record["name"])
        counts[key] += 1
        result.append((*key, counts[key]))
    return result


def compare_sets(
    expected: list[dict], observed: list[dict], *, fact: str, representation: str
) -> list[Finding]:
    if not expected:
        raise Incomplete(f"No required declarations for {fact}")
    left, right = Counter(identities(expected)), Counter(identities(observed))
    if left == right:
        return [
            Finding(
                fact,
                representation,
                "pass",
                "complete-declaration-set",
                list(left),
                list(right),
            )
        ]
    return [
        Finding(
            fact,
            representation,
            "fail",
            "declaration-set-mismatch",
            list((left - right).elements()),
            list((right - left).elements()),
        )
    ]


def compare_value(
    expected: Any,
    observed: Any,
    *,
    field: str,
    language: str,
    normalize: Callable[[str, str, str], Any],
) -> bool:
    if field in {"type", "return_type", "signature"}:
        if expected in (None, "") or observed in (None, ""):
            return expected in (None, "") and observed in (None, "")
        return normalize(language, "type", expected) == normalize(
            language, "type", observed
        )
    if field in {"default", "default_factory"}:
        if expected is None or observed is None:
            return expected is observed
        return normalize(language, "expr", expected) == normalize(
            language, "expr", observed
        )
    return expected == observed


def conclude(findings: list[Finding]) -> dict:
    if not findings:
        raise Incomplete("Empty assessment cannot pass")
    counts = Counter(f.status for f in findings)
    unknown = set(counts) - {
        "pass",
        "fail",
        "blocked",
        "not-applicable",
        "bounded-omission",
    }
    if unknown:
        raise Incomplete(f"Unknown finding status: {sorted(unknown)}")
    if not counts["pass"]:
        raise Incomplete("Assessment has no positive observations")
    return {
        "status": "fail"
        if counts["fail"]
        else "incomplete"
        if counts["blocked"]
        else "pass",
        "counts": dict(sorted(counts.items())),
        "findings": [finding.payload() for finding in findings],
    }
