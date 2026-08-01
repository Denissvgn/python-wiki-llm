from __future__ import annotations

import json
import textwrap

from llm_wiki_cli.commands import extract_cmd
from llm_wiki_cli.services.dependencies import analyze_dependencies
from llm_wiki_cli.services.dependency_versions import (
    build_dependency_version_details,
)
from llm_wiki_cli.services.source_snapshot import build_source_snapshot


def _records(tmp_path):
    return build_dependency_version_details(tmp_path)["records"]


def test_python_monorepo_keeps_selected_versions_in_their_lock_scopes(tmp_path):
    for scope, version in (("api", "2.31.0"), ("worker", "2.32.0")):
        directory = tmp_path / scope
        directory.mkdir()
        (directory / "pyproject.toml").write_text(
            '[project]\ndependencies = ["requests>=2"]\n',
            encoding="utf-8",
        )
        (directory / "poetry.lock").write_text(
            f'[[package]]\nname = "requests"\nversion = "{version}"\n',
            encoding="utf-8",
        )

    selected = [
        record
        for record in _records(tmp_path)
        if record["package"] == "requests"
        and record["selection_confidence"] == "selected"
    ]

    assert [(record["scope"], record["version"]) for record in selected] == [
        ("api", "2.31.0"),
        ("worker", "2.32.0"),
    ]
    assert [record["source_path"] for record in selected] == [
        "api/poetry.lock",
        "worker/poetry.lock",
    ]
    assert all(record["reach"] == "direct" for record in selected)


def test_python_declaration_categories_and_missing_selection_are_explicit(tmp_path):
    (tmp_path / "pyproject.toml").write_text(
        textwrap.dedent(
            """\
            [project]
            dependencies = ["requests>=2"]

            [project.optional-dependencies]
            image = ["pillow"]

            [build-system]
            requires = ["setuptools>=68"]

            [tool.poetry.group.dev.dependencies]
            pytest = "^8"
            """
        ),
        encoding="utf-8",
    )

    details = build_dependency_version_details(tmp_path)
    records = details["records"]

    assert {
        (record["package"], record["declaration"])
        for record in records
    } == {
        ("pillow", "optional"),
        ("pytest", "dev"),
        ("requests", "required"),
        ("setuptools", "build"),
    }
    assert {
        record["selection_confidence"] for record in records
    } == {"declared"}
    assert {record["selection_state"] for record in records} == {"unknown"}
    assert "unknown-selection-without-lock-evidence" in details["coverage"][
        "limitations"
    ]


def test_uv_lock_omits_local_workspace_packages_and_keeps_member_reach_unknown(
    tmp_path,
):
    (tmp_path / "pyproject.toml").write_text(
        textwrap.dedent(
            """\
            [project]
            name = "workspace-root"
            version = "0.1.0"

            [tool.uv.workspace]
            members = ["packages/worker"]
            """
        ),
        encoding="utf-8",
    )
    worker = tmp_path / "packages" / "worker"
    worker.mkdir(parents=True)
    (worker / "pyproject.toml").write_text(
        textwrap.dedent(
            """\
            [project]
            name = "worker"
            version = "0.2.0"
            dependencies = ["requests>=2"]
            """
        ),
        encoding="utf-8",
    )
    (tmp_path / "uv.lock").write_text(
        textwrap.dedent(
            """\
            version = 1

            [[package]]
            name = "workspace-root"
            version = "0.1.0"
            source = { virtual = "." }

            [[package]]
            name = "worker"
            version = "0.2.0"
            source = { editable = "packages/worker" }

            [[package]]
            name = "requests"
            version = "2.32.3"
            source = { registry = "https://pypi.org/simple" }
            """
        ),
        encoding="utf-8",
    )

    selected = [
        record
        for record in _records(tmp_path)
        if record["selection_confidence"] == "selected"
    ]

    assert [
        (record["package"], record["version"], record["reach"])
        for record in selected
    ] == [("requests", "2.32.3", "unknown")]
    assert selected[0]["source_semantics"] == "uv-lock-selection"


