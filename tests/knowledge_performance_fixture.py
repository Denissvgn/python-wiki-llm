"""Deterministic source/graph corpora for disposable performance qualification."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time

SEED = 260916
TIERS = {"small": (8, 3), "medium": (64, 4), "large": (256, 5)}


def source_corpus(tier):
    owners, functions = TIERS[tier]
    files = {}
    for i in range(owners):
        neighbor = (i + 1) % owners
        lines = [f'"""Owner {i}; fixture seed {SEED}."""', f"import unit_{neighbor:04d} as peer", ""]
        lines += ["def step_0(value=3):", f'    """Owner {i} bounded recursion."""',
                  "    return peer.step_0(value - 1) if value > 0 else 0", ""]
        for j in range(1, functions):
            lines += [f"def step_{j}(value={j}):", "    return step_0(value)", ""]
        lines += [f"class Service{i:04d}:", "    def execute(self, value=2):", "        return step_0(value)", ""]
        files[f"unit_{i:04d}.py"] = "\n".join(lines)
    # Skewed owner and dense fanout, independent of the ring above.
    fanout = min(owners, 128)
    lines = [f"import unit_{i:04d} as owner_{i}" for i in range(fanout)]
    for j in range(8):
        lines += ["", f"def dispatch_{j}(value=2):", "    return (" + " + ".join(
            f"owner_{i}.step_{j % functions}(value)" for i in range(fanout)) + ")"]
    files["hub.py"] = "\n".join(lines) + "\n"
    oracle = {"seed": SEED, "tier": tier, "source_files": owners + 1, "ring_edges": owners,
              "ring_sources": [f"unit_{i:04d}.py" for i in range(owners)],
              "service_names": [f"Service{i:04d}" for i in range(owners)],
              "hub_dispatches": 8, "hub_fanout": fanout, "functions_per_owner": functions,
              "known_call": "unit_0000.step_0 calls unit_0001.step_0 when value > 0"}
    return files, oracle


def generate(work: Path, tier: str, *, governed=False, manifest_heavy=False):
    total_started = time.perf_counter_ns()
    commands = []
    if work.exists() and any(work.iterdir()):
        raise ValueError("fixture directory must be new or empty")
    work.mkdir(parents=True, exist_ok=True)
    source, wiki = work / "source", work / "wiki"
    source.mkdir()
    files, oracle = source_corpus(tier)
    for name, text in files.items():
        (source / name).write_text(text, encoding="utf-8")
    oracle["source_sha256"] = {name: hashlib.sha256(text.encode()).hexdigest() for name, text in files.items()}
    def command(*arguments):
        started = time.perf_counter_ns()
        result = subprocess.run([sys.executable, "-c", "from llm_wiki_cli.cli import main; main()", *arguments],
                                cwd=work, capture_output=True, text=True, timeout=600)
        if result.returncode:
            raise RuntimeError(result.stdout[-4000:] + result.stderr[-4000:])
        measured = {"operation": arguments[0], "wall_ns": time.perf_counter_ns() - started, "emitted_bytes": len(result.stdout.encode())}
        commands.append(measured)
        return measured
    setup = command("bootstrap", "--src-dir", str(source), "--wiki-dir", str(wiki), "--skip-flows", "--skip-workflows", "--knowledge-format", "packed-v3-deflate" )
    # Real authored prose, captured by the owning sync writer.
    page = wiki / "modules/unit_0000.md"
    page.write_text(page.read_text() + "\n## Operator notes\n\nStop recursive work when the value reaches zero.\n")
    command("sync", "--src-dir", str(source), "--wiki-dir", str(wiki), "--jobs", "1", "--no-plugins", "--progress", "never")
    if governed:
        command("knowledge", "init", "--wiki-dir", str(wiki), "--bundle-id", "kb_perf_260916")
        from llm_wiki_cli.services.knowledge_governance import (
            GovernanceAlias, load_governance, save_governance,
        )
        from dataclasses import replace
        ledger = load_governance(wiki).ledger
        aliases = dict(ledger.aliases)
        for number, allocation in enumerate(ledger.concepts.values()):
            for i in range(8):
                alias = GovernanceAlias(allocation.uid, "locator", f"llm-wiki://entities/historic-{number}-{i}")
                aliases[alias.key] = alias
        save_governance(wiki, replace(ledger, aliases=aliases))
        command("sync", "--src-dir", str(source), "--wiki-dir", str(wiki), "--jobs", "1", "--no-plugins", "--progress", "never")
    if manifest_heavy:
        from llm_wiki_cli.services.sync_manifest import SyncManifest
        manifest = SyncManifest.load(wiki)
        for info in manifest.sources.values():
            info["benchmark_notes"] = "large source metadata\n" * 1000
        manifest.save(wiki)
    from llm_wiki_cli.services.knowledge_loader import load_knowledge_state
    validation_started = time.perf_counter_ns()
    state = load_knowledge_state(wiki)
    assert state.knowledge is not None and state.manifest_basis is not None
    titles = {c.title for c in state.knowledge.concepts}
    assert set(oracle["service_names"]) <= titles
    assert set(state.manifest_basis.sources) == set(files)
    assert "Stop recursive work" in page.read_text()
    from llm_wiki_cli.services.contracts import TYPED_GRAPH_EXTENSION_KEY
    graph = state.knowledge.extensions[TYPED_GRAPH_EXTENSION_KEY]
    calls = {(e["from"].get("locator"), e["target"].get("locator")) for e in graph["edges"] if e["kind"] == "calls"}
    for i in range(TIERS[tier][0]):
        assert (f"llm-wiki://modules/unit_{i:04d}", f"llm-wiki://modules/unit_{(i + 1) % TIERS[tier][0]:04d}") in calls
    oracle["verified_ring_calls"] = len(oracle["ring_sources"])
    oracle.update(governed=governed, manifest_heavy=manifest_heavy,
                  setup_commands=commands, total_setup_wall_ns=time.perf_counter_ns() - total_started,
                  final_validation_wall_ns=time.perf_counter_ns() - validation_started,
                  expected_fact_checks=True, setup=setup,
                  concepts=len(state.knowledge.concepts), relationships=len(state.knowledge.relationships),
                  artifacts={name: hashlib.sha256((wiki / name).read_bytes()).hexdigest() for name in
                             (".llm-wiki-knowledge.json", ".llm-wiki-manifest.json", ".llm-wiki-surface.json")})
    (work / "oracle.json").write_text(json.dumps(oracle, indent=2) + "\n")
    return oracle


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--work", type=Path, required=True)
    parser.add_argument("--tier", choices=TIERS, required=True)
    parser.add_argument("--governed", action="store_true")
    parser.add_argument("--manifest-heavy", action="store_true")
    args = parser.parse_args()
    result = generate(args.work.absolute(), args.tier, governed=args.governed, manifest_heavy=args.manifest_heavy)
    print(json.dumps({k: result[k] for k in ("tier", "source_files", "concepts", "relationships", "verified_ring_calls")}))


if __name__ == "__main__":
    main()
