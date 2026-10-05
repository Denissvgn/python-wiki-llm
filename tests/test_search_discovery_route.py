"""Discovery receipts never substitute for exact inspection or task evidence."""

from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
from typing import Any

import pytest

from llm_wiki_cli import api
from llm_wiki_cli.services import native_inspection, task_context
from llm_wiki_cli.services.knowledge_storage_lifecycle import migrate_knowledge_storage
from llm_wiki_cli.services.token_counting import EstimatedCounter


STORE_SOURCE = '''"""Cobalt requests preserve existing values for repeated identifiers."""
from pathlib import Path
Path("target-execution-tripwire").write_text("executed")

class Store:
    """A cobalt request identifier selects the first recorded value."""
    def __init__(self):
        self.values = {}

    def save(self, request_id: str, value: int) -> int:
        if request_id not in self.values:
            self.values[request_id] = value
        return self.values[request_id]
'''
SCOPE_SOURCE = '''"""Repeated declarations deliberately require exact occurrences."""
class Repeated:
    def touch(self, value):
        return value + 1

class Repeated:
    def touch(self, value):
        return value + 2
'''
VIEW = {"schema_version": "llm-wiki-task-view-request/v1", "budget_tokens": 32000}


def _tree(root: Path) -> dict[str, bytes]:
    return {path.relative_to(root).as_posix(): path.read_bytes()
            for path in root.rglob("*") if path.is_file() and "__pycache__" not in path.parts}


def _source(root: Path, *, selected: bool) -> None:
    source = root / "src"
    folder = source / "selected" if selected else source
    folder.mkdir(parents=True)
    (folder / "store.py").write_text(STORE_SOURCE, encoding="utf-8")
    (folder / "scope.py").write_text(SCOPE_SOURCE, encoding="utf-8")
    if selected:
        (source / "outside.py").write_text("# excluded private sentinel\n", encoding="utf-8")
        profile = source / ".llm-wiki/source-selection.json"
        profile.parent.mkdir()
        profile.write_text(json.dumps({"schema_version": "llm-wiki-source-selection/v1",
                                       "include": ["selected"], "exclude": []}) + "\n", encoding="utf-8")


@pytest.fixture(params=["sharded-v2", "packed-v4-deflate"])
def native_project(tmp_path, monkeypatch, capsys, request):
    monkeypatch.chdir(tmp_path)
    _source(tmp_path, selected=True)
    api.bootstrap_wiki("src", "wiki")
    api.adopt_maintenance("src", "wiki", recovery_dir="maintenance-recovery")
    migrate_knowledge_storage(Path("wiki"), to=request.param, recovery_dir=Path("storage-recovery"))
    migrate_knowledge_storage(Path("wiki"), to="indexed-v8", recovery_dir=Path("manifest-recovery"))
    capsys.readouterr()
    assert not (tmp_path / "target-execution-tripwire").exists()
    return tmp_path


def _discover(**options: Any) -> dict[str, Any]:
    return dict(api.search_wiki("cobalt request identifier", src_dir="src", wiki_dir="wiki",
                               kinds=["modules", "entities"], limit=100,
                               discovery="qualified-v1", **options))


def _store_member(result: dict[str, Any]) -> dict[str, Any]:
    return next(member for member in result["discovery"]["members"] if member["path"] == "entities/Store.md")


def _request(path: str, *, source=False) -> dict[str, Any]:
    value: dict[str, Any] = {
        "schema_version": "llm-wiki-task-request/v2",
        "anchors": [{"kind": "wiki", "value": path}],
        "requirements": [{"id": "selected-concept", "facet": "concept", "selector": path}],
        "options": {"knowledge_mode": "required", "budget_tokens": 32000},
        "storage_options": {"selection": "required-facets-v1"},
    }
    if source:
        value["requirements"].append({"id": "decisive-source", "facet": "source-contract",
                                      "selector": "selected/store.py:Store.save"})
    else:
        value["options"]["read_scope"] = "snapshot"
    return value


def _compact(request: dict[str, Any]):
    result = api.build_compact_task_context(request, src_dir="src", wiki_dir="wiki", view_options=VIEW)
    assert result.ok
    canonical = api.validate_task_context(result.canonical_text, request)
    expanded = api.expand_compact_task_context(result.rendered, result.canonical_text, request, view_options=VIEW)
    for field in ("facts", "coverage", "omissions", "limitations"):
        assert expanded[field] == canonical[field]
    assert expanded["canonical"]["result_id"] == canonical["result_id"]
    return result, canonical, expanded


