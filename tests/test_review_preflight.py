"""Review admission must distinguish exclusion from a negative impact result."""

from __future__ import annotations

import json
import stat
from pathlib import Path
from types import SimpleNamespace

import pytest

from llm_wiki_cli.commands import review_cmd
from llm_wiki_cli.services import impact, review_service
from llm_wiki_cli.services.extraction_service import InventoryResult
from llm_wiki_cli.services.source_selection import (
    SourceSelectionError,
    resolve_source_selection,
    with_source_selection_generation_input,
)
from llm_wiki_cli.services.source_snapshot import (
    SourceSnapshot,
    SourceSnapshotError,
    build_source_snapshot,
)
from llm_wiki_cli.services.sync_manifest import SyncManifest
from tests.test_change_selection import git


@pytest.fixture
def scoped(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "selected").mkdir()
    (tmp_path / "outside").mkdir()
    (tmp_path / "selected/app.py").write_text("def run(): return 1\n", encoding="utf-8")
    (tmp_path / "selected/client.ts").write_text(
        "export const client = 1;\n", encoding="utf-8"
    )
    (tmp_path / "outside/ignored.py").write_bytes(b"excluded opaque bytes\x00\xff")
    (tmp_path / ".gitignore").write_text(
        "# captured fixture selection control\n", encoding="utf-8"
    )
    (tmp_path / "selection.json").write_text(
        json.dumps(
            {
                "schema_version": "llm-wiki-source-selection/v1",
                "include": ["selected"],
                "exclude": [],
            }
        ),
        encoding="utf-8",
    )
    policy = resolve_source_selection(tmp_path, "selection.json")
    assert policy is not None
    snapshot = build_source_snapshot(tmp_path, selection_policy=policy)
    wiki = tmp_path / "wiki"
    wiki.mkdir()
    (wiki / "index.md").write_text("# Private wiki\n", encoding="utf-8")
    SyncManifest(
        generation_inputs=with_source_selection_generation_input(
            {},
            policy.identity,
            snapshot.source_selection_inputs,
        )
    ).save(wiki)
    return tmp_path


def _request(paths: list[str]) -> dict:
    return {
        "src_dir": ".",
        "wiki_dir": "wiki",
        "source_selection": "selection.json",
        "changes": {"mode": "paths", "paths": paths},
    }


def _unavailable(*_args, **_kwargs):
    raise ValueError("full selected inventory requires the unavailable helper")


def _tree(root: Path) -> dict[str, bytes]:
    return {
        p.relative_to(root).as_posix(): p.read_bytes()
        for p in root.rglob("*")
        if p.is_file() and ".git" not in p.parts
    }


def test_excluded_only_returns_explicit_scope_before_unrelated_inventory(
    scoped: Path, monkeypatch: pytest.MonkeyPatch
):
    before = _tree(scoped)
    monkeypatch.setattr(review_service, "get_inventory_result", _unavailable)
    findings = review_service.build_findings("", **_request(["outside/ignored.py"]))
    assert len(findings) == 1
    finding = findings[0]
    assert finding.severity == "info" and finding.source_path == "outside/ignored.py"
    assert finding.wiki_pages == []
    assert "excluded" in finding.reason.lower()
    assert "regular-file" in finding.reason
    assert "not evaluated" in finding.reason.lower()
    assert "unknown" in finding.reason.lower()
    assert "no impact" not in finding.reason.lower()
    assert set(json.loads(review_cmd.render_json(findings))) == {"ok", "findings"}
    assert "No wiki-aware review findings" not in review_cmd.render_markdown(findings)
    assert _tree(scoped) == before


