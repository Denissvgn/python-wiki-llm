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


def test_optional_package_without_version_disappears_from_public_extract_but_not_contract(
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

    python = _public_external(tmp_path, {})["python"]

    assert python == {
        "used": {},
        "undeclared": [],
        "unused": ["requests"],
    }
    assert "pytest" not in json.dumps(python)

    text = _skill_text()
    normalized = " ".join(text.split())
    assert "union of the raw declaration ledger" in normalized
    assert "Optional/dev/build packages must remain rows" in normalized
    assert "every row in the supported raw declaration ledger" in normalized
    assert "Treat an absent resolved/scoped version as unknown" in normalized
    assert "| unknown-version | No exact version, no scope mapping," in normalized


def test_multiple_lockfiles_collapse_versions_but_contract_requires_scoped_observations(
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

    python = _public_external(tmp_path, {})["python"]

    assert python["versions"] == {
        "requests": {
            "version": "2.32.0",
            "resolved_from": "requirements.txt",
        }
    }

    text = _skill_text()
    normalized = " ".join(text.split())
    assert (
        "Two lockfiles with different versions produce two scoped observations"
        in normalized
    )
    assert "selecting the public maximum is not an allowed shortcut" in normalized
    assert "query every reliable scoped version" in normalized


def test_multiple_versions_in_one_lockfile_collapse_and_remain_explicitly_bounded(
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

    typescript = _public_external(tmp_path, {})["typescript"]

    assert typescript["versions"] == {
        "widget": {
            "version": "2.0.0",
            "resolved_from": "package-lock.json",
        }
    }
    assert "**Multiple versions in one lockfile**" in _skill_text()


def test_lockfile_only_transitive_version_is_absent_from_public_projection(tmp_path):
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

    typescript = _public_external(tmp_path, {})["typescript"]

    assert typescript["versions"] == {
        "axios": {
            "version": "1.7.0",
            "resolved_from": "package-lock.json",
        }
    }
    assert "follow-redirects" not in json.dumps(typescript)

    text = _skill_text()
    normalized = " ".join(text.split())
    assert "Lockfile-only transitive dependencies are excluded" in normalized
    assert "Do not claim complete transitive coverage" in normalized
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

    go = _public_external(
        tmp_path,
        {"main.go": _mod("go", _imp("github.com/pkg/errors"))},
    )["go"]

    assert go["versions"] == {
        "github.com/pkg/errors": {
            "version": "v0.9.1",
            "resolved_from": "go.sum",
        }
    }

    text = _skill_text()
    normalized = " ".join(text.split())
    assert (
        "`go.sum` is download/checksum history, not the selected module graph"
        in normalized
    )
    assert "`go.sum` history alone never produces a selected-version claim" in normalized
    assert "observed-in-go.sum" in text


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
