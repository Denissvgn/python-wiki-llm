"""Replay the small credential-free acceptance manifest with existing pytest cases."""

import argparse
import json
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "tests/fixtures/qualified-context-acceptance.json"
CORPORA = frozenset({"fx-path-policy", "fx-stale-evidence", "fx-same-owner-receipt"})


def load_manifest():
    def require(condition, message):
        if not condition:
            raise ValueError(message)
    if MANIFEST.stat().st_size > 128 * 1024:
        raise ValueError("Acceptance manifest exceeds its bound.")
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    require(data["schema_version"] == "llm-wiki-qualified-context-acceptance/v1", "Unsupported corpus manifest.")
    require(data["evidence_kind"] == "synthetic-regression-cases", "Corpus evidence must be synthetic.")
    require(len(data["corpora"]) == 3 and {group["id"] for group in data["corpora"]} == CORPORA, "Expected all three named corpora.")
    seen = set()
    for group in data["corpora"]:
        require(0 < len(group["cases"]) <= 64, "Corpus case count is outside its bound.")
        for case in group["cases"]:
            require(re.fullmatch(r"[a-z][a-z0-9-]{0,79}", case["id"]), "Invalid corpus case ID.")
            require(case["id"] not in seen, "Duplicate corpus case ID.")
            seen.add(case["id"])
            require(case["old_assumption"] and case["expected"], "Each case needs its former assumption and expected outcome.")
            path = ROOT / case["test"].split("::", 1)[0]
            require(path.resolve().is_relative_to(ROOT / "tests"), "Corpus target must be inside tests.")
            require(path.suffix == ".py" and path.is_file(), "Corpus target must name an existing Python module.")
    return data


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus", choices=sorted(CORPORA), action="append")
    parser.add_argument("--junitxml", type=Path)
    args = parser.parse_args()
    selected = set(args.corpus or CORPORA)
    manifest = load_manifest()
    selectors = list(dict.fromkeys(
        case["test"] for group in manifest["corpora"] if group["id"] in selected
        for case in group["cases"]
    ))
    import pytest
    options = ["-q", "-p", "no:cacheprovider", "--strict-config", "--strict-markers",
               "-W", "error", "-o", "xfail_strict=true", "--rootdir", str(ROOT)]
    if args.junitxml:
        options.append(f"--junitxml={args.junitxml}")
    raise SystemExit(pytest.main([*selectors, *options]))


if __name__ == "__main__":
    main()
