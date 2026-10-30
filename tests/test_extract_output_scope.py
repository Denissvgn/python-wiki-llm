"""Extraction selectors apply to emitted source and infrastructure records."""
from __future__ import annotations

import json
from types import SimpleNamespace

import pytest

from llm_wiki_cli.api import InvalidRequestError, extract_source
from llm_wiki_cli.services import extraction_service as service
from llm_wiki_cli.services.dependencies import describe_unscanned_scopes
from llm_wiki_cli.services.source_selection import SOURCE_SELECTION_SCHEMA_VERSION
from llm_wiki_cli.services.source_snapshot import build_source_snapshot


@pytest.fixture
def project(tmp_path):
    files = {
        "pyproject.toml": '[project]\nname = "root-owner"\ndependencies = ["root-dep"]\n'
                          '[project.scripts]\nroot-tool = "root:root"\nmissing-tool = "missing:main"\n',
        "root.py": "def root():\n    return 1\n",
        "Dockerfile": "FROM alpine\nCOPY app /app\n",
        "compose.yaml": "services:\n  root:\n    image: alpine\n",
        "app/pyproject.toml": '[project]\nname = "app-owner"\ndependencies = ["selected-dep"]\n',
        "app/main.py": "__all__ = ['main']\ndef main():\n    return 42\n",
        "app/helper.py": "def helper():\n    return 1\n",
        "app/Dockerfile": "FROM python:3.14-slim\nCOPY . /app\n",
        "app/infra.yaml": "services:\n  selected:\n    build: .\n",
        "app/deploy.sh": "#!/bin/sh\necho app\n",
        "app/nested/pyproject.toml": '[project]\nname = "nested-owner"\n',
        "app/nested/child.py": "def child():\n    pass\n",
        "app/nested/Dockerfile": "FROM busybox\n",
        "app_extra/other.py": "def other():\n    pass\n",
        "app_extra/Dockerfile": "FROM nginx\n",
        "app_extra/deploy.sh": "#!/bin/sh\necho other\n",
    }
    for relative, text in files.items():
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    return tmp_path.resolve()


def _extract(project, **options):
    return service.build_extract_payload(str(project), allow_external_src=True, read_only=True, **options)


@pytest.mark.parametrize("deep", [False, True])
@pytest.mark.parametrize("summary", [False, True])
def test_exact_code_path_excludes_unselected_infrastructure(project, deep, summary):
    result = _extract(project, paths=["app/main.py"], deep=deep, summary=summary)
    assert set(result.payload["inventory"]) == {"app/main.py"}
    assert "docker" not in result.payload and result.docker_count == 0


@pytest.mark.parametrize("path", ["app/Dockerfile", "compose.yaml", "app/infra.yaml"])
def test_exact_infrastructure_path_does_not_expand_related_contents(project, path):
    result = _extract(project, paths=[path], deep=True)
    assert result.payload["inventory"] == {}
    assert set(result.payload["docker"]) == {path}
    assert result.docker_count == 1


def test_mixed_exact_paths_intersect_a_supplied_broad_snapshot(project):
    snapshot = build_source_snapshot(project)
    paths = ["app/main.py", "app/Dockerfile", "app/infra.yaml", "app/deploy.sh"]
    result = _extract(project, paths=paths, source_snapshot=snapshot, deep=True)
    assert set(result.payload["inventory"]) == {"app/main.py"}
    assert set(result.payload["docker"]) == {"app/Dockerfile", "app/infra.yaml"}
    assert result.payload["unsupported_sources"] == {"shell": {"count": 1, "paths": ["app/deploy.sh"]}}


@pytest.mark.parametrize("absolute", [False, True])
def test_supported_path_spellings_select_code_and_infrastructure_consistently(project, absolute):
    selected = ["app/main.py", "app/Dockerfile"]
    paths = [str(project / path) if absolute else "./" + path for path in selected]
    result = _extract(project, paths=paths, deep=True)
    assert set(result.payload["inventory"]) == {"app/main.py"}
    assert set(result.payload["docker"]) == {"app/Dockerfile"}


@pytest.mark.parametrize("path", ["app/main.py", "app/Dockerfile", "compose.yaml", "app/infra.yaml"])
def test_changed_files_apply_to_every_emitted_facet(project, monkeypatch, path):
    monkeypatch.setattr(service, "_git_changed_files", lambda _root: [path])
    result = _extract(project, changed=True, deep=True)
    assert result.changed_file_count == 1
    assert set(result.payload["inventory"]) == ({path} if path.endswith(".py") else set())
    assert set(result.payload.get("docker", {})) == (set() if path.endswith(".py") else {path})


@pytest.mark.parametrize("changed", [None, []])
def test_changed_full_fallback_and_empty_selection_remain_distinct(project, monkeypatch, changed):
    monkeypatch.setattr(service, "_git_changed_files", lambda _root: changed)
    result = _extract(project, changed=True, deep=True)
    if changed is None:
        assert "Dockerfile" in result.payload["docker"]
        assert "app/main.py" in result.payload["inventory"]
        assert not result.no_changed_files
    else:
        assert result.payload["inventory"] == {} and "docker" not in result.payload
        assert result.no_changed_files