def test_pending_discovery_explicit_inspection_and_compact_keep_separate_authorities(native_project):
    before = _tree(native_project / "src"), _tree(native_project / "wiki")
    discovered = _discover()
    retained = deepcopy(discovered)
    member = _store_member(discovered)
    assert member["identity_state"] == "candidate"
    route = member["next_read"]
    assert route == {"operation": "inspect_concept", "locator_or_exact_route": "entities/Store.md",
                     "live": False, "selection_required": True, "resolution_performed": False}
    recorded = member["recorded_review"]
    assert recorded["basis"] == "snapshot" and recorded["live_evaluation_performed"] is False
    rows = recorded["records"]
    assert rows and any(row["recorded_status"] == "pending" for row in rows)
    assert all(row["effective_status"] is None and row["basis_available"] is False for row in rows)
    assert recorded["bounds"]["returned"] == len(rows)

    # Selecting the exact path is an explicit second operation by the caller.
    inspected = api.inspect_concept(route["locator_or_exact_route"], src_dir="src", wiki_dir="wiki",
                                    live=route["live"], limit=1)
    assert inspected["concept"]["found"] is True and inspected["concept"]["ambiguous"] is False
    selected = inspected["concept"]["concept"]
    assert selected is not None and selected["canonical_path"] == member["path"]
    assert inspected["read_scope"] == "snapshot-only"
    assert inspected["concept"]["knowledge"]["freshness_evaluated"] is False

    _, canonical, expanded = _compact(_request(member["path"]))
    concept = next(fact for fact in expanded["facts"] if fact["facet"] == "concept")
    summary = concept["observation"]["concept"]["maintenance"]
    assert summary["analysis_scope"] == "selected-header" and summary["availability"] == "partial"
    assert summary["pending"] == summary["acknowledged"] == 0
    assert summary["unavailable"] == summary["total"] > 0
    assert summary["live_evaluation_performed"] is False
    assert canonical["storage"]["whole_store_validated"] is False
    assert canonical["storage"]["lookup_complete"] is True
    status = api.get_maintenance_status("src", "wiki", live=False, limit=128)
    by_id = {row["record_id"]: row for row in status["records"]}
    assert all(by_id[row["record_id"]]["recorded_status"] == row["recorded_status"] for row in rows)
    assert discovered == retained
    assert (_tree(native_project / "src"), _tree(native_project / "wiki")) == before
    assert not (native_project / "target-execution-tripwire").exists()


def test_fuzzy_discovery_never_calls_exact_inspection_or_builds_a_task(native_project, monkeypatch):
    before = _tree(native_project / "src"), _tree(native_project / "wiki")
    monkeypatch.setattr(native_inspection, "inspect_native_concept", lambda *a, **k: pytest.fail("search inspected automatically"))
    monkeypatch.setattr(task_context, "build_task_context", lambda *a, **k: pytest.fail("search built a task automatically"))
    result = _discover()
    assert result["results"] and result["discovery"]["members"]
    assert all(member["identity_state"] == "candidate" and member["next_read"]["resolution_performed"] is False
               for member in result["discovery"]["members"])
    with pytest.raises(api.InvalidRequestError):
        api.inspect_concept("cobalt request identifier", src_dir="src", wiki_dir="wiki")
    assert (_tree(native_project / "src"), _tree(native_project / "wiki")) == before


def test_exact_missing_route_never_selects_a_nearby_discovery_candidate(native_project):
    before = _tree(native_project / "src"), _tree(native_project / "wiki")
    member = _store_member(_discover())
    missing = "entities/Store-missing.md"
    assert missing != member["next_read"]["locator_or_exact_route"]
    exact = api.inspect_concept(missing, src_dir="src", wiki_dir="wiki", live=False)
    assert exact["concept"]["found"] is False and exact["concept"]["ambiguous"] is False
    assert exact["concept"]["concept"] is None and exact["concept"]["bounds"]["matches"]["total"] == 0
    _, _, value = _compact(_request(missing))
    gap = next(row for row in value["coverage"] if row["requirement_id"] == "selected-concept")
    assert gap["state"] == "missing" and gap["satisfied"] is False
    assert value["facts"] == [] and value["omissions"]
    assert (_tree(native_project / "src"), _tree(native_project / "wiki")) == before


def test_unique_discovered_page_does_not_resolve_an_ambiguous_source_requirement(native_project):
    member = _store_member(_discover())
    exact = api.inspect_concept(member["path"], src_dir="src", wiki_dir="wiki", live=False)
    assert exact["concept"]["found"] is True
    request = _request(member["path"], source=True)
    request["requirements"].append({"id": "uncertain-owner", "facet": "source-contract",
                                     "selector": "selected/scope.py:Repeated.touch"})
    _, _, value = _compact(request)
    gap = next(row for row in value["coverage"] if row["requirement_id"] == "uncertain-owner")
    assert gap["state"] == "ambiguous" and gap["satisfied"] is False
    assert gap in value["omissions"]
    assert not any(fact["selector"] == "selected/scope.py:Repeated.touch" for fact in value["facts"])


