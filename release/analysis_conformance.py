"""Capture focused installed observations on the existing native owner lanes."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import platform
import sys
import tempfile


def capture(fixture_path: Path, output: Path, helper_cache_dir: str) -> dict:
    from llm_wiki_cli import __version__
    from llm_wiki_cli.services.extraction_service import get_inventory_result
    from llm_wiki_cli.services.knowledge_evidence import normalize_module_observation

    raw = fixture_path.read_bytes()
    fixture = json.loads(raw)
    with tempfile.TemporaryDirectory(prefix="analysis-conformance-") as directory:
        for name, content in fixture["sources"].items():
            path = Path(directory) / name
            if path.parent != Path(directory):
                raise ValueError("conformance fixtures require flat source paths")
            path.write_bytes(content.encode("utf-8"))
        result = get_inventory_result(directory, deep=True, include_plugins=False,
                                      helper_cache_dir=helper_cache_dir)
    observations = {name: normalize_module_observation(value) for name, value in result.inventory.items()}
    if observations != fixture["observations"]:
        raise ValueError("installed native observations differ from the frozen fixture")
    components = result.analysis_components
    languages = set()
    for row in observations.values():
        if row is None:
            raise ValueError("native fixture contains an unsupported observation")
        languages.add(row["language"])
    if not components or not {"agent-wiki-cli", *("llm-wiki/extractor/" + language for language in languages)} <= components.keys():
        raise ValueError("native observation capture is missing required analysis identities")
    record = {
        "schema_version": "llm-wiki-analysis-conformance/v1", "status": "pass",
        "python": list(sys.version_info[:2]), "platform": sys.platform,
        "machine": platform.machine(), "producer_version": __version__,
        "fixture_sha256": hashlib.sha256(raw).hexdigest(),
        "observations": observations, "components": components,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return record


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixture", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--helper-cache-dir", required=True)
    args = parser.parse_args()
    capture(args.fixture, args.output, args.helper_cache_dir)


if __name__ == "__main__":
    main()