def test_changed_selection_boundary_reevaluates_all_selected_facets(project, monkeypatch):
    policy = project / "selection.json"
    policy.write_text(json.dumps({"schema_version": SOURCE_SELECTION_SCHEMA_VERSION,
        "include": ["app", "Dockerfile"], "exclude": []}), encoding="utf-8")
    monkeypatch.setattr(service, "_git_changed_files", lambda _root: ["selection.json"])
    result = _extract(project, changed=True, deep=True, source_selection="selection.json")
    assert "app/main.py" in result.payload["inventory"]
    assert set(result.payload["docker"]) == {"Dockerfile", "app/Dockerfile", "app/infra.yaml", "app/nested/Dockerfile"}


def test_package_selection_uses_nearest_owner_for_every_emitted_facet(project):
    result = _extract(project, package_filter="app-owner", deep=True)
    assert set(result.payload["inventory"]) == {"app/main.py", "app/helper.py"}
    assert set(result.payload["docker"]) == {"app/Dockerfile", "app/infra.yaml"}
    assert result.payload["unsupported_sources"] == {"shell": {"count": 1, "paths": ["app/deploy.sh"]}}
    assert result.payload["dependencies"]["external"]["python"]["unused"] == ["selected-dep"]


def test_package_and_paths_are_an_intersection_including_infrastructure_only(project):
    result = _extract(project, package_filter="app-owner", paths=["app/Dockerfile", "app/nested/Dockerfile"], deep=True)
    assert result.payload["inventory"] == {}
    assert set(result.payload["docker"]) == {"app/Dockerfile"}


def test_package_with_infrastructure_but_no_code_is_not_empty(project):
    (project / "containers").mkdir()
    (project / "containers/pyproject.toml").write_text('[project]\nname = "container-owner"\n', encoding="utf-8")
    (project / "containers/Dockerfile").write_text("FROM alpine\n", encoding="utf-8")
    result = _extract(project, package_filter="container-owner", deep=True)
    assert result.payload["inventory"] == {}
    assert set(result.payload["docker"]) == {"containers/Dockerfile"}


def test_unknown_package_is_not_satisfied_by_unrelated_infrastructure(project):
    with pytest.raises(ValueError, match="No files found for package 'missing'"):
        _extract(project, package_filter="missing", deep=True)


def test_unselected_infrastructure_is_not_parsed(project, monkeypatch):
    def reject(_text):
        raise AssertionError("unselected infrastructure was parsed")
    monkeypatch.setattr(service, "_parse_dockerfile", reject)
    monkeypatch.setattr(service, "_parse_compose", reject)
    result = _extract(project, paths=["app/main.py"], deep=True)
    assert "docker" not in result.payload


def test_lower_level_infrastructure_selection_preserves_default_and_empty_scopes(project):
    snapshot = build_source_snapshot(project, only_files=["app/main.py"])
    assert len(service.get_docker_inventory(project, source_snapshot=snapshot)) == 6
    assert service.get_docker_inventory(project, source_snapshot=snapshot, only_files=[]) == {}
    assert set(service.get_docker_inventory(project, source_snapshot=snapshot, only_files=["./app/infra.yaml"])) == {"app/infra.yaml"}


def test_public_api_applies_the_same_selection(project):
    payload = extract_source(str(project), paths=["app/main.py"], deep=True, allow_external_src=True)
    assert set(payload["inventory"]) == {"app/main.py"}
    assert "docker" not in payload


@pytest.mark.parametrize("folder", ["a", "z"])
def test_single_character_package_root_overrides_the_parent(project, folder):
    (project / folder).mkdir()
    (project / folder / "pyproject.toml").write_text('[project]\nname = "child-owner"\n', encoding="utf-8")
    (project / folder / "main.py").write_text("def main():\n    pass\n", encoding="utf-8")
    (project / folder / "Dockerfile").write_text("FROM alpine\n", encoding="utf-8")
    result = _extract(project, package_filter="child-owner", deep=True)
    assert set(result.payload["inventory"]) == {f"{folder}/main.py"}
    assert set(result.payload["docker"]) == {f"{folder}/Dockerfile"}
    assert result.payload["dependencies"]["external"]["python"]["unused"] == []


def test_unsupported_only_package_retains_qualified_selected_records(project):
    (project / "scripts").mkdir()
    (project / "scripts/pyproject.toml").write_text('[project]\nname = "script-owner"\n', encoding="utf-8")
    (project / "scripts/deploy.sh").write_text("#!/bin/sh\necho scripts\n", encoding="utf-8")
    result = _extract(project, package_filter="script-owner", deep=True)
    assert result.payload["inventory"] == {} and "docker" not in result.payload
    assert result.payload["unsupported_sources"] == {"shell": {"count": 1, "paths": ["scripts/deploy.sh"]}}
    assert result.payload["data_flow_details"]["state"] == "unsupported"