def test_go_mod_selection_is_separate_from_all_go_sum_observations(tmp_path):
    (tmp_path / "go.mod").write_text(
        textwrap.dedent(
            """\
            module example.com/app

            require (
                github.com/pkg/errors v0.9.0
                golang.org/x/text v0.14.0 // indirect
            )
            """
        ),
        encoding="utf-8",
    )
    (tmp_path / "go.sum").write_text(
        textwrap.dedent(
            """\
            github.com/pkg/errors v0.8.1 h1:old
            github.com/pkg/errors v0.9.1 h1:new
            github.com/pkg/errors v0.9.1/go.mod h1:metadata
            """
        ),
        encoding="utf-8",
    )

    records = _records(tmp_path)
    errors = [
        record for record in records if record["package"] == "github.com/pkg/errors"
    ]

    assert [
        (record["selection_confidence"], record["version"])
        for record in errors
    ] == [
        ("observed", "v0.8.1"),
        ("observed", "v0.9.1"),
        ("selected", "v0.9.0"),
    ]
    assert all(
        record["source_semantics"] == "go-checksum-observation"
        and record["reach"] == "unknown"
        for record in errors
        if record["selection_confidence"] == "observed"
    )
    indirect = next(
        record for record in records if record["package"] == "golang.org/x/text"
    )
    assert indirect["selection_confidence"] == "selected"
    assert indirect["reach"] == "transitive"


def test_go_mod_replacements_preserve_requested_and_effective_versions(tmp_path):
    (tmp_path / "go.mod").write_text(
        textwrap.dedent(
            """\
            module example.com/app

            require (
                example.com/same v1.2.3
                example.com/original v2.0.0 // indirect
                example.com/local v3.0.0
                example.com/unchanged v4.0.0
            )

            replace example.com/same => example.com/same v1.2.4
            replace (
                example.com/original v2.0.0 => example.com/fork v2.1.0
                example.com/local => ../private/local-module
            )
            """
        ),
        encoding="utf-8",
    )

    details = build_dependency_version_details(tmp_path)
    records = details["records"]

    assert {
        (
            record["package"],
            record["version"],
            record["selection_confidence"],
            record["source_semantics"],
            record["reach"],
            record["declared_as"],
        )
        for record in records
    } == {
        (
            "example.com/same",
            "v1.2.3",
            "declared",
            "go-mod-requirement",
            "direct",
            None,
        ),
        (
            "example.com/same",
            "v1.2.4",
            "selected",
            "go-mod-replacement-selection",
            "direct",
            None,
        ),
        (
            "example.com/original",
            "v2.0.0",
            "declared",
            "go-mod-requirement",
            "transitive",
            None,
        ),
        (
            "example.com/fork",
            "v2.1.0",
            "selected",
            "go-mod-replacement-selection",
            "transitive",
            "example.com/original",
        ),
        (
            "example.com/local",
            "v3.0.0",
            "declared",
            "go-mod-requirement",
            "direct",
            None,
        ),
        (
            "example.com/unchanged",
            "v4.0.0",
            "selected",
            "go-mod-selection",
            "direct",
            None,
        ),
    }
    assert details["diagnostics"] == [
        {
            "source_path": "go.mod",
            "state": "partial",
            "reason": "go-local-replacement-version-unknown",
        }
    ]
    assert details["coverage"]["observed"] == 7
    assert details["coverage"]["emitted"] == 6
    assert details["coverage"]["omitted"] == 1
    assert "private/local-module" not in json.dumps(details, sort_keys=True)


