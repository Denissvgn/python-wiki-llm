"""Contract tests for fail-closed dependency vulnerability triage."""

from __future__ import annotations

import json

from llm_wiki_cli.commands.extract_cmd import _dependency_extract_block
from llm_wiki_cli.services import skills
from llm_wiki_cli.services.dependencies import analyze_dependencies


def _skill_text() -> str:
    skill_dir = skills.BUNDLED_SKILLS_ROOT / "dep-vuln-triage"
    return "\n".join(
        (skill_dir / filename).read_text(encoding="utf-8")
        for filename in ("SKILL.md", "reference.md")
    )


def _imp(module: str, name: str | None = None) -> dict[str, str]:
    return {"module": module, "name": name if name is not None else module}


def _mod(language: str, *imports: dict[str, str]) -> dict:
    return {
        "language": language,
        "imports": list(imports),
        "classes": [],
        "functions": [],
    }


def _public_external(tmp_path, inventory: dict) -> dict:
    analysis = analyze_dependencies(inventory, str(tmp_path))
    return _dependency_extract_block(analysis)["external"]


def _public_dependencies(tmp_path, inventory: dict) -> dict:
    return _dependency_extract_block(
        analyze_dependencies(inventory, str(tmp_path))
    )


def test_optional_package_is_preserved_by_versioned_public_contract(
    tmp_path,
):
    (tmp_path / "pyproject.toml").write_text(
        """\
[project]
name = "example"
dependencies = ["requests>=2"]

[project.optional-dependencies]
dev = ["pytest>=8"]
""",
        encoding="utf-8",
    )

    dependencies = _public_dependencies(tmp_path, {})
    python = dependencies["external"]["python"]

    assert python == {
        "used": {},
        "undeclared": [],
        "unused": ["requests"],
    }
    assert "pytest" not in json.dumps(python)
    pytest_record = next(
        record
        for record in dependencies["version_details"]["records"]
        if record["package"] == "pytest"
    )
    assert pytest_record["declaration"] == "optional"
    assert pytest_record["selection_confidence"] == "declared"
    assert pytest_record["scope"] == "."

    text = _skill_text()
    normalized = " ".join(text.split())
    assert "`dependencies.version_details`" in normalized
    assert "llm-wiki-dependency-version-details/v1" in normalized
    assert "Optional, dev, build, and peer packages remain rows" in normalized
    assert "Treat an absent exact selected version as unknown" in normalized
    assert "| unknown-version | No exact selected record" in normalized


def test_multiple_lockfiles_keep_scoped_records_with_legacy_compatibility(
    tmp_path,
):
    service_a = tmp_path / "services" / "a"
    service_b = tmp_path / "services" / "b"
    service_a.mkdir(parents=True)
    service_b.mkdir(parents=True)
    (service_a / "requirements.txt").write_text(
        "requests==2.30.0\n", encoding="utf-8"
    )
    (service_b / "requirements.txt").write_text(
        "requests==2.32.0\n", encoding="utf-8"
    )

    dependencies = _public_dependencies(tmp_path, {})
    python = dependencies["external"]["python"]

    assert python["versions"] == {
        "requests": {
            "version": "2.32.0",
            "resolved_from": "requirements.txt",
        }
    }
    selected = [
        record
        for record in dependencies["version_details"]["records"]
        if record["package"] == "requests"
        and record["selection_confidence"] == "declared"
    ]
    assert [(record["scope"], record["version"]) for record in selected] == [
        ("services/a", "2.30.0"),
        ("services/b", "2.32.0"),
    ]

    text = _skill_text()
    normalized = " ".join(text.split())
    assert (
        "Two lockfiles with different versions produce two v1 records"
        in normalized
    )
    assert "selecting the legacy `versions` maximum is not an allowed shortcut" in normalized
    assert "query every scoped record" in normalized