def test_excluded_only_impact_does_not_construct_a_graph_or_claim_zero_impact(
    scoped: Path, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.setattr(review_service, "get_inventory_result", _unavailable)
    monkeypatch.setattr(impact, "build_dependency_graph", _unavailable)
    monkeypatch.setattr(impact, "build_static_api_contracts", _unavailable)
    monkeypatch.setattr(review_service, "_surface_index_pages", _unavailable)
    monkeypatch.setattr(review_service, "_symbol_reference_pages", _unavailable)
    monkeypatch.setattr(review_service, "_surface_text_pages", _unavailable)
    result = impact.build_impact(
        **_request(["outside/ignored.py", "outside/deleted.py"])
    )
    scope = result["review_scope"]
    assert scope["status"] == "excluded-only"
    assert scope["cost"]["full_inventory_performed"] is False
    assert (
        scope["cost"]["source_snapshot_scope"]
        == "full-selected-discovery-and-content-capture"
    )
    rows = {row["path"]: row for row in scope["paths"]}
    assert rows["outside/ignored.py"]["physical"] == "regular-file"
    assert rows["outside/deleted.py"]["physical"] == "missing"
    assert all(
        row["selection"] == "excluded" and row["inventory"] == "not-evaluated"
        for row in rows.values()
    )
    assert (
        result["dependencies"]["basis"]
        == result["contracts"]["basis"]
        == "not-evaluated-excluded-only"
    )
    assert all(f["basis"] == "source-selection-preflight" for f in result["findings"])
    summary = impact.render_summary(result)
    assert "not evaluated" in summary.lower() and "no impact" in summary.lower()
    assert "Dependency edges: 0" not in summary


@pytest.mark.parametrize(
    "paths",
    [
        ["selected/app.py"],
        ["selected/app.py", "outside/ignored.py"],
        [],
        ["selection.json"],
        [".gitignore"],
        ["selected/deleted.py"],
    ],
    ids=["selected", "mixed", "empty", "profile", "ignore", "selected-deletion"],
)
def test_full_review_routes_retain_unavailable_helper_failure(
    scoped: Path, monkeypatch: pytest.MonkeyPatch, paths: list[str]
):
    calls = []

    def unavailable(*args, **kwargs):
        calls.append(kwargs)
        _unavailable()

    monkeypatch.setattr(review_service, "get_inventory_result", unavailable)
    with pytest.raises(ValueError, match="unavailable helper"):
        review_service.build_findings("", **_request(paths))
    assert len(calls) == 1 and calls[0]["deep"] is True
    assert calls[0]["source_snapshot"].source_selection_path == "selection.json"


def test_mixed_ready_review_retains_real_mapping_and_full_cost(
    scoped: Path, monkeypatch: pytest.MonkeyPatch
):
    def inventory(*_args, source_snapshot=None, **_kwargs):
        return InventoryResult(
            {
                "selected/app.py": {"classes": [], "functions": []},
                "selected/client.ts": {"classes": [], "functions": []},
            },
            {},
            source_snapshot=source_snapshot,
        )

    monkeypatch.setattr(review_service, "get_inventory_result", inventory)
    result = impact.build_impact(**_request(["selected/app.py", "outside/ignored.py"]))
    assert result["changes"]["paths"] == ["selected/app.py"]
    assert result["review_scope"]["status"] == "mixed"
    assert result["review_scope"]["cost"]["full_inventory_performed"] is True
    rows = {r["path"]: r for r in result["review_scope"]["paths"]}
    assert rows["selected/app.py"]["inventory"] == "present"
    assert rows["outside/ignored.py"]["inventory"] == "absent"
    assert result["page_mapping"]["selected/app.py"]
    assert any(
        f["source_path"] == "selected/app.py" and f["severity"] == "warning"
        for f in result["findings"]
    )
    assert result["dependencies"]["basis"] == "candidate-static-imports"


def test_excluded_only_real_unprepared_helper_is_not_prepared(scoped: Path):
    cache = scoped / "empty-helper-cache"
    request = _request(["outside/ignored.py"])
    findings = review_service.build_findings("", **request, helper_cache_dir=str(cache))
    assert findings and "not evaluated" in findings[0].reason.lower()
    assert not cache.exists()
    with pytest.raises(ValueError, match="extraction failed"):
        review_service.build_findings(
            "",
            **_request(["selected/app.py", "outside/ignored.py"]),
            helper_cache_dir=str(cache),
        )
    assert not cache.exists()


@pytest.mark.parametrize(
    "bad", ["../outside.py", "/outside.py", "a//b.py", "C:/outside.py"]
)
def test_preflight_never_admits_malformed_paths(
    scoped: Path, monkeypatch: pytest.MonkeyPatch, bad: str
):
    monkeypatch.setattr(review_service, "get_inventory_result", _unavailable)
    with pytest.raises(ValueError, match="paths"):
        review_service.build_findings("", **_request([bad]))


def test_profile_mismatch_still_refuses_before_excluded_only_result(scoped: Path):
    data = json.loads((scoped / "selection.json").read_bytes())
    data["include"] = ["selected/app.py"]
    (scoped / "selection.json").write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(SourceSelectionError, match="persisted"):
        review_service.build_findings("", **_request(["outside/ignored.py"]))


def test_preflight_metadata_is_bounded_without_reading_excluded_contents(
    scoped: Path, monkeypatch: pytest.MonkeyPatch
):
    requested = [f"outside/file{i:03d}.py" for i in range(105)]
    monkeypatch.setattr(review_service, "get_inventory_result", _unavailable)
    inspected = []
    original = review_service._review_physical_state

    def observe(root, path):
        inspected.append(path)
        return original(root, path)

    monkeypatch.setattr(review_service, "_review_physical_state", observe)
    analysis = review_service.build_analysis("", **_request(requested))
    scope = analysis.review_scope
    assert scope is not None
    assert scope["bounds"] == {
        "paths": {"total": 105, "returned": 100, "omitted": 5},
        "physical_max_components": 32,
        "excluded_content_reads": 0,
    }
    assert len(inspected) == 100 and len(analysis.findings) == 100
    assert "5 additional excluded" in analysis.findings[-1].suggested_follow_up


@pytest.mark.parametrize("kind", ["symlink", "reparse-tag", "reparse-attribute"])
@pytest.mark.parametrize("unsafe_at", ["root", "ancestor"])
def test_metadata_does_not_follow_unsafe_ancestors(
    scoped: Path, monkeypatch: pytest.MonkeyPatch, kind: str, unsafe_at: str
):
    original = Path.lstat
    inspected = []

    def lstat(path, *args, **kwargs):
        inspected.append(path)
        if path == (scoped if unsafe_at == "root" else scoped / "outside"):
            return SimpleNamespace(
                st_mode=stat.S_IFLNK if kind == "symlink" else stat.S_IFDIR,
                st_reparse_tag=1 if kind == "reparse-tag" else 0,
                st_file_attributes=0x400 if kind == "reparse-attribute" else 0,
            )
        return original(path, *args, **kwargs)

    monkeypatch.setattr(Path, "lstat", lstat)
    assert (
        review_service._review_physical_state(scoped, "outside/ignored.py")
        == "unsafe-path"
    )
    assert scoped / "outside/ignored.py" not in inspected


def test_selection_mutation_during_preflight_cannot_return_a_limited_success(
    scoped: Path, monkeypatch: pytest.MonkeyPatch
):
    original = review_service._review_physical_state

    def mutate(root, path):
        result = original(root, path)
        (scoped / "selection.json").write_text("{}\n", encoding="utf-8")
        return result

    monkeypatch.setattr(review_service, "_review_physical_state", mutate)
    with pytest.raises(SourceSnapshotError, match="selection_policy"):
        review_service.build_findings("", **_request(["outside/ignored.py"]))


def test_selected_source_mutation_during_excluded_preflight_is_refused(
    scoped: Path, monkeypatch: pytest.MonkeyPatch
):
    original = review_service._review_physical_state

    def mutate(root, path):
        result = original(root, path)
        (scoped / "selected/app.py").write_text("CHANGED = True\n", encoding="utf-8")
        return result

    monkeypatch.setattr(review_service, "_review_physical_state", mutate)
    with pytest.raises(ValueError, match="Source changed"):
        review_service.build_findings("", **_request(["outside/ignored.py"]))


def test_equivalent_excluded_patch_paths_staged_and_range_keep_one_identity(
    scoped: Path, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.setattr(review_service, "get_inventory_result", _unavailable)
    git(scoped, "init", "-q")
    git(scoped, "add", ".")
    git(scoped, "commit", "-qm", "base")
    base = git(scoped, "rev-parse", "HEAD")
    (scoped / "outside/ignored.py").write_text("VALUE = 2\n", encoding="utf-8")
    git(scoped, "add", "outside/ignored.py")
    patch = git(scoped, "diff", "--cached")
    common = {k: v for k, v in _request([]).items() if k != "changes"}
    explicit = impact.build_impact(**_request(["outside/ignored.py"]))
    assert impact.build_impact(patch, **common) == explicit
    assert impact.build_impact(**common, changes={"mode": "staged"}) == explicit
    git(scoped, "commit", "-qm", "candidate")
    assert (
        impact.build_impact(
            **common, changes={"mode": "range", "base": base, "head": "HEAD"}
        )
        == explicit
    )


def test_unavailable_selection_is_never_promoted_to_excluded_only(
    scoped: Path, monkeypatch: pytest.MonkeyPatch
):
    original = SourceSnapshot.path_is_effectively_selected

    def unavailable(self, path):
        if path == "outside/ignored.py":
            raise SourceSelectionError("selected_path", "classification unavailable")
        return original(self, path)

    monkeypatch.setattr(SourceSnapshot, "path_is_effectively_selected", unavailable)
    monkeypatch.setattr(review_service, "get_inventory_result", _unavailable)
    with pytest.raises(ValueError, match="unavailable helper"):
        review_service.build_findings("", **_request(["outside/ignored.py"]))


def test_available_inventory_does_not_hide_unclassified_review_scope(
    scoped: Path, monkeypatch: pytest.MonkeyPatch
):
    original = SourceSnapshot.path_is_effectively_selected

    def unavailable(self, path):
        if path == "outside/ignored.py":
            raise SourceSelectionError("selected_path", "classification unavailable")
        return original(self, path)

    def inventory(*_args, source_snapshot=None, **_kwargs):
        return InventoryResult(
            {"selected/app.py": {"classes": []}}, {}, source_snapshot=source_snapshot
        )

    monkeypatch.setattr(SourceSnapshot, "path_is_effectively_selected", unavailable)
    monkeypatch.setattr(review_service, "get_inventory_result", inventory)
    findings = review_service.build_findings("", **_request(["outside/ignored.py"]))
    assert len(findings) == 1 and "could not classify" in findings[0].reason
    assert "unknown" in findings[0].reason and findings[0].wiki_pages == []
    result = impact.build_impact(**_request(["outside/ignored.py"]))
    assert result["review_scope"]["status"] == "selection-unavailable"
    assert result["review_scope"]["cost"]["full_inventory_performed"] is True
    assert result["findings"][0]["basis"] == "source-selection-preflight"


@pytest.mark.parametrize(
    "format", ["json", "markdown", "impact-json", "impact-markdown", "github"]
)
def test_cli_formats_keep_the_excluded_only_qualification(
    scoped: Path, monkeypatch: pytest.MonkeyPatch, capsys, format: str
):
    monkeypatch.setattr(review_service, "get_inventory_result", _unavailable)
    review_cmd.run(
        SimpleNamespace(
            src_dir=".",
            wiki_dir="wiki",
            format=format,
            source_selection="selection.json",
            changed_path=["outside/ignored.py"],
        )
    )
    output = capsys.readouterr().out
    if format == "json":
        assert set(json.loads(output)) == {"ok", "findings"}
    elif format == "impact-json":
        assert json.loads(output)["review_scope"]["status"] == "excluded-only"
    else:
        assert "not evaluated" in output.lower()


def test_metadata_depth_and_unreadable_states_remain_unknown(
    scoped: Path, monkeypatch: pytest.MonkeyPatch
):
    assert (
        review_service._review_physical_state(scoped, "/".join(["deep"] * 33))
        == "unavailable-depth-limit"
    )
    original = Path.lstat

    def denied(path, *args, **kwargs):
        if path == scoped / "outside":
            raise PermissionError("metadata unavailable")
        return original(path, *args, **kwargs)

    monkeypatch.setattr(Path, "lstat", denied)
    assert (
        review_service._review_physical_state(scoped, "outside/ignored.py")
        == "unavailable"
    )