def test_go_mod_local_replacement_with_version_is_malformed_and_path_private(
    tmp_path,
):
    (tmp_path / "go.mod").write_text(
        textwrap.dedent(
            """\
            module example.com/app
            require example.com/original v1.0.0
            replace example.com/original => ../private/local-module v1.2.3
            """
        ),
        encoding="utf-8",
    )

    details = build_dependency_version_details(tmp_path)

    assert [
        (
            record["package"],
            record["version"],
            record["selection_confidence"],
        )
        for record in details["records"]
    ] == [("example.com/original", "v1.0.0", "declared")]
    assert details["diagnostics"] == [
        {
            "source_path": "go.mod",
            "state": "partial",
            "reason": "malformed-go-replacement",
        }
    ]
    assert details["coverage"]["observed"] == 2
    assert details["coverage"]["emitted"] == 1
    assert details["coverage"]["omitted"] == 1
    assert "private/local-module" not in json.dumps(details, sort_keys=True)


def test_go_mod_ambiguous_and_unmatched_replacements_fail_closed(tmp_path):
    (tmp_path / "go.mod").write_text(
        textwrap.dedent(
            """\
            module example.com/app

            require example.com/original v1.0.0
            replace (
                example.com/original => example.com/fork v1.1.0
                example.com/original v1.0.0 => example.com/fork v1.2.0
                example.com/missing => example.com/other v2.0.0
                broken =>
            )
            """
        ),
        encoding="utf-8",
    )

    details = build_dependency_version_details(tmp_path)

    assert [
        (
            record["package"],
            record["version"],
            record["selection_confidence"],
        )
        for record in details["records"]
    ] == [("example.com/original", "v1.0.0", "declared")]
    assert {item["reason"] for item in details["diagnostics"]} == {
        "conflicting-go-replacement",
        "malformed-go-replacement",
        "unmatched-go-replacement",
    }
    assert details["coverage"]["observed"] == 5
    assert details["coverage"]["emitted"] == 1
    assert details["coverage"]["omitted"] == 4


def test_go_mod_malformed_replacement_makes_applicable_selection_unknown(
    tmp_path,
):
    (tmp_path / "go.mod").write_text(
        textwrap.dedent(
            """\
            module example.com/app
            require example.com/original v1.0.0
            replace example.com/original => example.com/fork v1.1.0
            replace broken =>
            """
        ),
        encoding="utf-8",
    )

    details = build_dependency_version_details(tmp_path)

    assert [
        (
            record["package"],
            record["version"],
            record["selection_confidence"],
        )
        for record in details["records"]
    ] == [("example.com/original", "v1.0.0", "declared")]
    assert {item["reason"] for item in details["diagnostics"]} == {
        "indeterminate-go-replacement-selection",
        "malformed-go-replacement",
    }
    assert details["coverage"] == {
        "observed": 3,
        "emitted": 1,
        "omitted": 2,
        "limit": None,
        "truncated": False,
        "limitations": [
            "declarations-do-not-prove-a-selected-version",
            "malformed-or-unsupported-version-records",
            "static-lock-analysis-does-not-claim-runtime-installation",
            "unknown-selection-without-lock-evidence",
        ],
    }


def test_requirements_unsupported_forms_are_counted_and_diagnostic(tmp_path):
    (tmp_path / "requirements.txt").write_text(
        textwrap.dedent(
            """\
            requests==2.32.0
            named @ https://example.invalid/named-1.0.tar.gz
            -r base.txt
            -rmore.txt
            --requirement nested.txt
            --requirement=other.txt
            -c constraints.txt
            -cmore-constraints.txt
            --constraint pins.txt
            --constraint=other-pins.txt
            -e .
            -e../local
            --editable ../other
            --editable=../third
            git+https://example.invalid/repo.git#egg=unnamed
            hg+https://example.invalid/repo
            https://example.invalid/archive.tar.gz
            file:///private/archive.whl
            """
        ),
        encoding="utf-8",
    )

    details = build_dependency_version_details(tmp_path)

    assert {
        (record["package"], record["version"])
        for record in details["records"]
    } == {
        ("named", None),
        ("requests", "2.32.0"),
    }
    assert details["coverage"]["observed"] == 18
    assert details["coverage"]["emitted"] == 2
    assert details["coverage"]["omitted"] == 16
    assert details["diagnostics"] == [
        {
            "source_path": "requirements.txt",
            "state": "partial",
            "reason": "unnamed-requirements-url-or-vcs",
        },
        {
            "source_path": "requirements.txt",
            "state": "partial",
            "reason": "unsupported-requirements-editable",
        },
        {
            "source_path": "requirements.txt",
            "state": "partial",
            "reason": "unsupported-requirements-indirection",
        },
    ]
    assert "/private/archive.whl" not in json.dumps(details, sort_keys=True)