@pytest.mark.parametrize("native_layout", ["absent", "flat"])
def test_native_capability_unavailable_never_becomes_source_only_success(tmp_path, monkeypatch, capsys, native_layout):
    monkeypatch.chdir(tmp_path)
    _source(tmp_path, selected=False)
    if native_layout == "flat":
        api.bootstrap_wiki("src", "wiki")
        capsys.readouterr()
    else:
        Path("wiki/entities").mkdir(parents=True)
        Path("wiki/entities/Store.md").write_text("# Store\n\n## Description\nCobalt request identifiers.\n", encoding="utf-8")
    before = _tree(tmp_path / "src"), _tree(tmp_path / "wiki")
    member = _store_member(_discover())
    assert member["native"]["state"] == "unavailable" and member["native"]["locator"] is None
    request = _request(member["path"])
    with pytest.raises(api.LlmWikiApiError):
        api.build_compact_task_context(request, src_dir="src", wiki_dir="wiki", view_options=VIEW)
    if native_layout == "absent":
        request["options"]["knowledge_mode"] = "auto"
        _, _, value = _compact(request)
        gap = next(row for row in value["coverage"] if row["requirement_id"] == "selected-concept")
        assert gap["state"] == "unavailable" and gap["satisfied"] is False
        assert value["facts"] == [] and value["state"] != "covered"
    assert (_tree(tmp_path / "src"), _tree(tmp_path / "wiki")) == before
    assert not (tmp_path / "target-execution-tripwire").exists()


@pytest.mark.parametrize("mutation", ["missing", "valid-reformat"])
def test_declared_legacy_native_corruption_is_not_capability_unavailable(tmp_path, monkeypatch, capsys, mutation):
    monkeypatch.chdir(tmp_path)
    _source(tmp_path, selected=False)
    api.bootstrap_wiki("src", "wiki")
    capsys.readouterr()
    path = Path("wiki/.llm-wiki-knowledge.json")
    if mutation == "missing":
        path.unlink()
    else:
        path.write_bytes(path.read_bytes() + b" \n")
        assert json.loads(path.read_bytes())["schema_version"] == "llm-wiki-knowledge/v1"
    before = _tree(tmp_path / "src"), _tree(tmp_path / "wiki")
    with pytest.raises(api.LlmWikiApiError):
        _discover()
    assert (_tree(tmp_path / "src"), _tree(tmp_path / "wiki")) == before


def test_plain_discovery_does_not_reload_an_uncaptured_maintenance_owner(tmp_path, monkeypatch):
    from llm_wiki_cli.services.sync_manifest import SyncManifest

    monkeypatch.chdir(tmp_path)
    _source(tmp_path, selected=False)
    Path("wiki/entities").mkdir(parents=True)
    Path("wiki/entities/Store.md").write_text("# Store\n\n## Description\nCobalt request identifiers.\n", encoding="utf-8")
    monkeypatch.setattr(SyncManifest, "load", classmethod(
        lambda cls, *a, **k: pytest.fail("discovery reopened an uncaptured owner outside its guarded budget")))
    member = _store_member(_discover())
    assert member["native"]["state"] == "unavailable"
    assert member["recorded_review"]["availability"] == "unadopted"


def test_discovery_does_not_bypass_compact_output_budget(native_project):
    member = _store_member(_discover())
    request = _request(member["path"])
    result = api.build_compact_task_context(request, src_dir="src", wiki_dir="wiki",
                                          view_options={**VIEW, "budget_tokens": 1})
    assert not result.ok and result.error == "cannot-fit-compact" and result.rendered == ""
    assert "facts" not in result.to_payload()
    canonical = api.validate_task_context(result.canonical_text, request)
    assert canonical["coverage"][0]["satisfied"] is True
    assert result.accounting["minimum_tokens"] > 1


@pytest.mark.parametrize("surface", ["source", "wiki", "native", "selection", "counter"])
def test_discovered_route_compact_rejects_late_counter_or_input_races(native_project, surface):
    member = _store_member(_discover())
    request = _request(member["path"], source=True)

    class RacingCounter(EstimatedCounter):
        changed = False

        def count(self, text):
            if not self.changed and '"schema_version":"llm-wiki-task-compact/v1"' in text:
                self.changed = True
                if surface == "counter":
                    self.identity = "changed-after-discovery/v1"
                else:
                    path = {"source": Path("src/selected/store.py"), "wiki": Path("wiki/entities/Store.md"),
                            "native": Path("wiki/.llm-wiki-knowledge.json"),
                            "selection": Path("src/.llm-wiki/source-selection.json")}[surface]
                    path.write_bytes(path.read_bytes() + b"\n# raced after compact rendering\n")
            return super().count(text)

    counter = RacingCounter()
    with pytest.raises(api.LlmWikiApiError):
        api.build_compact_task_context(request, src_dir="src", wiki_dir="wiki", view_options=VIEW, counter=counter)
    assert counter.changed
