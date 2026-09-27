"""The compatibility qualification cannot pass on missing or rebound evidence."""

import hashlib
import io
import json
from pathlib import Path
import tarfile
import zipfile

import pytest

from release import qualification as q
from llm_wiki_cli.services import analysis_compatibility as ac


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")


@pytest.fixture
def compatibility_bundle(tmp_path):
    source = tmp_path / "evidence/RD-00/source"
    source.mkdir(parents=True)
    source_bytes = b"VALUE = 1\n"
    fixture_bytes = json.dumps({"observations": {"model.py": {"classes": []}}}).encode()
    registry = {
        "shared": ["core.py"], "providers": {"python": ["core.py"], "typescript": ["core.py"]},
        "portable_python_profiles": [["linux", 3, 10, "x86_64"], ["linux", 3, 13, "x86_64"],
                                     ["darwin", 3, 14, "arm64"], ["win32", 3, 13, "amd64"]],
        "portable_helper_toolchains": {"typescript": "node v24.18.0; npm 11.16.0"},
    }
    files = {
        "src/llm_wiki_cli/services/analysis_contracts.json": json.dumps(registry).encode(),
        "src/llm_wiki_cli/core.py": source_bytes,
        "src/llm_wiki_cli/extractors/python_extractor.py": source_bytes,
        "tests/fixtures/analysis-portability.json": fixture_bytes,
        "tests/fixtures/analysis-helper-portability.json": fixture_bytes,
    }
    with tarfile.open(source / "candidate-source.tar", "w") as archive:
        for name, raw in files.items():
            info = tarfile.TarInfo(name)
            info.size = len(raw)
            archive.addfile(info, io.BytesIO(raw))
    write(source / "identity.json", {"version": "1.2.3"})
    hashes = {"core.py": hashlib.sha256(source_bytes).hexdigest()}
    implementation = "sha256:" + hashlib.sha256(json.dumps(hashes, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    portable = {"profile": "qualified-python-observations/v1"}
    components = {"agent-wiki-cli": {"implementation": implementation, "runtime": ac.digest(portable)}}
    for language in ("python", "typescript", "javascript"):
        helper = "" if language == "python" else "node v24.18.0; npm 11.16.0; active-node v24.18.0"
        components["llm-wiki/extractor/" + language] = {"implementation": implementation,
            "runtime": ac.digest({"python": portable, "helper": helper, "dependencies": {}})}
    for path, platform, version, machine in (
        ("RD-01/ubuntu/core-ubuntu-3.10-analysis.json", "linux", [3, 10], "x86_64"),
        ("RD-01/macos/core-macos-3.14-analysis.json", "darwin", [3, 14], "arm64"),
        ("RD-01/windows/core-windows-3.13-analysis.json", "win32", [3, 13], "AMD64"),
        ("RD-07/toolchains/analysis-python.json", "linux", [3, 13], "x86_64"),
        ("RD-07/toolchains/analysis-helpers.json", "linux", [3, 13], "x86_64"),
        ("RD-01/macos/core-macos-3.14-helpers.json", "darwin", [3, 14], "arm64"),
    ):
        write(tmp_path / "evidence" / path, {
            "schema_version": "llm-wiki-analysis-conformance/v1", "status": "pass",
            "platform": platform, "python": version,
            "machine": machine,
            "fixture_sha256": hashlib.sha256(fixture_bytes).hexdigest(),
            "observations": json.loads(fixture_bytes)["observations"],
            "components": components,
        })
    pairs = tmp_path / "evidence/RD-10/analysis"
    rows = []
    for name, version, mutated in (("baseline", "1.2.3", False), ("version-only", "1.2.3.post1", False),
                                   ("same-version-analysis-change", "1.2.3", True), ("new-version-analysis-change", "1.2.3.post1", True)):
        wheel = pairs / name / "dist" / ("agent_wiki_cli-" + version + "-py3-none-any.whl")
        wheel.parent.mkdir(parents=True)
        with zipfile.ZipFile(wheel, "w") as archive:
            archive.writestr("llm_wiki_cli/extractors/python_extractor.py", source_bytes + (b"\n# Controlled analysis implementation mutation.\n" if mutated else b""))
        state = "unhealthy" if mutated else "healthy"
        report = pairs / (name + "-doctor.json")
        write(report, {"schema_version": "llm-wiki-doctor/v4", "status": state,
            "health_details": {"basis": {"recorded": {"tool": {"version": "1.2.3"}}, "live": {"tool": {"version": version}}}}})
        row = {"name": name, "version": version, "status": state,
               "wheel_sha256": q.sha256_file(wheel), "report_sha256": q.sha256_file(report)}
        for kind in ("native", "mcp"):
            path = Path(str(report) + "." + kind + ".json")
            write(path, {"counts": {"modeled": 2, "modeled_freshness": {"current": 0 if mutated else 2}}})
            row[kind + "_sha256"] = q.sha256_file(path)
        rows.append(row)
    write(pairs / "result.json", {"schema_version": "llm-wiki-installed-analysis-pairs/v1", "status": "pass",
                                 "cases": rows, "commands": [{"exit": 0}] * 13})
    return tmp_path


@pytest.mark.parametrize("mutation", ["none", "missing-native", "wrong-observations", "wrong-runtime", "wrong-machine", "copied-runtime", "missing-helper", "missing-linux313", "missing-pairs", "wrong-wheel", "copied-result", "missing-mcp"])
def test_combined_compatibility_evidence_is_required(compatibility_bundle, mutation):
    root = compatibility_bundle
    native = root / "evidence/RD-01/ubuntu/core-ubuntu-3.10-analysis.json"
    pairs = root / "evidence/RD-10/analysis"
    if mutation == "missing-native":
        native.unlink()
    if mutation in {"wrong-observations", "wrong-runtime"}:
        data = json.loads(native.read_text())
        data["observations" if mutation == "wrong-observations" else "python"] = {}
        write(native, data)
    if mutation in {"wrong-machine", "copied-runtime"}:
        data = json.loads(native.read_text())
        if mutation == "wrong-machine":
            data["machine"] = "aarch64"
        else:
            data["components"]["llm-wiki/extractor/python"]["runtime"] = "sha256:" + "0" * 64
        write(native, data)
    if mutation == "missing-helper":
        (root / "evidence/RD-01/macos/core-macos-3.14-helpers.json").unlink()
    if mutation == "missing-linux313":
        (root / "evidence/RD-07/toolchains/analysis-python.json").unlink()
    if mutation == "missing-pairs":
        (pairs / "result.json").unlink()
    if mutation == "wrong-wheel":
        next((pairs / "version-only/dist").glob("*.whl")).write_bytes(b"wrong wheel")
    if mutation == "copied-result":
        data = json.loads((pairs / "result.json").read_text())
        data["cases"][1] = data["cases"][0]
        write(pairs / "result.json", data)
    if mutation == "missing-mcp":
        (pairs / "baseline-doctor.json.mcp.json").unlink()
    if mutation == "none":
        q._validate_analysis_conformance(root)
    else:
        with pytest.raises(q.QualificationError):
            q._validate_analysis_conformance(root)