def test_cargo_keeps_multiple_selected_versions_and_truthful_reach(tmp_path):
    (tmp_path / "Cargo.toml").write_text(
        textwrap.dedent(
            """\
            [package]
            name = "app"
            version = "0.1.0"

            [dependencies]
            serde = "1"
            tracing = { version = "0.1", optional = true }

            [dev-dependencies]
            insta = "1"

            [build-dependencies]
            cc = "1"
            """
        ),
        encoding="utf-8",
    )
    (tmp_path / "Cargo.lock").write_text(
        textwrap.dedent(
            """\
            [[package]]
            name = "serde"
            version = "1.0.180"

            [[package]]
            name = "serde"
            version = "1.0.197"

            [[package]]
            name = "syn"
            version = "2.0.60"
            """
        ),
        encoding="utf-8",
    )

    records = _records(tmp_path)
    selected = [
        record
        for record in records
        if record["selection_confidence"] == "selected"
    ]

    assert [
        (record["package"], record["version"], record["reach"])
        for record in selected
    ] == [
        ("serde", "1.0.180", "unknown"),
        ("serde", "1.0.197", "unknown"),
        ("syn", "2.0.60", "transitive"),
    ]
    assert {
        (record["package"], record["declaration"])
        for record in records
        if record["selection_confidence"] == "declared"
    } == {
        ("cc", "build"),
        ("insta", "dev"),
        ("serde", "required"),
        ("tracing", "optional"),
    }


def test_cargo_workspace_lock_omits_members_and_does_not_guess_member_reach(
    tmp_path,
):
    (tmp_path / "Cargo.toml").write_text(
        '[workspace]\nmembers = ["crates/api"]\nresolver = "2"\n',
        encoding="utf-8",
    )
    api = tmp_path / "crates" / "api"
    api.mkdir(parents=True)
    (api / "Cargo.toml").write_text(
        textwrap.dedent(
            """\
            [package]
            name = "api"
            version = "0.1.0"

            [dependencies]
            serde = "1"
            """
        ),
        encoding="utf-8",
    )
    (tmp_path / "Cargo.lock").write_text(
        textwrap.dedent(
            """\
            [[package]]
            name = "api"
            version = "0.1.0"

            [[package]]
            name = "serde"
            version = "1.0.197"
            source = "registry+https://github.com/rust-lang/crates.io-index"
            """
        ),
        encoding="utf-8",
    )

    selected = [
        record
        for record in _records(tmp_path)
        if record["selection_confidence"] == "selected"
    ]

    assert [
        (record["package"], record["version"], record["reach"])
        for record in selected
    ] == [("serde", "1.0.197", "unknown")]