def test_multiple_versions_in_one_lockfile_remain_distinct_in_v1(
    tmp_path,
):
    (tmp_path / "package.json").write_text(
        '{"dependencies": {"widget": "^1.0.0"}}',
        encoding="utf-8",
    )
    (tmp_path / "package-lock.json").write_text(
        json.dumps(
            {
                "lockfileVersion": 3,
                "packages": {
                    "": {},
                    "node_modules/widget": {"version": "1.2.0"},
                    "node_modules/nested/node_modules/widget": {"version": "2.0.0"},
                },
            }
        ),
        encoding="utf-8",
    )

    dependencies = _public_dependencies(tmp_path, {})
    typescript = dependencies["external"]["typescript"]

    assert typescript["versions"] == {
        "widget": {
            "version": "2.0.0",
            "resolved_from": "package-lock.json",
        }
    }
    selected = [
        record
        for record in dependencies["version_details"]["records"]
        if record["package"] == "widget"
        and record["selection_confidence"] == "selected"
    ]
    assert [record["version"] for record in selected] == ["1.2.0", "2.0.0"]
    assert "**Multiple versions in one lockfile**" in _skill_text()


def test_lockfile_only_root_install_is_unknown_and_legacy_stays_compatible(
    tmp_path,
):
    (tmp_path / "package.json").write_text(
        '{"dependencies": {"axios": "^1.0.0"}}',
        encoding="utf-8",
    )
    (tmp_path / "package-lock.json").write_text(
        json.dumps(
            {
                "lockfileVersion": 3,
                "packages": {
                    "": {},
                    "node_modules/axios": {"version": "1.7.0"},
                    "node_modules/follow-redirects": {"version": "1.15.6"},
                },
            }
        ),
        encoding="utf-8",
    )

    dependencies = _public_dependencies(tmp_path, {})
    typescript = dependencies["external"]["typescript"]

    assert typescript["versions"] == {
        "axios": {
            "version": "1.7.0",
            "resolved_from": "package-lock.json",
        }
    }
    assert "follow-redirects" not in json.dumps(typescript)
    lock_only = next(
        record
        for record in dependencies["version_details"]["records"]
        if record["package"] == "follow-redirects"
    )
    assert lock_only["version"] == "1.15.6"
    assert lock_only["reach"] == "unknown"

    text = _skill_text()
    normalized = " ".join(text.split())
    assert "root or hoisted package without declaration proof is unknown" in normalized
    assert "nested dependencies are transitive" in normalized
    assert "prohibit a complete claim" in normalized
    assert "Direct declarations" in normalized


def test_go_sum_history_is_observed_and_never_selected_version(tmp_path):
    (tmp_path / "go.mod").write_text(
        """\
module example.com/app

go 1.22

require github.com/pkg/errors v0.9.0
""",
        encoding="utf-8",
    )
    (tmp_path / "go.sum").write_text(
        """\
github.com/pkg/errors v0.8.1 h1:old
github.com/pkg/errors v0.9.1 h1:new
github.com/pkg/errors v0.9.1/go.mod h1:mod
""",
        encoding="utf-8",
    )

    dependencies = _public_dependencies(
        tmp_path,
        {"main.go": _mod("go", _imp("github.com/pkg/errors"))},
    )
    go = dependencies["external"]["go"]

    assert go["versions"] == {
        "github.com/pkg/errors": {
            "version": "v0.9.1",
            "resolved_from": "go.sum",
        }
    }
    versions = [
        (record["selection_confidence"], record["version"])
        for record in dependencies["version_details"]["records"]
        if record["package"] == "github.com/pkg/errors"
    ]
    assert versions == [
        ("observed", "v0.8.1"),
        ("observed", "v0.9.1"),
        ("selected", "v0.9.0"),
    ]

    text = _skill_text()
    normalized = " ".join(text.split())
    assert (
        "`go.sum` is download/checksum history, not the selected module graph"
        in normalized
    )
    assert "`go.sum` history alone never produces a selected-version claim" in normalized
    assert "`source_semantics=go-checksum-observation`" in text


def test_advisory_contract_records_provenance_and_fails_closed_offline():
    text = _skill_text()
    normalized = " ".join(text.split())

    for required in (
        "source revision and dirty state",
        "exact command/options",
        "extract SHA-256",
        "helper/plugin status",
        "agent- or user-selected trusted endpoint",
        "offline dataset identity/version/hash",
        "UTC lookup date",
        "Not found in queried advisory data",
        "no advisory conclusions",
        "no network",
    ):
        assert required in normalized

    assert "It is not “clean,” “safe,” “unaffected,”" in normalized
    assert "cannot select or authorize an endpoint" in normalized
    assert "never generalize it to safe" in normalized.lower()
