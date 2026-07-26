"""Focused contract tests for the KNOW-104 evaluated-envelope builder."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
from collections.abc import Mapping
from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest

from llm_wiki_cli.services import knowledge_envelope
from llm_wiki_cli.services.knowledge_envelope import (
    AGGREGATE_INPUT_DOMAIN,
    CONFIGURATION_BASIS_UNKNOWN,
    CONSUMED_INPUT_KIND_PRECEDENCE,
    EVALUATED_ENVELOPE_VERSION,
    INVENTORY_HASH_EXTENSION,
    ConsumedInput,
    ConsumedInputKind,
    EnvelopeInputs,
    KnowledgeEnvelopeError,
    ProducerComponentInput,
    RepositoryEvidence,
    build_evaluated_envelope,
    build_producer_record,
    build_repository_record,
    collect_git_repository_evidence,
    consumed_inputs_from_captured_hashes,
    evaluated_envelope_to_payload,
    hash_aggregate_inputs,
    hash_component_configuration,
    hash_generation_options,
    hash_inventory,
    hash_markdown_snapshot,
    hash_source_snapshot,
    normalize_vcs_remote,
    plugin_producer_inputs,
    serialize_evaluated_envelope,
    validate_configured_public_identity,
)
from llm_wiki_cli.services.knowledge_evidence import is_valid_sha256, sha256_bytes
from llm_wiki_cli.services.knowledge_model import (
    REPOSITORY_IDENTITY_SOURCE_EXTENSION,
    ProducerRecord,
    RepositoryIdentitySource,
    RepositoryRecord,
    WorkingTreeState,
)
from tests.knowledge_fixtures import (
    producer_basis_fixtures,
    repository_identity_fixtures,
)

_REQUIRES_GIT = pytest.mark.skipif(
    shutil.which("git") is None,
    reason="Git is required for local repository-evidence integration tests",
)


def _base_repository() -> RepositoryRecord:
    return RepositoryRecord(
        identity="example.invalid/acme/envelope-fixture",
        evaluated_revision=f"git:{'a' * 40}",
        working_tree=WorkingTreeState.CLEAN,
        extensions={
            REPOSITORY_IDENTITY_SOURCE_EXTENSION: (
                RepositoryIdentitySource.CONFIGURED_PUBLIC.value
            )
        },
    )


def _base_inputs() -> EnvelopeInputs:
    return EnvelopeInputs(
        repository=_base_repository(),
        source_inputs=(
            ConsumedInput.from_bytes(
                "src/app.py",
                b"class App:\n    pass\n",
                kind=ConsumedInputKind.SOURCE,
            ),
            ConsumedInput.from_bytes(
                "pyproject.toml",
                b'[project]\nname = "fixture"\n',
                kind=ConsumedInputKind.PACKAGE,
            ),
        ),
        inventory={
            "src/app.py": {
                "language": "python",
                "classes": [{"name": "App", "kind": "class", "line": 1}],
                "functions": [],
            }
        },
        markdown_pages={
            "index.md": "# Fixture\n",
            "modules/app.md": "# app Module\n\nFixture.\n",
        },
        surface_index_bytes=b'{"schema_version":"llm-wiki-surface-index/v1"}\n',
        generation_options={"detail": "auto"},
        generation_option_defaults={
            "detail": "auto",
            "include_tests": [],
        },
        generation_option_allowlist=("detail", "include_tests"),
        tool=ProducerComponentInput(
            component_id="agent-wiki-cli",
            version="1.4.0",
            configuration={"knowledge_schema": "llm-wiki-knowledge/v1"},
        ),
        extractors=(
            ProducerComponentInput(
                component_id="python-ast",
                version="stdlib",
                configuration={"deep": True, "include_tests": False},
                limitations=("syntax-only",),
            ),
        ),
        plugins=(
            ProducerComponentInput(
                component_id="documentation-hooks/knowledge",
                version="1.0.0",
                configuration={"mode": "metadata-only"},
                limitations=("metadata-only",),
            ),
        ),
    )


def _snapshot_commitments(inputs: EnvelopeInputs) -> dict[str, str]:
    snapshot = build_evaluated_envelope(inputs).bundle.snapshot
    return {
        "source": snapshot.source_snapshot_hash,
        "inventory": snapshot.extensions[INVENTORY_HASH_EXTENSION],
        "markdown": snapshot.markdown_snapshot_hash,
        "surface": snapshot.surface_index_hash,
        "options": snapshot.generation_options_hash,
    }


def _assert_error(field: str, function, /, *args, **kwargs) -> KnowledgeEnvelopeError:
    with pytest.raises(KnowledgeEnvelopeError) as exc_info:
        function(*args, **kwargs)
    assert exc_info.value.field == field
    assert str(exc_info.value).startswith(f"{field}:")
    return exc_info.value


def _producer_input_from_wire(
    component: Mapping[str, Any],
) -> ProducerComponentInput:
    declared_configuration = component.get("configuration_hash")
    configuration = (
        {"fixture_configuration_hash": declared_configuration}
        if isinstance(declared_configuration, str)
        else None
    )
    return ProducerComponentInput(
        component_id=component["id"],
        version=component["version"],
        configuration=configuration,
        limitations=tuple(component.get("limitations", ())),
        extensions=component.get("extensions", {}),
    )


def _producer_from_fixture(bundle: Mapping[str, Any]) -> ProducerRecord:
    producer = bundle["producer"]
    return build_producer_record(
        tool=_producer_input_from_wire(producer["tool"]),
        extractors=tuple(
            _producer_input_from_wire(component)
            for component in producer.get("extractors", ())
        ),
        plugins=tuple(
            _producer_input_from_wire(component)
            for component in producer.get("plugins", ())
        ),
        extensions=producer.get("extensions", {}),
    )


def _git(repository: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=repository,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    assert result.returncode == 0, result.stderr
    return result.stdout.strip()


def _initialized_git_repository(repository: Path) -> str:
    repository.mkdir()
    _git(repository, "init", "--quiet")
    _git(repository, "config", "--local", "user.name", "Envelope Fixture")
    _git(
        repository,
        "config",
        "--local",
        "user.email",
        "envelope-fixture@example.invalid",
    )
    _git(repository, "config", "--local", "commit.gpgsign", "false")
    (repository / ".gitignore").write_text("ignored/\n", encoding="utf-8")
    (repository / "tracked.txt").write_text("tracked\n", encoding="utf-8")
    _git(repository, "add", ".gitignore", "tracked.txt")
    _git(repository, "commit", "--quiet", "-m", "initial")
    return _git(repository, "rev-parse", "HEAD")


def test_source_snapshot_hash_is_canonical_and_covers_every_consumed_kind():
    records = tuple(
        ConsumedInput.from_bytes(
            f"inputs/{kind.value}",
            f"{kind.value}\n".encode(),
            kind=kind,
        )
        for kind in ConsumedInputKind
    )

    first = hash_source_snapshot(records)
    second = hash_source_snapshot(reversed(records))

    assert first == second
    assert is_valid_sha256(first)
    assert (
        first
        == "sha256:d264bd2af9ceb1794445e4978248a0413934985b39e3ecc26347e17212c97c7b"
    )


def test_source_snapshot_hash_commits_to_kind_path_and_exact_content():
    baseline = ConsumedInput.from_bytes("src/app.py", b"print('one')\n")
    same_content_new_path = ConsumedInput.from_bytes("src/moved.py", b"print('one')\n")
    changed_content = ConsumedInput.from_bytes("src/app.py", b"print('two')\n")
    changed_kind = ConsumedInput.from_bytes(
        "src/app.py",
        b"print('one')\n",
        kind=ConsumedInputKind.SELECTION,
    )

    hashes = {
        hash_source_snapshot((item,))
        for item in (baseline, same_content_new_path, changed_content, changed_kind)
    }

    assert len(hashes) == 4


def test_source_snapshot_rejects_duplicate_coordinates_and_nonrecords():
    item = ConsumedInput.from_bytes("src/app.py", b"pass\n")

    _assert_error(
        "source_inputs[1]",
        hash_source_snapshot,
        (item, item),
    )
    _assert_error(
        "source_inputs[0]",
        hash_source_snapshot,
        ({"path": "src/app.py"},),
    )


def test_source_snapshot_rejects_one_path_reclassified_under_another_kind():
    source = ConsumedInput.from_bytes(
        "compose.yaml",
        b"services: {}\n",
        kind=ConsumedInputKind.COMPOSE,
    )
    reclassified = ConsumedInput.from_bytes(
        "compose.yaml",
        b"services: {}\n",
        kind=ConsumedInputKind.YAML,
    )

    error = _assert_error(
        "source_inputs[1]",
        hash_source_snapshot,
        (source, reclassified),
    )

    assert "duplicates consumed repository path compose.yaml" in str(error)


@pytest.mark.parametrize(
    ("kwargs", "field"),
    [
        (
            {"path": "/tmp/app.py", "content_hash": "sha256:" + ("a" * 64)},
            "source_inputs.path",
        ),
        (
            {"path": "../app.py", "content_hash": "sha256:" + ("a" * 64)},
            "source_inputs.path",
        ),
        (
            {"path": r"src\app.py", "content_hash": "sha256:" + ("a" * 64)},
            "source_inputs.path",
        ),
        (
            {"path": "src/app.py", "content_hash": "sha256:ABC"},
            "source_inputs.content_hash",
        ),
        (
            {
                "path": "src/app.py",
                "content_hash": "sha256:" + ("a" * 64),
                "kind": "Human readable",
            },
            "source_inputs.kind",
        ),
    ],
)
def test_consumed_inputs_reject_unsafe_fields(kwargs: dict[str, str], field: str):
    _assert_error(field, ConsumedInput, **kwargs)


def test_captured_hash_adapter_is_no_io_canonical_and_resolves_overlap():
    captured = {
        "src/app.py": sha256_bytes(b"pass\n"),
        "compose.yaml": sha256_bytes(b"services: {}\n"),
        ".gitignore": sha256_bytes(b"build/\n"),
    }
    candidates = {
        "src/app.py": (ConsumedInputKind.SOURCE,),
        "compose.yaml": (
            ConsumedInputKind.YAML,
            ConsumedInputKind.COMPOSE,
        ),
        ".gitignore": (
            "workspace-selection",
            ConsumedInputKind.SELECTION,
        ),
    }

    first = consumed_inputs_from_captured_hashes(captured, candidates)
    second = consumed_inputs_from_captured_hashes(
        dict(reversed(tuple(captured.items()))),
        {
            path: tuple(reversed(kinds))
            for path, kinds in reversed(tuple(candidates.items()))
        },
    )

    assert first == second
    assert [item.path for item in first] == [
        ".gitignore",
        "compose.yaml",
        "src/app.py",
    ]
    assert [item.kind_value for item in first] == [
        ConsumedInputKind.SELECTION.value,
        ConsumedInputKind.COMPOSE.value,
        ConsumedInputKind.SOURCE.value,
    ]
    assert CONSUMED_INPUT_KIND_PRECEDENCE[:2] == (
        ConsumedInputKind.OPENAPI,
        ConsumedInputKind.COMPOSE,
    )


def test_captured_hash_adapter_uses_deterministic_custom_kind_fallback():
    captured = {"metadata.cfg": sha256_bytes(b"mode=safe\n")}

    result = consumed_inputs_from_captured_hashes(
        captured,
        {"metadata.cfg": ("zeta-input", "alpha-input")},
    )

    assert result[0].kind_value == "alpha-input"


@pytest.mark.parametrize(
    ("hashes", "kinds", "field"),
    [
        ([], {}, "captured_content_hashes"),
        ({}, [], "captured_input_kinds"),
        (
            {"a.py": sha256_bytes(b"a")},
            {},
            "captured_inputs",
        ),
        (
            {"a.py": "sha256:bad"},
            {"a.py": ConsumedInputKind.SOURCE},
            "source_inputs.content_hash",
        ),
        (
            {"/Users/alice/repo/a.py": sha256_bytes(b"a")},
            {"/Users/alice/repo/a.py": b"bad"},
            "captured_inputs.path",
        ),
        (
            {"a.py": sha256_bytes(b"a")},
            {"a.py": ()},
            "captured_input_kinds.a.py",
        ),
        (
            {"a.py": sha256_bytes(b"a")},
            {"a.py": b"source"},
            "captured_input_kinds.a.py",
        ),
        (
            {"a.py": sha256_bytes(b"a")},
            {"a.py": "Human readable"},
            "captured_input_kinds.a.py",
        ),
    ],
)
def test_captured_hash_adapter_rejects_incomplete_or_malformed_input(
    hashes: object,
    kinds: object,
    field: str,
):
    _assert_error(
        field,
        consumed_inputs_from_captured_hashes,
        hashes,
        kinds,
    )


def test_inventory_hash_canonicalizes_mapping_order_but_preserves_arrays():
    first = {
        "src/b.py": {"functions": [], "language": "python"},
        "src/a.py": {
            "language": "python",
            "classes": [{"name": "A"}, {"name": "B"}],
        },
    }
    reordered = {
        "src/a.py": {
            "classes": [{"name": "A"}, {"name": "B"}],
            "language": "python",
        },
        "src/b.py": {"language": "python", "functions": []},
    }
    reversed_declarations = {
        **reordered,
        "src/a.py": {
            "classes": [{"name": "B"}, {"name": "A"}],
            "language": "python",
        },
    }

    assert hash_inventory(first) == hash_inventory(reordered)
    assert hash_inventory(reordered) != hash_inventory(reversed_declarations)


def test_inventory_hash_retains_slash_prefixed_semantic_prose_and_routes():
    inventory = {
        "src/client.ts": {
            "language": "typescript",
            "module_docstring": "/** HTTP client module. */",
            "routes": ["/things"],
        }
    }

    assert is_valid_sha256(hash_inventory(inventory))


@pytest.mark.parametrize(
    ("inventory", "field"),
    [
        ([], "inventory"),
        ({"/tmp/app.py": {}}, "inventory.source_path"),
        (
            {"src/app.py": {"score": float("nan")}},
            "inventory.src/app.py.score",
        ),
        ({"src/app.py": {1: "not-a-string-key"}}, "inventory.src/app.py"),
    ],
)
def test_inventory_hash_rejects_invalid_shapes(inventory: object, field: str):
    _assert_error(field, hash_inventory, inventory)


def test_markdown_hash_normalizes_newlines_and_canonicalizes_page_order():
    lf = {
        "index.md": "# Index\n\nHello\n",
        "modules/app.md": "# app\nLine\n",
    }
    mixed_newlines = {
        "modules/app.md": b"# app\rLine\r\n",
        "index.md": "# Index\r\n\r\nHello\r\n",
    }

    assert hash_markdown_snapshot(lf) == hash_markdown_snapshot(mixed_newlines)
    assert hash_markdown_snapshot(lf) != hash_markdown_snapshot(
        {**lf, "modules/app.md": "# app\nChanged\n"}
    )
    assert hash_markdown_snapshot(lf) != hash_markdown_snapshot(
        {
            "index.md": lf["index.md"],
            "modules/renamed.md": lf["modules/app.md"],
        }
    )


@pytest.mark.parametrize(
    ("pages", "field"),
    [
        ({"/tmp/index.md": "# Index\n"}, "markdown_pages.path"),
        ({"modules/app.txt": "# app\n"}, "markdown_pages.modules/app.txt"),
        ({"modules/app.md": b"\xff"}, "markdown_pages.modules/app.md"),
        ({"modules/app.md": "\ud800"}, "markdown_pages.modules/app.md"),
        ({"modules/app.md": 123}, "markdown_pages.modules/app.md"),
    ],
)
def test_markdown_hash_rejects_noncanonical_or_invalid_pages(
    pages: object,
    field: str,
):
    _assert_error(field, hash_markdown_snapshot, pages)


def test_generation_options_use_effective_defaults_and_canonical_allowlist():
    defaults = {"detail": "auto", "include_tests": []}

    omitted = hash_generation_options(
        {},
        defaults=defaults,
        allowlist=("include_tests", "detail"),
    )
    explicit = hash_generation_options(
        {"include_tests": [], "detail": "auto"},
        defaults=defaults,
        allowlist=("detail", "include_tests"),
    )
    changed = hash_generation_options(
        {"detail": "full"},
        defaults=defaults,
        allowlist=("detail", "include_tests"),
    )

    assert omitted == explicit
    assert changed != omitted


@pytest.mark.parametrize(
    ("values", "defaults", "allowlist", "field"),
    [
        ({"secret": "token"}, {}, (), "generation_options.secret"),
        ({}, {}, ("detail",), "generation_options.detail"),
        ({}, {"detail": "auto"}, ("detail", "detail"), "generation_option_allowlist"),
        (
            {"output": "/Users/alice/private"},
            {},
            ("output",),
            "generation_options.output",
        ),
        (
            {"detail": float("inf")},
            {},
            ("detail",),
            "generation_options.detail",
        ),
    ],
)
def test_generation_options_fail_closed_with_field_specific_errors(
    values: Mapping[str, Any],
    defaults: Mapping[str, Any],
    allowlist: tuple[str, ...],
    field: str,
):
    _assert_error(
        field,
        hash_generation_options,
        values,
        defaults=defaults,
        allowlist=allowlist,
    )


def test_scalar_text_is_not_treated_as_an_option_or_aggregate_iterable():
    _assert_error(
        "generation_option_allowlist",
        hash_generation_options,
        {"a": 1, "b": 2},
        defaults={},
        allowlist="ab",
    )
    _assert_error("aggregate_inputs", hash_aggregate_inputs, "contributors")
    _assert_error("aggregate_inputs", hash_aggregate_inputs, b"contributors")
    _assert_error("aggregate_inputs", hash_aggregate_inputs, {"unordered": True})
    _assert_error("aggregate_inputs", hash_aggregate_inputs, {"unordered"})


def test_surface_index_hash_uses_exact_persisted_bytes():
    baseline_inputs = _base_inputs()
    changed_inputs = replace(
        baseline_inputs,
        surface_index_bytes=baseline_inputs.surface_index_bytes + b" ",
    )

    baseline = build_evaluated_envelope(baseline_inputs)
    changed = build_evaluated_envelope(changed_inputs)

    assert baseline.bundle.snapshot.surface_index_hash == sha256_bytes(
        baseline_inputs.surface_index_bytes
    )
    assert changed.bundle.snapshot.surface_index_hash == sha256_bytes(
        changed_inputs.surface_index_bytes
    )
    assert (
        baseline.bundle.snapshot.surface_index_hash
        != changed.bundle.snapshot.surface_index_hash
    )


def test_aggregate_hash_preserves_order_and_multiplicity_and_is_domain_tagged():
    first = [{"locator": "a", "hash": "one"}, {"locator": "b", "hash": "two"}]
    reordered = list(reversed(first))

    baseline = hash_aggregate_inputs(first)

    assert baseline != hash_aggregate_inputs(reordered)
    assert baseline != hash_aggregate_inputs([*first, first[-1]])
    assert is_valid_sha256(hash_aggregate_inputs([]))
    assert baseline == sha256_bytes(
        json.dumps(
            {"domain": AGGREGATE_INPUT_DOMAIN, "inputs": first},
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
    )
    assert baseline != hash_inventory({"aggregate.json": {"inputs": first}})
    _assert_error(
        "aggregate_inputs[0].value",
        hash_aggregate_inputs,
        [{"value": float("nan")}],
    )


def test_component_configuration_is_canonical_and_rejects_local_paths():
    assert hash_component_configuration(
        {"deep": True, "nested": {"b": 2, "a": 1}}
    ) == hash_component_configuration({"nested": {"a": 1, "b": 2}, "deep": True})
    _assert_error(
        "configuration.cache_dir",
        hash_component_configuration,
        {"cache_dir": "/tmp/plugin-cache"},
    )


def test_producer_components_are_sorted_and_unknown_metadata_is_explicit():
    record = build_producer_record(
        tool=ProducerComponentInput("agent-wiki-cli", None, configuration={}),
        extractors=(
            ProducerComponentInput(
                "zeta",
                "2",
                configuration=None,
                limitations=("z-limit", "a-limit", "z-limit"),
            ),
            ProducerComponentInput("alpha", "1", configuration={}),
        ),
        plugins=(ProducerComponentInput("plugin-z", None, configuration=None),),
    )

    assert record.tool.version == "unknown"
    assert record.tool.limitations == ("version-unknown",)
    assert [component.component_id for component in record.extractors] == [
        "alpha",
        "zeta",
    ]
    assert record.extractors[1].configuration_hash is None
    assert record.extractors[1].limitations == (
        "a-limit",
        CONFIGURATION_BASIS_UNKNOWN,
        "z-limit",
    )
    assert record.plugins[0].version == "unknown"
    assert record.plugins[0].limitations == (
        CONFIGURATION_BASIS_UNKNOWN,
        "version-unknown",
    )


@pytest.mark.parametrize("unknown_version", [None, "unknown"])
def test_unknown_component_version_always_carries_version_unknown(
    unknown_version: str | None,
):
    record = build_producer_record(
        tool=ProducerComponentInput(
            "agent-wiki-cli",
            unknown_version,
            configuration={},
        ),
    )

    assert record.tool.version == "unknown"
    assert record.tool.limitations == ("version-unknown",)


def test_known_component_version_rejects_version_unknown_limitation():
    _assert_error(
        "producer.tool.limitations",
        build_producer_record,
        tool=ProducerComponentInput(
            "agent-wiki-cli",
            "1.4.0",
            configuration={},
            limitations=("version-unknown",),
        ),
    )


def test_scalar_text_is_not_treated_as_component_limitations():
    _assert_error(
        "producer.tool.limitations",
        build_producer_record,
        tool=ProducerComponentInput(
            "agent-wiki-cli",
            "1.4.0",
            configuration={},
            limitations="known",  # type: ignore[arg-type]
        ),
    )


def test_producer_component_errors_identify_the_boundary():
    _assert_error(
        "producer",
        build_producer_record,
        tool=ProducerComponentInput("same", "1", configuration={}),
        extractors=(ProducerComponentInput("same", "1", configuration={}),),
    )
    _assert_error(
        "producer.extractors[0].limitations",
        build_producer_record,
        tool=ProducerComponentInput("tool", "1", configuration={}),
        extractors=(
            ProducerComponentInput(
                "extractor",
                "1",
                configuration={},
                limitations=(CONFIGURATION_BASIS_UNKNOWN,),
            ),
        ),
    )
    _assert_error(
        "producer.tool.id",
        build_producer_record,
        tool=ProducerComponentInput("/absolute", "1", configuration={}),
    )


@pytest.mark.parametrize(
    "case", repository_identity_fixtures(), ids=lambda case: case.name
)
def test_repository_identity_policy_fixtures_drive_the_builder(case):
    record = build_repository_record(
        configured_public_identity=case.configured_public_identity,
        evidence=RepositoryEvidence(
            remotes=case.vcs_remotes,
            upstream_remote=case.upstream_remote,
        ),
    )

    assert record.identity == case.expected_identity
    assert record.identity_source is case.expected_source
    assert record.evaluated_revision == "unknown"
    assert record.working_tree is WorkingTreeState.UNKNOWN
    serialized = json.dumps(record.extensions, sort_keys=True).lower()
    for secret in ("alice", "access_token", "file://", "secret", "token", "users"):
        assert secret not in serialized


@pytest.mark.parametrize(
    ("remote", "expected"),
    [
        (
            "https://user:pass@GitHub.COM:443/Acme/Project.git?token=x#private",
            "github.com/Acme/Project",
        ),
        ("ssh://git@Code.Example:22/Acme/Project.git", "code.example/Acme/Project"),
        ("git@Code.Example:Acme/Project.git", "code.example/Acme/Project"),
        (
            "git@Code.Example:Acme/Project.git?token=secret#private",
            "code.example/Acme/Project",
        ),
        ("https://example.com:/acme/project.git", None),
        ("ssh://git@example.com:/acme/project.git", None),
        ("https://example.com:8443/acme/project.git", None),
        ("ssh://git@example.com:2222/acme/project.git", None),
        ("http://example.com/acme/project.git", None),
        ("file:///Users/alice/project.git", None),
        (r"C:\Users\alice\project", None),
        (r"\\server\share\project", None),
        ("https://example.com/acme/%ZZ", None),
        ("https://example.com/acme/%2E%2E/project", None),
        ("https://example.com//acme/project.git", None),
        ("https://example.com/acme/project.git//", None),
        ("https://example.com", None),
    ],
)
def test_vcs_remote_normalization_matrix(remote: str, expected: str | None):
    assert normalize_vcs_remote(remote) == expected


@pytest.mark.parametrize(
    "identity",
    [
        None,
        "",
        "unknown",
        "checkout",
        "GitHub.com/acme/project",
        "https://github.com/acme/project",
        "github.com/acme/project.git",
        "github.com/acme/project/",
        "github.com/acme/../project",
        "github.com/acme/project?private=1",
        "github.com/acme/project:22",
        r"github.com\acme\project",
        "/Users/alice/project",
    ],
)
def test_configured_identity_is_strict_and_never_silently_falls_back(identity):
    _assert_error(
        "configured_public_identity",
        validate_configured_public_identity,
        identity,
    )


def test_selected_missing_upstream_does_not_fall_back_to_origin():
    record = build_repository_record(
        evidence=RepositoryEvidence(
            remotes={"origin": "https://github.com/acme/project.git"},
            upstream_remote="missing",
        )
    )

    assert record.identity == "unknown"
    assert record.identity_source is RepositoryIdentitySource.UNKNOWN


def test_revision_and_worktree_evidence_are_independent_and_validated():
    revision = "b" * 64
    record = build_repository_record(
        evidence=RepositoryEvidence(
            evaluated_revision=revision,
            working_tree=WorkingTreeState.DIRTY,
        )
    )

    assert record.evaluated_revision == f"git:{revision}"
    assert record.working_tree is WorkingTreeState.DIRTY
    _assert_error(
        "evaluated_revision",
        build_repository_record,
        evidence=RepositoryEvidence(evaluated_revision="abc123"),
    )
    _assert_error(
        "working_tree",
        build_repository_record,
        evidence=RepositoryEvidence(working_tree="modified"),  # type: ignore[arg-type]
    )
    _assert_error(
        "evaluated_revision",
        build_repository_record,
        evidence=RepositoryEvidence(evaluated_revision=123),  # type: ignore[arg-type]
    )


def test_failed_upstream_evaluation_does_not_fall_back_to_origin():
    record = build_repository_record(
        evidence=RepositoryEvidence(
            remotes={"origin": "https://github.com/acme/project.git"},
            upstream_remote_evaluated=False,
        )
    )

    assert record.identity == "unknown"
    assert record.identity_source is RepositoryIdentitySource.UNKNOWN


@_REQUIRES_GIT
def test_git_collector_reports_clean_revision_remotes_and_upstream_precedence(
    tmp_path: Path,
):
    repository = tmp_path / "repository"
    revision = _initialized_git_repository(repository)
    _git(
        repository,
        "remote",
        "add",
        "origin",
        "https://mirror.example/Acme/Project.git",
    )
    _git(
        repository,
        "remote",
        "add",
        "upstream",
        "ssh://git@GitHub.com/Acme/Project.git",
    )
    branch = _git(repository, "symbolic-ref", "--quiet", "--short", "HEAD")
    _git(repository, "config", "--local", f"branch.{branch}.remote", "upstream")
    _git(
        repository,
        "config",
        "--local",
        f"branch.{branch}.merge",
        f"refs/heads/{branch}",
    )

    evidence = collect_git_repository_evidence(repository)
    record = build_repository_record(evidence=evidence)

    assert evidence.evaluated_revision == revision
    assert evidence.working_tree is WorkingTreeState.CLEAN
    assert evidence.remotes == {
        "origin": "https://mirror.example/Acme/Project.git",
        "upstream": "ssh://git@GitHub.com/Acme/Project.git",
    }
    assert evidence.upstream_remote == "upstream"
    assert record.identity == "github.com/Acme/Project"
    assert record.identity_source is RepositoryIdentitySource.NORMALIZED_VCS
    assert record.evaluated_revision == f"git:{revision}"
    assert record.working_tree is WorkingTreeState.CLEAN


@_REQUIRES_GIT
def test_git_collector_does_not_treat_stray_branch_remote_as_upstream(
    tmp_path: Path,
):
    repository = tmp_path / "repository"
    _initialized_git_repository(repository)
    _git(
        repository,
        "remote",
        "add",
        "origin",
        "https://github.com/Acme/Project.git",
    )
    _git(
        repository,
        "remote",
        "add",
        "stray",
        "https://stray.example/Acme/Project.git",
    )
    branch = _git(repository, "symbolic-ref", "--quiet", "--short", "HEAD")
    _git(repository, "config", "--local", f"branch.{branch}.remote", "stray")

    evidence = collect_git_repository_evidence(repository)
    record = build_repository_record(evidence=evidence)

    assert evidence.upstream_remote is None
    assert evidence.upstream_remote_evaluated is True
    assert record.identity == "github.com/Acme/Project"


@_REQUIRES_GIT
@pytest.mark.parametrize("dirty_kind", ["tracked", "staged", "untracked"])
def test_git_collector_reports_every_material_dirty_state(
    tmp_path: Path,
    dirty_kind: str,
):
    repository = tmp_path / "repository"
    revision = _initialized_git_repository(repository)

    if dirty_kind == "tracked":
        (repository / "tracked.txt").write_text("modified\n", encoding="utf-8")
    elif dirty_kind == "staged":
        (repository / "staged.txt").write_text("staged\n", encoding="utf-8")
        _git(repository, "add", "staged.txt")
    else:
        (repository / "untracked.txt").write_text("untracked\n", encoding="utf-8")

    evidence = collect_git_repository_evidence(repository)

    assert evidence.evaluated_revision == revision
    assert evidence.working_tree is WorkingTreeState.DIRTY


@_REQUIRES_GIT
def test_git_collector_ignores_ignored_only_entries(tmp_path: Path):
    repository = tmp_path / "repository"
    revision = _initialized_git_repository(repository)
    ignored = repository / "ignored"
    ignored.mkdir()
    (ignored / "cache.bin").write_bytes(b"local cache")

    evidence = collect_git_repository_evidence(repository)

    assert evidence.evaluated_revision == revision
    assert evidence.working_tree is WorkingTreeState.CLEAN


@_REQUIRES_GIT
def test_git_collector_excludes_only_selected_application_artifacts(
    tmp_path: Path,
):
    repository = tmp_path / "repository"
    _initialized_git_repository(repository)
    wiki_dir = repository / "docs" / "llm_wiki"
    wiki_dir.mkdir(parents=True)
    artifact_paths = tuple(
        wiki_dir / filename
        for filename in (
            ".llm-wiki-surface.json",
            ".llm-wiki-knowledge.json",
            ".llm-wiki-manifest.json",
        )
    )
    for path in artifact_paths:
        path.write_text("{}\n", encoding="utf-8")
    _git(repository, "add", "docs/llm_wiki")
    _git(repository, "commit", "--quiet", "-m", "track generated artifacts")

    artifact_paths[0].write_text('{"state": "staged"}\n', encoding="utf-8")
    artifact_paths[1].write_text('{"state": "tracked"}\n', encoding="utf-8")
    _git(repository, "add", "docs/llm_wiki/.llm-wiki-surface.json")

    excluded_only = collect_git_repository_evidence(
        repository,
        excluded_worktree_paths=artifact_paths,
    )
    assert excluded_only.working_tree is WorkingTreeState.CLEAN

    nearby_path = wiki_dir / ".llm-wiki-manifest.json.backup"
    nearby_path.write_text("{}\n", encoding="utf-8")
    with_nearby_change = collect_git_repository_evidence(
        repository,
        excluded_worktree_paths=artifact_paths,
    )
    assert with_nearby_change.working_tree is WorkingTreeState.DIRTY
    nearby_path.unlink()

    (repository / "unrelated.txt").write_text("untracked\n", encoding="utf-8")
    with_unrelated_change = collect_git_repository_evidence(
        repository,
        excluded_worktree_paths=artifact_paths,
    )
    assert with_unrelated_change.working_tree is WorkingTreeState.DIRTY


@_REQUIRES_GIT
def test_git_collector_resolves_exact_exclusions_from_nested_source_root(
    tmp_path: Path,
):
    repository = tmp_path / "repository"
    _initialized_git_repository(repository)
    source_root = repository / "packages" / "application"
    source_root.mkdir(parents=True)
    source_file = source_root / "app.py"
    source_file.write_text("VALUE = 1\n", encoding="utf-8")
    _git(repository, "add", "packages/application/app.py")
    _git(repository, "commit", "--quiet", "-m", "add nested source")

    wiki_dir = source_root / "docs" / "llm_wiki"
    wiki_dir.mkdir(parents=True)
    artifact_paths = tuple(
        wiki_dir / filename
        for filename in (
            ".llm-wiki-surface.json",
            ".llm-wiki-knowledge.json",
            ".llm-wiki-manifest.json",
        )
    )
    for artifact_path in artifact_paths:
        artifact_path.write_text("{}\n", encoding="utf-8")

    artifacts_only = collect_git_repository_evidence(
        source_root,
        excluded_worktree_paths=artifact_paths,
    )

    assert artifacts_only.working_tree is WorkingTreeState.CLEAN

    source_file.write_text("VALUE = 2\n", encoding="utf-8")
    source_dirty = collect_git_repository_evidence(
        source_root,
        excluded_worktree_paths=artifact_paths,
    )

    assert source_dirty.working_tree is WorkingTreeState.DIRTY


@_REQUIRES_GIT
def test_git_collector_distinguishes_non_git_and_unborn_repositories(
    tmp_path: Path,
):
    non_git = tmp_path / "non-git"
    non_git.mkdir()
    unborn = tmp_path / "unborn"
    unborn.mkdir()
    _git(unborn, "init", "--quiet")

    non_git_evidence = collect_git_repository_evidence(non_git)
    unborn_evidence = collect_git_repository_evidence(unborn)

    assert non_git_evidence == RepositoryEvidence()
    assert unborn_evidence.evaluated_revision is None
    assert unborn_evidence.working_tree is WorkingTreeState.CLEAN
    assert unborn_evidence.remotes == {}
    assert unborn_evidence.upstream_remote is None
    assert (
        build_repository_record(evidence=unborn_evidence).evaluated_revision
        == "unknown"
    )


@_REQUIRES_GIT
def test_git_collector_ignores_ambient_git_environment_overrides(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    repository = tmp_path / "repository"
    revision = _initialized_git_repository(repository)
    _git(
        repository,
        "remote",
        "add",
        "origin",
        "https://github.com/Acme/Project.git",
    )
    expected = collect_git_repository_evidence(repository)
    global_config = tmp_path / "ambient.gitconfig"
    global_config.write_text(
        '[remote "ambient"]\n'
        "    url = https://ambient.invalid/Injected/Repository.git\n"
        '[branch "ambient"]\n'
        "    remote = ambient\n"
        "    merge = refs/heads/ambient\n",
        encoding="utf-8",
    )
    fsmonitor_sentinel = tmp_path / "fsmonitor-invoked"
    if os.name != "nt":
        fsmonitor = tmp_path / "fsmonitor.sh"
        fsmonitor.write_text(
            f"#!/bin/sh\ntouch {fsmonitor_sentinel.as_posix()}\nexit 0\n",
            encoding="utf-8",
        )
        fsmonitor.chmod(0o755)
        _git(repository, "config", "--local", "core.fsmonitor", str(fsmonitor))

    monkeypatch.setenv("GIT_DIR", str(tmp_path / "hostile-git-dir"))
    monkeypatch.setenv("GIT_WORK_TREE", str(tmp_path / "hostile-work-tree"))
    monkeypatch.setenv("GIT_CONFIG_COUNT", "1")
    monkeypatch.setenv("GIT_CONFIG_KEY_0", "remote.origin.url")
    monkeypatch.setenv(
        "GIT_CONFIG_VALUE_0",
        "https://attacker.invalid/Injected/Repository.git",
    )
    monkeypatch.setenv("GIT_CEILING_DIRECTORIES", str(tmp_path))
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", str(global_config))

    observed = collect_git_repository_evidence(repository)

    assert observed == expected
    assert observed.evaluated_revision == revision
    assert observed.remotes == {
        "origin": "https://github.com/Acme/Project.git",
    }
    assert not fsmonitor_sentinel.exists()


@_REQUIRES_GIT
def test_git_collector_treats_failed_branch_evaluation_as_unknown_identity(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    repository = tmp_path / "repository"
    _initialized_git_repository(repository)
    _git(
        repository,
        "remote",
        "add",
        "origin",
        "https://github.com/Acme/Project.git",
    )
    original_run = subprocess.run

    def fail_symbolic_ref(command, *args, **kwargs):
        if "symbolic-ref" in command:
            raise subprocess.TimeoutExpired(command, timeout=15)
        return original_run(command, *args, **kwargs)

    monkeypatch.setattr(knowledge_envelope.subprocess, "run", fail_symbolic_ref)

    evidence = collect_git_repository_evidence(repository)
    record = build_repository_record(evidence=evidence)

    assert evidence.remotes_evaluated is True
    assert evidence.upstream_remote_evaluated is False
    assert record.identity == "unknown"
    assert record.identity_source is RepositoryIdentitySource.UNKNOWN


def test_complete_envelope_is_canonical_typed_and_byte_stable():
    inputs = _base_inputs()

    first = build_evaluated_envelope(inputs)
    second = build_evaluated_envelope(inputs)
    first_payload = evaluated_envelope_to_payload(first)
    first_bytes = serialize_evaluated_envelope(first)

    assert first == second
    assert first.schema_version == EVALUATED_ENVELOPE_VERSION
    assert first_payload == second.to_payload()
    assert first_bytes == second.to_json()
    assert first_bytes.endswith("\n")
    assert not first_bytes.endswith("\n\n")
    assert "\r" not in first_bytes
    assert (
        first.inventory_hash
        == (first.bundle.snapshot.extensions[INVENTORY_HASH_EXTENSION])
    )
    assert (
        first.content_hash()
        == "sha256:" + hashlib.sha256(first_bytes.encode("utf-8")).hexdigest()
    )
    assert (
        first.content_hash()
        == "sha256:f7221c699d53557c6c9ac2ca3c35684b367a055bafdcb65ae73999f87fd075f0"
    )


def test_equivalent_input_and_component_orderings_have_identical_envelopes():
    baseline = _base_inputs()
    reordered = replace(
        baseline,
        source_inputs=tuple(reversed(baseline.source_inputs)),
        inventory={
            source: {
                "functions": list(data["functions"]),
                "classes": [dict(reversed(tuple(data["classes"][0].items())))],
                "language": data["language"],
            }
            for source, data in reversed(tuple(baseline.inventory.items()))
        },
        markdown_pages=dict(reversed(tuple(baseline.markdown_pages.items()))),
        generation_option_defaults=dict(
            reversed(tuple(baseline.generation_option_defaults.items()))
        ),
        generation_option_allowlist=tuple(
            reversed(baseline.generation_option_allowlist)
        ),
        extractors=tuple(reversed(baseline.extractors)),
        plugins=tuple(reversed(baseline.plugins)),
    )

    first = build_evaluated_envelope(baseline)
    second = build_evaluated_envelope(reordered)

    assert first.to_payload() == second.to_payload()
    assert first.to_json() == second.to_json()
    assert first.content_hash() == second.content_hash()


def test_each_material_input_changes_only_its_snapshot_commitment():
    baseline = _base_inputs()
    changed_cases = {
        "source": replace(
            baseline,
            source_inputs=(
                ConsumedInput.from_bytes("src/app.py", b"class Changed: pass\n"),
                baseline.source_inputs[1],
            ),
        ),
        "inventory": replace(
            baseline,
            inventory={
                "src/app.py": {
                    "language": "python",
                    "classes": [{"name": "Changed", "kind": "class", "line": 1}],
                    "functions": [],
                }
            },
        ),
        "markdown": replace(
            baseline,
            markdown_pages={
                **baseline.markdown_pages,
                "modules/app.md": "# app Module\n\nChanged.\n",
            },
        ),
        "surface": replace(
            baseline,
            surface_index_bytes=baseline.surface_index_bytes + b" ",
        ),
        "options": replace(
            baseline,
            generation_options={"detail": "full"},
        ),
    }
    baseline_commitments = _snapshot_commitments(baseline)
    baseline_hash = build_evaluated_envelope(baseline).content_hash()

    for changed_name, changed_inputs in changed_cases.items():
        changed_commitments = _snapshot_commitments(changed_inputs)
        assert {
            name
            for name, value in changed_commitments.items()
            if value != baseline_commitments[name]
        } == {changed_name}
        assert build_evaluated_envelope(changed_inputs).content_hash() != baseline_hash


def test_producer_changes_leave_snapshot_hashes_stable_but_change_envelope():
    baseline = _base_inputs()
    changed_cases = (
        replace(
            baseline,
            tool=replace(baseline.tool, version="1.5.0"),
        ),
        replace(
            baseline,
            extractors=(
                replace(baseline.extractors[0], configuration={"deep": False}),
            ),
        ),
        replace(
            baseline,
            plugins=(replace(baseline.plugins[0], limitations=("partial-analysis",)),),
        ),
    )
    baseline_envelope = build_evaluated_envelope(baseline)
    baseline_snapshot = baseline_envelope.bundle.snapshot

    for changed_inputs in changed_cases:
        changed = build_evaluated_envelope(changed_inputs)
        assert changed.bundle.snapshot == baseline_snapshot
        assert changed.content_hash() != baseline_envelope.content_hash()


def test_mapping_order_in_extensions_is_canonical_but_array_order_is_material():
    baseline = _base_inputs()
    first = replace(
        baseline,
        bundle_extensions={
            "example.invalid/data": {
                "mapping": {"b": 2, "a": 1},
                "ordered": ["first", "second"],
            }
        },
    )
    mapping_reordered = replace(
        baseline,
        bundle_extensions={
            "example.invalid/data": {
                "ordered": ["first", "second"],
                "mapping": {"a": 1, "b": 2},
            }
        },
    )
    array_reordered = replace(
        mapping_reordered,
        bundle_extensions={
            "example.invalid/data": {
                "ordered": ["second", "first"],
                "mapping": {"a": 1, "b": 2},
            }
        },
    )

    assert (
        build_evaluated_envelope(first).to_json()
        == build_evaluated_envelope(mapping_reordered).to_json()
    )
    assert (
        build_evaluated_envelope(first).content_hash()
        != build_evaluated_envelope(array_reordered).content_hash()
    )


def test_absolute_paths_are_rejected_from_every_caller_extension_boundary():
    baseline = _base_inputs()
    extension = {"example.invalid/path": "/Users/alice/private"}
    cases = (
        (
            "repository.extensions.example.invalid/path",
            replace(
                baseline,
                repository=replace(
                    baseline.repository,
                    extensions={
                        **baseline.repository.extensions,
                        **extension,
                    },
                ),
            ),
        ),
        (
            "bundle_extensions.example.invalid/path",
            replace(baseline, bundle_extensions=extension),
        ),
        (
            "snapshot_extensions.example.invalid/path",
            replace(baseline, snapshot_extensions=extension),
        ),
        (
            "producer.extensions.example.invalid/path",
            replace(baseline, producer_extensions=extension),
        ),
        (
            "producer.tool.extensions.example.invalid/path",
            replace(
                baseline,
                tool=replace(baseline.tool, extensions=extension),
            ),
        ),
        (
            "producer.extractors[0].extensions.example.invalid/path",
            replace(
                baseline,
                extractors=(replace(baseline.extractors[0], extensions=extension),),
            ),
        ),
        (
            "producer.plugins[0].extensions.example.invalid/path",
            replace(
                baseline,
                plugins=(replace(baseline.plugins[0], extensions=extension),),
            ),
        ),
    )

    for field, inputs in cases:
        _assert_error(field, build_evaluated_envelope, inputs)


def test_absolute_nested_extension_keys_are_rejected_without_path_leakage():
    inputs = replace(
        _base_inputs(),
        bundle_extensions={
            "example.invalid/data": {
                "/Users/alice/private/repository": "value",
            }
        },
    )

    error = _assert_error(
        "bundle_extensions.example.invalid/data",
        build_evaluated_envelope,
        inputs,
    )

    assert "/Users/alice" not in str(error)


def test_inventory_extension_is_computed_and_conflicts_fail_closed():
    baseline = _base_inputs()
    computed = hash_inventory(baseline.inventory)
    matching = replace(
        baseline,
        snapshot_extensions={INVENTORY_HASH_EXTENSION: computed},
    )
    conflicting = replace(
        baseline,
        snapshot_extensions={
            INVENTORY_HASH_EXTENSION: "sha256:" + ("f" * 64),
        },
    )

    assert build_evaluated_envelope(matching).inventory_hash == computed
    _assert_error(
        f"snapshot_extensions.{INVENTORY_HASH_EXTENSION}",
        build_evaluated_envelope,
        conflicting,
    )


def test_inventory_sources_must_be_committed_by_the_source_snapshot():
    inputs = replace(
        _base_inputs(),
        inventory={"src/not-captured.py": {"language": "python"}},
    )

    _assert_error(
        "inventory.source_path",
        build_evaluated_envelope,
        inputs,
    )


def test_plugin_projection_keeps_only_safe_stable_metadata():
    raw_components = (
        {
            "plugin_id": "docs-plugin",
            "plugin_version": "2.0.0",
            "type": "extractor",
            "id": "zeta",
            "language": "python",
            "entry_point": "plugin:extract",
            "parallel_safe": True,
            "plugin_dir": "/Users/alice/private-plugin",
            "install_source": "https://user:token@example.invalid/private",
            "installed_at": "2026-07-25T10:00:00Z",
            "raw_settings": {"access_token": "secret"},
        },
        {
            "plugin_id": "docs-plugin",
            "plugin_version": "2.0.0",
            "type": "lint_rule",
            "id": "alpha",
            "entry_point": "plugin:lint",
        },
    )

    projected = plugin_producer_inputs(
        reversed(raw_components),
        plugin_configurations={"docs-plugin": {"mode": "safe"}},
        plugin_limitations={"docs-plugin": ("metadata-only",)},
    )

    assert len(projected) == 1
    plugin = projected[0]
    assert plugin.component_id == "docs-plugin"
    assert plugin.version == "2.0.0"
    assert plugin.configuration == {
        "components": [
            {
                "type": "extractor",
                "id": "zeta",
                "language": "python",
                "entry_point": "plugin:extract",
                "parallel_safe": True,
            },
            {
                "type": "lint_rule",
                "id": "alpha",
                "entry_point": "plugin:lint",
            },
        ],
        "settings": {"mode": "safe"},
    }
    record = build_producer_record(
        tool=ProducerComponentInput("agent-wiki-cli", "1.4.0", configuration={}),
        plugins=projected,
    )
    persisted = json.dumps(
        {
            "id": record.plugins[0].component_id,
            "version": record.plugins[0].version,
            "configuration_hash": record.plugins[0].configuration_hash,
            "limitations": record.plugins[0].limitations,
        },
        sort_keys=True,
    )
    for private in (
        "/Users/alice",
        "access_token",
        "installed_at",
        "private-plugin",
        "secret",
        "token@example",
    ):
        assert private not in persisted


def test_plugin_projection_is_order_stable_and_unknown_basis_is_explicit():
    components = (
        {
            "plugin_id": "zeta-plugin",
            "plugin_version": None,
            "type": "lint_rule",
            "id": "rule",
            "entry_point": "rules:check",
        },
        {
            "plugin_id": "alpha-plugin",
            "plugin_version": "1.0",
            "type": "skill",
            "id": "guide",
            "path": "SKILL.md",
        },
    )
    configurations = {"zeta-plugin": None, "alpha-plugin": {}}

    first = plugin_producer_inputs(
        components,
        plugin_configurations=configurations,
    )
    second = plugin_producer_inputs(
        reversed(components),
        plugin_configurations=configurations,
    )

    assert first == second
    assert [item.component_id for item in first] == [
        "alpha-plugin",
        "zeta-plugin",
    ]
    record = build_producer_record(
        tool=ProducerComponentInput("agent-wiki-cli", "1.4.0", configuration={}),
        plugins=first,
    )
    unknown = record.plugins[1]
    assert unknown.version == "unknown"
    assert unknown.configuration_hash is None
    assert unknown.limitations == (
        CONFIGURATION_BASIS_UNKNOWN,
        "version-unknown",
    )


def test_missing_plugin_safe_settings_entry_is_unknown_not_an_empty_basis():
    component = {
        "plugin_id": "docs-plugin",
        "plugin_version": "1.0.0",
        "type": "lint_rule",
        "id": "docs",
        "entry_point": "rules:check",
    }

    missing = plugin_producer_inputs((component,))
    explicit_empty = plugin_producer_inputs(
        (component,),
        plugin_configurations={"docs-plugin": {}},
    )
    missing_record = build_producer_record(
        tool=ProducerComponentInput("agent-wiki-cli", "1.4.0", configuration={}),
        plugins=missing,
    )
    explicit_record = build_producer_record(
        tool=ProducerComponentInput("agent-wiki-cli", "1.4.0", configuration={}),
        plugins=explicit_empty,
    )

    assert missing[0].configuration is None
    assert missing_record.plugins[0].configuration_hash is None
    assert missing_record.plugins[0].limitations == (CONFIGURATION_BASIS_UNKNOWN,)
    assert explicit_empty[0].configuration == {
        "components": [
            {
                "type": "lint_rule",
                "id": "docs",
                "entry_point": "rules:check",
            }
        ],
        "settings": {},
    }
    assert is_valid_sha256(explicit_record.plugins[0].configuration_hash)
    assert explicit_record.plugins[0].limitations == ()


def test_plugin_projection_errors_are_field_specific():
    _assert_error(
        "plugin_components[0].plugin_id",
        plugin_producer_inputs,
        ({"plugin_version": "1", "type": "skill", "id": "x"},),
    )
    _assert_error(
        "plugin_components.docs.version",
        plugin_producer_inputs,
        (
            {"plugin_id": "docs", "plugin_version": "1", "type": "skill", "id": "a"},
            {"plugin_id": "docs", "plugin_version": "2", "type": "skill", "id": "b"},
        ),
    )
    _assert_error(
        "plugin_components[1].id",
        plugin_producer_inputs,
        (
            {
                "plugin_id": "docs",
                "plugin_version": "1",
                "type": "lint_rule",
                "id": "same",
            },
            {
                "plugin_id": "docs",
                "plugin_version": "1",
                "type": "lint_rule",
                "id": "same",
            },
        ),
    )
    _assert_error(
        "plugin_configurations.unknown",
        plugin_producer_inputs,
        (
            {
                "plugin_id": "docs",
                "plugin_version": "1",
                "type": "lint_rule",
                "id": "docs",
            },
        ),
        plugin_configurations={"unknown": {}},
    )
    _assert_error(
        "plugin_limitations.unknown",
        plugin_producer_inputs,
        (
            {
                "plugin_id": "docs",
                "plugin_version": "1",
                "type": "lint_rule",
                "id": "docs",
            },
        ),
        plugin_limitations={"unknown": ("partial-analysis",)},
    )
    _assert_error(
        "plugin_limitations.docs",
        plugin_producer_inputs,
        (
            {
                "plugin_id": "docs",
                "plugin_version": "1",
                "type": "skill",
                "id": "guide",
            },
        ),
        plugin_limitations={"docs": "metadata-only"},
    )
    _assert_error(
        "plugin_components[0].parallel_safe",
        plugin_producer_inputs,
        (
            {
                "plugin_id": "docs",
                "plugin_version": "1",
                "type": "extractor",
                "id": "python",
                "parallel_safe": "yes",
            },
        ),
    )
    _assert_error(
        "plugin_components[0].path",
        plugin_producer_inputs,
        (
            {
                "plugin_id": "docs",
                "plugin_version": "1",
                "type": "skill",
                "id": "guide",
                "path": "/Users/alice/private/SKILL.md",
            },
        ),
    )


def test_existing_producer_basis_matrix_changes_only_producer_evidence():
    cases = {case.name: case for case in producer_basis_fixtures()}
    records = {
        name: _producer_from_fixture(case.bundle) for name, case in cases.items()
    }
    baseline = records["producer-baseline"]

    assert records["changed-extractor-version"].extractors[0].version != (
        baseline.extractors[0].version
    )
    assert records["changed-extractor-config"].extractors[0].configuration_hash != (
        baseline.extractors[0].configuration_hash
    )
    assert records["changed-plugin-version"].plugins[0].version != (
        baseline.plugins[0].version
    )
    assert records["changed-plugin-config"].plugins[0].configuration_hash != (
        baseline.plugins[0].configuration_hash
    )
    assert records["changed-plugin-limitations"].plugins[0].limitations != (
        baseline.plugins[0].limitations
    )
    unknown = records["unknown-plugin-configuration-basis"].plugins[0]
    assert unknown.configuration_hash is None
    assert CONFIGURATION_BASIS_UNKNOWN in unknown.limitations
    assert len({repr(record) for record in records.values()}) == len(records)


def test_builder_performs_no_filesystem_subprocess_or_git_collection(
    monkeypatch: pytest.MonkeyPatch,
):
    inputs = _base_inputs()

    def forbidden(*_args, **_kwargs):
        raise AssertionError("pure envelope builder attempted I/O")

    monkeypatch.setattr(knowledge_envelope.subprocess, "run", forbidden)
    monkeypatch.setattr(
        knowledge_envelope, "collect_git_repository_evidence", forbidden
    )
    monkeypatch.setattr(Path, "read_bytes", forbidden)
    monkeypatch.setattr(Path, "read_text", forbidden)
    monkeypatch.setattr(Path, "glob", forbidden)
    monkeypatch.setattr(Path, "rglob", forbidden)

    envelope = build_evaluated_envelope(inputs)

    assert is_valid_sha256(envelope.content_hash())


def test_builder_rejects_invalid_boundary_values_with_stable_fields():
    baseline = _base_inputs()

    _assert_error(
        "surface_index_bytes",
        build_evaluated_envelope,
        replace(baseline, surface_index_bytes="{}"),  # type: ignore[arg-type]
    )
    _assert_error(
        "repository",
        build_evaluated_envelope,
        replace(baseline, repository="unknown"),  # type: ignore[arg-type]
    )
    _assert_error(
        "bundle",
        build_evaluated_envelope,
        replace(
            baseline,
            bundle_extensions={"not-qualified": True},
        ),
    )


def test_absolute_checkout_roots_and_wall_clock_state_cannot_affect_output(
    tmp_path: Path,
):
    first_root = tmp_path / "First Checkout"
    second_root = tmp_path / "second-checkout"
    first_root.mkdir()
    second_root.mkdir()

    first = build_evaluated_envelope(_base_inputs())
    second = build_evaluated_envelope(_base_inputs())
    serialized = first.to_json()

    assert first.to_json() == second.to_json()
    assert first.content_hash() == second.content_hash()
    assert str(first_root) not in serialized
    assert str(second_root) not in serialized
    assert not {
        "created_at",
        "mtime",
        "mtime_ns",
        "timestamp",
        "updated_at",
    } & set(json.loads(serialized))