def test_npm_and_pnpm_records_are_additive_and_do_not_collapse_versions(tmp_path):
    (tmp_path / "package.json").write_text(
        json.dumps(
            {
                "dependencies": {"react": "^18"},
                "optionalDependencies": {"sharp": "^0.33"},
                "devDependencies": {"vitest": "^1"},
            }
        ),
        encoding="utf-8",
    )
    (tmp_path / "package-lock.json").write_text(
        json.dumps(
            {
                "lockfileVersion": 3,
                "packages": {
                    "": {},
                    "node_modules/react": {"version": "18.2.0"},
                    "node_modules/a/node_modules/react": {"version": "17.0.2"},
                },
            }
        ),
        encoding="utf-8",
    )
    (tmp_path / "pnpm-lock.yaml").write_text(
        textwrap.dedent(
            """\
            lockfileVersion: '9.0'
            packages:
              react@18.3.0:
                resolution: {integrity: sha512-react}
              '@scope/pkg@2.1.0':
                resolution: {integrity: sha512-scoped}
            snapshots: {}
            """
        ),
        encoding="utf-8",
    )

    records = _records(tmp_path)
    react = [
        record
        for record in records
        if record["package"] == "react"
        and record["selection_confidence"] == "selected"
    ]

    assert [(record["version"], record["source_path"]) for record in react] == [
        ("17.0.2", "package-lock.json"),
        ("18.2.0", "package-lock.json"),
        ("18.3.0", "pnpm-lock.yaml"),
    ]
    assert [record["reach"] for record in react] == [
        "transitive",
        "direct",
        "unknown",
    ]
    assert {
        (record["package"], record["declaration"])
        for record in records
        if record["selection_confidence"] == "declared"
    } == {
        ("react", "required"),
        ("sharp", "optional"),
        ("vitest", "dev"),
    }


def test_package_lock_omits_project_rows_and_marks_hoisted_member_reach_unknown(
    tmp_path,
):
    (tmp_path / "package.json").write_text(
        json.dumps(
            {
                "name": "workspace-root",
                "version": "1.0.0",
                "workspaces": ["packages/web"],
            }
        ),
        encoding="utf-8",
    )
    web = tmp_path / "packages" / "web"
    web.mkdir(parents=True)
    (web / "package.json").write_text(
        json.dumps(
            {
                "name": "web",
                "version": "1.0.0",
                "dependencies": {"react": "^18"},
            }
        ),
        encoding="utf-8",
    )
    (tmp_path / "package-lock.json").write_text(
        json.dumps(
            {
                "lockfileVersion": 3,
                "packages": {
                    "": {"name": "workspace-root", "version": "1.0.0"},
                    "packages/web": {"name": "web", "version": "1.0.0"},
                    "node_modules/react": {"version": "18.2.0"},
                },
            }
        ),
        encoding="utf-8",
    )

    selected = [
        record
        for record in _records(tmp_path)
        if record["selection_confidence"] == "selected"
    ]

    assert [
        (record["package"], record["version"], record["reach"])
        for record in selected
    ] == [("react", "18.2.0", "unknown")]


def test_package_lock_uses_embedded_root_and_workspace_declarations(tmp_path):
    (tmp_path / "package-lock.json").write_text(
        json.dumps(
            {
                "lockfileVersion": 3,
                "packages": {
                    "": {
                        "dependencies": {"root-direct": "^1"},
                    },
                    "packages/web": {
                        "devDependencies": {"workspace-direct": "^2"},
                    },
                    "node_modules/root-direct": {"version": "1.0.0"},
                    "packages/web/node_modules/workspace-direct": {
                        "version": "2.0.0"
                    },
                    "node_modules/workspace-direct": {"version": "2.1.0"},
                    "node_modules/hoisted-unknown": {"version": "3.0.0"},
                    "node_modules/parent/node_modules/nested": {
                        "version": "4.0.0"
                    },
                    "node_modules/web": {
                        "link": True,
                        "resolved": "packages/web",
                    },
                },
            }
        ),
        encoding="utf-8",
    )

    details = build_dependency_version_details(tmp_path)

    assert [
        (record["package"], record["version"], record["reach"])
        for record in details["records"]
    ] == [
        ("hoisted-unknown", "3.0.0", "unknown"),
        ("nested", "4.0.0", "transitive"),
        ("root-direct", "1.0.0", "direct"),
        ("workspace-direct", "2.0.0", "direct"),
        ("workspace-direct", "2.1.0", "unknown"),
    ]
    assert not details["diagnostics"]