def test_unscanned_parent_does_not_claim_a_selected_child_source(project):
    snapshot = build_source_snapshot(project, only_files=["app/main.py"])
    parent = describe_unscanned_scopes(project, "python", [""], snapshot)[0]
    assert parent["manifests"] == ["pyproject.toml"]
    assert parent["reason"] == "source-scope-unavailable" and parent["sources"] == []


def test_empty_paths_do_not_fall_back_to_the_source_tree(project):
    result = _extract(project, paths=[], deep=True)
    assert result.payload["inventory"] == {}
    assert "docker" not in result.payload and "unsupported_sources" not in result.payload
    assert result.inventory_count == result.docker_count == 0
    assert "entrypoints" not in result.payload and result.payload["data_flows"] == []
    assert extract_source(str(project), paths=[], deep=True, allow_external_src=True)["inventory"] == {}


def test_explicit_paths_cannot_readmit_profile_excluded_infrastructure(project):
    (project / "selection.json").write_text(json.dumps({"schema_version": SOURCE_SELECTION_SCHEMA_VERSION,
        "include": ["app"], "exclude": ["app/Dockerfile"]}), encoding="utf-8")
    result = _extract(project, paths=["app/Dockerfile", "app/infra.yaml"], deep=True, source_selection="selection.json")
    assert result.payload["inventory"] == {}
    assert set(result.payload["docker"]) == {"app/infra.yaml"}


def test_explicit_ignored_infrastructure_keeps_its_existing_opt_in(project):
    (project / ".gitignore").write_text("app/Dockerfile\n", encoding="utf-8")
    result = _extract(project, paths=["app/Dockerfile"], deep=True)
    assert result.payload["inventory"] == {}
    assert set(result.payload["docker"]) == {"app/Dockerfile"}


@pytest.mark.parametrize("path", ["app/main.py", "app/Dockerfile"])
def test_exact_paths_exclude_unbound_console_declarations_from_context(project, path):
    result = _extract(project, paths=[path], deep=True)
    assert all(entry.get("file") == path for entry in result.payload.get("entrypoints", []))
    assert all(flow["entry"].get("file") == path for flow in result.payload["data_flows"])


def test_selected_project_manifest_retains_its_unresolved_declarations(project):
    result = _extract(project, paths=["pyproject.toml"], deep=True)
    assert result.payload["inventory"] == {} and "docker" not in result.payload
    assert {entry["label"] for entry in result.payload["entrypoints"]} == {"root-tool", "missing-tool"}
    assert all(flow["analysis"]["state"] == "unavailable" for flow in result.payload["data_flows"])


def test_package_selection_does_not_invoke_unrelated_language_extractors(project, monkeypatch):
    from llm_wiki_cli.extractors.ts_extractor import TypeScriptExtractor
    (project / "app/client.ts").write_text("export const selected = 1;\n", encoding="utf-8")
    (project / "app_extra/client.ts").write_text("export const other = 1;\n", encoding="utf-8")
    def reject(*args, **kwargs):
        raise AssertionError("a Python package selection invoked TypeScript extraction")
    monkeypatch.setattr(TypeScriptExtractor, "extract", reject)
    result = _extract(project, package_filter="app-owner", deep=True)
    assert set(result.payload["inventory"]) == {"app/main.py", "app/helper.py"}


def test_public_scope_bounds_provider_output_and_retains_explicit_custom_sources(project, monkeypatch):
    (project / "custom.widget").write_text("custom source\n", encoding="utf-8")
    inventory = {path: {"language": "python", "functions": [{"name": symbol}], "all_exports": [symbol]}
                 for path, symbol in (("app/main.py", "main"), ("app/helper.py", "helper"), ("custom.widget", "custom"))}
    monkeypatch.setattr(service, "get_inventory_result", lambda _request: service.InventoryResult(inventory, {}))
    selected = {"app/main.py", "custom.widget"}
    result = _extract(project, paths=sorted(selected), deep=True)
    assert set(result.payload["inventory"]) == selected
    assert {entry["file"] for entry in result.payload["entrypoints"]} == selected
    assert "docker" not in result.payload


@pytest.mark.parametrize("package", ["", " \t", False, []])
def test_invalid_package_selector_is_rejected_before_extraction(project, monkeypatch, package):
    def reject(_request):
        raise AssertionError("invalid package selector reached extraction")
    monkeypatch.setattr(service, "get_inventory_result", reject)
    with pytest.raises(ValueError, match="--package must be a non-empty package name"):
        _extract(project, package_filter=package, deep=True)


@pytest.mark.parametrize("package", ["", "   "])
def test_python_api_rejects_an_empty_package_selector(project, package):
    with pytest.raises(InvalidRequestError, match="--package must be a non-empty package name"):
        extract_source(str(project), package=package, deep=True, allow_external_src=True)


def test_cli_rejects_an_empty_package_selector_without_emitting_inventory(project, capsys):
    args = SimpleNamespace(src_dir=str(project), changed=False, paths=None, package="", summary=False,
                           deep=True, output=None, include_empty=False, read_only=True, allow_external_src=True)
    with pytest.raises(SystemExit) as error:
        service.run(args)
    captured = capsys.readouterr()
    assert error.value.code == 2
    assert captured.out == ""
    assert "--package must be a non-empty package name" in captured.err
