"""Installed public consumer: project isolation and native compatibility states."""

import json
from pathlib import Path
import shutil
import subprocess
import sys

from llm_wiki_cli import api


root = Path.cwd() / "provider-consumer"
root.mkdir()
origin = Path(api.__file__).resolve()
assert origin.is_relative_to(Path(sys.prefix).resolve())
assert (origin.parent / "py.typed").is_file()
cwd = Path.cwd()


def tree(directory):
    return {
        path.relative_to(directory).as_posix(): (path.read_bytes(), path.stat().st_mode)
        for path in directory.rglob("*")
        if path.is_file()
    }


def inspect(source, wiki, target, *, live=False):
    return api.inspect_concept(
        target, src_dir=str(source), wiki_dir=str(wiki), live=live
    )


projects = {}
for name, symbol, annotation in (("A", "Alpha", "int"), ("B", "Beta", "str")):
    project = root / name
    source = project / "src"
    wiki = project / "wiki"
    source.mkdir(parents=True)
    (source / "model.py").write_text(
        f"raise RuntimeError('target application must not execute')\n\nclass {symbol}:\n    value: {annotation}\n",
        encoding="utf-8",
    )
    api.bootstrap_wiki(str(source), str(wiki))
    projects[name] = (source, wiki, f"llm-wiki://entities/{symbol}")
    assert not (project / "AGENTS.md").exists()

before = tree(root)
packets = {}
for name, (source, wiki, target) in projects.items():
    report = inspect(source, wiki, target, live=True)
    assert report["schema_version"] == api.NATIVE_INSPECTION_SCHEMA_VERSION
    assert report["coverage"]["schema_version"] == api.KNOWLEDGE_COVERAGE_SCHEMA_VERSION
    assert report["concept"]["found"] is True
    assert report["coverage"]["counts"] is not None
    assert (
        report["coverage"]["counts"]["modeled"]
        == report["coverage"]["counts"]["compared"]
        == 2
    )
    other = projects["B" if name == "A" else "A"][2]
    assert inspect(source, wiki, other)["concept"]["found"] is False
    service = api.build_documentation_query_service(str(source), wiki_dir=str(wiki))
    assert api.get_concept(target, service=service)["found"] is True
    assert api.get_concept(other, service=service)["found"] is False
    for mode in (None, "off", "auto", "required"):
        request = {
            "budget_tokens": 4000,
            "focus": ["all"],
            "format": "json",
            "filters": {},
        }
        if mode is not None:
            request["knowledge_mode"] = mode
        packet = api.build_qualified_context(
            str(source), wiki_dir=str(wiki), request=request
        )
        payload = packet.to_payload()
        assert (
            payload["schema_version"]
            == f"llm-wiki-qualified-context-packet/v{1 if mode is None else 2}"
        )
        validated = api.validate_context_packet(packet.to_bytes())
        assert validated.valid and not validated.freshness_evaluated
        assert (
            api.reconcile_context_packet(
                packet.to_bytes(), str(source), wiki_dir=str(wiki)
            ).current
            is True
        )
        packets[name, mode] = packet.to_bytes()
assert packets["A", "auto"] != packets["B", "auto"]
assert tree(root) == before and Path.cwd() == cwd

source_a, wiki_a, target_a = projects["A"]
source_b, wiki_b, target_b = projects["B"]
(source_a / "model.py").write_text("class Alpha:\n    value: float\n", encoding="utf-8")
assert (
    api.reconcile_context_packet(
        packets["A", "auto"], str(source_a), wiki_dir=str(wiki_a)
    ).current
    is False
)
assert (
    api.reconcile_context_packet(
        packets["B", "auto"], str(source_b), wiki_dir=str(wiki_b)
    ).current
    is True
)
source_a.rename(source_a.with_name("offline-source"))
snapshot = inspect(source_a, wiki_a, target_a)
assert snapshot["concept"]["found"] is True
assert snapshot["coverage"]["freshness_evaluated"] is False
try:
    inspect(source_a, wiki_a, target_a, live=True)
except api.WorkspaceStateError as error:
    assert error.code == "workspace-state-error" and error.details == {
        "field": "src_dir"
    }
    assert str(root) not in str(error)
else:
    raise AssertionError("missing live source was accepted")

states = {}
for case in ("corrupt-knowledge", "unsupported", "corrupt-surface"):
    wiki = root / case
    shutil.copytree(wiki_b, wiki)
    if case == "corrupt-knowledge":
        (wiki / ".llm-wiki-knowledge.json").write_text("{broken", encoding="utf-8")
    elif case == "unsupported":
        path = wiki / ".llm-wiki-knowledge.json"
        payload = json.loads(path.read_text(encoding="utf-8"))
        payload["schema_version"] = "llm-wiki-knowledge/v999"
        path.write_text(json.dumps(payload), encoding="utf-8")
    else:
        (wiki / ".llm-wiki-surface.json").write_text("{broken", encoding="utf-8")
    frozen = tree(wiki)
    try:
        result = inspect(source_b, wiki, target_b)
    except api.ArtifactIntegrityError as error:
        assert case == "corrupt-surface"
        assert error.code == "artifact-integrity-error" and error.details == {
            "field": "wiki_dir"
        }
        assert str(root) not in str(error)
        states[case] = error.code
    else:
        expected = "degraded" if case == "corrupt-knowledge" else "unsupported"
        assert result["coverage"]["availability"] == expected
        assert result["coverage"]["counts"] is None
        assert result["concept"]["found"] is False
        states[case] = expected
    assert tree(wiki) == frozen

assert Path.cwd() == cwd
before_export = tree(wiki_b)
for surface, destination in (("site", "--out-dir"), ("obsidian", "--vault-dir")):
    options = [
        "--wiki-dir",
        str(wiki_b),
        destination,
        str(root / (surface + "-output")),
        "--knowledge-metadata",
        "summary",
        "--knowledge-profile",
        "public-portable",
    ]
    for operation in ("export", "check"):
        completed = subprocess.run(
            [
                sys.executable,
                "-X",
                "utf8",
                "-I",
                "-m",
                "llm_wiki_cli.cli",
                surface,
                operation,
                *options,
            ],
            capture_output=True,
            timeout=60,
        )
        assert completed.returncode == 0, completed.stderr.decode(errors="replace")
assert tree(wiki_b) == before_export
print(
    json.dumps(
        {
            "schema_version": "provider-consumer-check/v1",
            "projects": 2,
            "isolated_in_one_process": True,
            "application_execution": False,
            "offline_snapshot": True,
            "ungoverned_exports": True,
            "packet_modes": ["omitted", "off", "auto", "required"],
            "states": states,
        },
        sort_keys=True,
    )
)