def test_package_lock_v1_requires_declaration_proof_for_direct_reach(tmp_path):
    (tmp_path / "package.json").write_text(
        json.dumps({"dependencies": {"proved-direct": "^1"}}),
        encoding="utf-8",
    )
    (tmp_path / "package-lock.json").write_text(
        json.dumps(
            {
                "lockfileVersion": 1,
                "dependencies": {
                    "proved-direct": {"version": "1.0.0"},
                    "unproved-top-level": {"version": "2.0.0"},
                    "parent": {
                        "version": "3.0.0",
                        "dependencies": {
                            "nested": {"version": "4.0.0"},
                        },
                    },
                },
            }
        ),
        encoding="utf-8",
    )

    selected = [
        record
        for record in _records(tmp_path)
        if record["selection_confidence"] == "selected"
    ]

    assert [
        (record["package"], record["version"], record["reach"])
        for record in selected
    ] == [
        ("nested", "4.0.0", "transitive"),
        ("parent", "3.0.0", "unknown"),
        ("proved-direct", "1.0.0", "direct"),
        ("unproved-top-level", "2.0.0", "unknown"),
    ]


def test_public_analysis_is_deterministic_relative_and_reports_partial_sources(
    tmp_path,
):
    (tmp_path / "package.json").write_text(
        '{"dependencies": {"react": "^18"}}',
        encoding="utf-8",
    )
    (tmp_path / "package-lock.json").write_text("{bad json", encoding="utf-8")
    snapshot = build_source_snapshot(tmp_path)

    first = analyze_dependencies(
        {},
        str(tmp_path),
        source_snapshot=snapshot,
    )["reconciliation"]["version_details"]
    second = analyze_dependencies(
        {},
        str(tmp_path),
        source_snapshot=snapshot,
    )["reconciliation"]["version_details"]

    assert first == second
    assert first["diagnostics"] == [
        {
            "source_path": "package-lock.json",
            "state": "malformed",
            "reason": "unsupported-or-malformed-records",
        }
    ]
    assert first["coverage"]["omitted"] == 1
    assert first["coverage"]["truncated"] is False
    assert str(tmp_path) not in json.dumps(first, sort_keys=True)

    public = extract_cmd._dependency_extract_block(
        analyze_dependencies({}, str(tmp_path))
    )
    assert public["version_details"]["schema_version"] == (
        "llm-wiki-dependency-version-details/v1"
    )
    assert public["version_details"]["records"] == first["records"]


def test_snapshot_backed_public_extract_captures_standalone_supported_sources(
    tmp_path,
):
    (tmp_path / "Pipfile").write_text(
        '[packages]\nrequests = "==2.31.0"\n',
        encoding="utf-8",
    )
    (tmp_path / "Pipfile.lock").write_text(
        json.dumps(
            {
                "default": {
                    "requests": {
                        "version": "==2.31.0",
                    }
                }
            }
        ),
        encoding="utf-8",
    )
    rust = tmp_path / "rust"
    rust.mkdir()
    (rust / "Cargo.toml").write_text(
        '[package]\nname = "app"\nversion = "0.1.0"\n'
        '[dependencies]\nserde = "1"\n',
        encoding="utf-8",
    )
    (rust / "Cargo.lock").write_text(
        '[[package]]\nname = "serde"\nversion = "1.0.197"\n',
        encoding="utf-8",
    )
    (tmp_path / "requirements-dev.txt").write_text(
        "pytest==8.3.0\n",
        encoding="utf-8",
    )
    snapshot = build_source_snapshot(tmp_path)

    details = build_dependency_version_details(
        tmp_path,
        source_snapshot=snapshot,
    )

    sources = {record["source_path"] for record in details["records"]}
    assert {
        "Pipfile",
        "Pipfile.lock",
        "requirements-dev.txt",
        "rust/Cargo.toml",
        "rust/Cargo.lock",
    } <= sources
    assert not details["diagnostics"]
