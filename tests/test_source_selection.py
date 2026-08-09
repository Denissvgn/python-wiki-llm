"""Security, provenance, and snapshot parity for canonical source selection."""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

import pytest

from llm_wiki_cli.services import context_service, extraction_service
from llm_wiki_cli.services import source_selection as source_selection_module
from llm_wiki_cli.services import source_snapshot as source_snapshot_module
from llm_wiki_cli.services.extraction_service import (
    build_extract_payload,
    filter_source_diff,
)
from llm_wiki_cli.services.source_selection import (
    SOURCE_SELECTION_GENERATION_INPUT_KEY,
    SOURCE_SELECTION_IDENTITY_SCHEMA_VERSION,
    SOURCE_SELECTION_INPUTS_GENERATION_INPUT_KEY,
    SOURCE_SELECTION_PATH,
    SOURCE_SELECTION_SCHEMA_VERSION,
    SourceSelectionError,
    canonical_selection_payload,
    path_is_selected,
    resolve_source_selection,
    selection_fingerprint,
    source_selection_identity_from_generation_inputs,
    source_selection_inputs_from_generation_inputs,
    validate_persisted_source_selection_identity,
    with_source_selection_generation_input,
)
from llm_wiki_cli.services.source_snapshot import (
    SourceSnapshotError,
    build_source_snapshot,
    capture_source_selection_inputs,
)


def _write(root: Path, rel_path: str, content: str = "fixture\n") -> Path:
    path = root / rel_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def _policy_payload(
    include: list[object] | None = None,
    exclude: list[object] | None = None,
) -> dict[str, object]:
    return {
        "schema_version": SOURCE_SELECTION_SCHEMA_VERSION,
        "include": ["selected"] if include is None else include,
        "exclude": [] if exclude is None else exclude,
    }


def _write_policy(
    root: Path,
    *,
    include: list[object] | None = None,
    exclude: list[object] | None = None,
    rel_path: str = SOURCE_SELECTION_PATH,
    indent: int | None = 2,
) -> Path:
    path = root / rel_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            _policy_payload(include, exclude),
            ensure_ascii=False,
            indent=indent,
        )
        + "\n",
        encoding="utf-8",
    )
    return path


def _sha256(content: bytes) -> str:
    return "sha256:" + hashlib.sha256(content).hexdigest()


def test_no_configuration_preserves_broad_legacy_snapshot(tmp_path):
    _write(tmp_path, "selected/app.py", "def selected(): ...\n")
    _write(tmp_path, "tests/test_app.py", "def test_app(): ...\n")

    assert resolve_source_selection(tmp_path) is None
    snapshot = build_source_snapshot(tmp_path)

    assert snapshot.language_paths("python") == [
        "selected/app.py",
        "tests/test_app.py",
    ]
    assert snapshot.source_selection_policy is None
    assert snapshot.source_selection_path is None
    assert snapshot.source_selection_origin is None
    assert snapshot.source_selection_fingerprint is None
    assert snapshot.source_selection_identity is None


def test_default_policy_is_canonical_and_captures_raw_bytes_separately(tmp_path):
    _write(tmp_path, "z-root/z.py", "def z(): ...\n")
    _write(tmp_path, "a-root/a.py", "def a(): ...\n")
    policy_path = _write_policy(
        tmp_path,
        include=["z-root", "a-root"],
    )
    raw_content = policy_path.read_bytes()

    policy = resolve_source_selection(tmp_path)
    assert policy is not None
    assert policy.include == ("a-root", "z-root")
    assert policy.exclude == ()
    assert policy.path == SOURCE_SELECTION_PATH
    assert policy.origin == "default"
    assert policy.raw_content_hash == _sha256(raw_content)
    assert json.loads(canonical_selection_payload(policy)) == {
        "schema_version": SOURCE_SELECTION_SCHEMA_VERSION,
        "include": ["a-root", "z-root"],
        "exclude": [],
    }
    assert selection_fingerprint(policy) == policy.fingerprint

    snapshot = build_source_snapshot(tmp_path)
    assert snapshot.source_selection_path == SOURCE_SELECTION_PATH
    assert snapshot.source_selection_origin == "default"
    assert snapshot.source_selection_fingerprint == policy.fingerprint
    assert snapshot.source_selection_identity == policy.identity
    assert snapshot.captured_content_hashes[SOURCE_SELECTION_PATH] == _sha256(
        raw_content
    )
    assert snapshot.captured_input_kinds[SOURCE_SELECTION_PATH] == ("selection",)
    assert SOURCE_SELECTION_PATH not in snapshot.all_source_paths
    assert (
        snapshot.gitignore_fingerprint
        == build_source_snapshot(
            tmp_path,
            selection_policy=policy,
        ).gitignore_fingerprint
    )


def test_explicit_override_is_root_relative_and_has_explicit_origin(tmp_path):
    _write(tmp_path, "selected/app.py", "def app(): ...\n")
    _write_policy(tmp_path, rel_path="config/sources.json")

    assert resolve_source_selection(tmp_path) is None
    snapshot = build_source_snapshot(
        tmp_path,
        source_selection="config/sources.json",
    )

    assert snapshot.language_paths("python") == ["selected/app.py"]
    assert snapshot.source_selection_path == "config/sources.json"
    assert snapshot.source_selection_origin == "explicit"
    assert snapshot.source_selection_identity == {
        "schema_version": SOURCE_SELECTION_IDENTITY_SCHEMA_VERSION,
        "path": "config/sources.json",
        "fingerprint": snapshot.source_selection_fingerprint,
    }


@pytest.mark.parametrize(
    "override",
    (
        "../outside.json",
        "/absolute/policy.json",
        r"C:\policy.json",
        "config\\policy.json",
        "config//policy.json",
    ),
)
def test_explicit_override_cannot_escape_or_use_platform_spelling(tmp_path, override):
    _write(tmp_path, "selected/app.py")

    with pytest.raises(SourceSelectionError):
        resolve_source_selection(tmp_path, override)


def test_missing_explicit_override_never_falls_back_to_default(tmp_path):
    _write(tmp_path, "selected/app.py")
    _write_policy(tmp_path)

    with pytest.raises(SourceSelectionError, match="does not exist"):
        resolve_source_selection(tmp_path, "config/missing.json")


def test_formatting_and_list_order_change_raw_hash_not_semantic_fingerprint(
    tmp_path,
):
    _write(tmp_path, "alpha/a.py")
    _write(tmp_path, "beta/b.py")
    first_path = _write_policy(
        tmp_path,
        include=["beta", "alpha"],
        rel_path="config/first.json",
        indent=2,
    )
    second_path = _write_policy(
        tmp_path,
        include=["alpha", "beta"],
        rel_path="config/second.json",
        indent=None,
    )

    first = resolve_source_selection(tmp_path, "config/first.json")
    second = resolve_source_selection(tmp_path, "config/second.json")
    assert first is not None and second is not None
    assert first.fingerprint == second.fingerprint
    assert first.raw_content_hash != second.raw_content_hash
    assert first.identity != second.identity
    assert first.raw_content_hash == _sha256(first_path.read_bytes())
    assert second.raw_content_hash == _sha256(second_path.read_bytes())
    first_snapshot = build_source_snapshot(
        tmp_path, source_selection="config/first.json"
    )
    second_snapshot = build_source_snapshot(
        tmp_path, source_selection="config/second.json"
    )
    assert first_snapshot.gitignore_fingerprint == second_snapshot.gitignore_fingerprint
    assert (
        first_snapshot.captured_content_hashes["config/first.json"]
        != second_snapshot.captured_content_hashes["config/second.json"]
    )


@pytest.mark.parametrize(
    "raw_content",
    (
        "[]",
        '{"schema_version":"llm-wiki-source-selection/v1","include":["selected"]}',
        '{"schema_version":"llm-wiki-source-selection/v1",'
        '"include":["selected"],"exclude":[],"extra":true}',
        '{"schema_version":"llm-wiki-source-selection/v2",'
        '"include":["selected"],"exclude":[]}',
        '{"schema_version":"llm-wiki-source-selection/v1",'
        '"include":"selected","exclude":[]}',
        '{"schema_version":"llm-wiki-source-selection/v1","include":[],"exclude":[]}',
        '{"schema_version":"llm-wiki-source-selection/v1",'
        '"include":["selected",7],"exclude":[]}',
        '{"schema_version":"llm-wiki-source-selection/v1",'
        '"include":["selected"],"include":["selected"],"exclude":[]}',
        "\ufeff{}",
        "{not-json}",
    ),
)
def test_invalid_json_contract_fails_closed(tmp_path, raw_content):
    _write(tmp_path, "selected/app.py")
    policy_path = tmp_path / SOURCE_SELECTION_PATH
    policy_path.parent.mkdir(parents=True)
    policy_path.write_text(raw_content, encoding="utf-8")

    with pytest.raises(SourceSelectionError):
        resolve_source_selection(tmp_path)


def test_oversized_json_contract_fails_before_decode(tmp_path):
    _write(tmp_path, "selected/app.py")
    policy_path = tmp_path / SOURCE_SELECTION_PATH
    policy_path.parent.mkdir(parents=True)
    policy_path.write_bytes(b" " * (64 * 1024 + 1))

    with pytest.raises(SourceSelectionError, match="at most 65536"):
        resolve_source_selection(tmp_path)


@pytest.mark.parametrize(
    "invalid_path",
    (
        "/absolute",
        "../escape",
        "selected/../escape",
        "selected\\native",
        r"C:\device",
        "C:/drive",
        "//server/share",
        "selected//double",
        "selected/./dot",
        "selected/",
        ".",
        "selected/*.py",
        "selected/[ab].py",
        "selected/name:stream",
        "selected/con/file.py",
        "selected/control\u0000.py",
        "selected/control\u001f.py",
        "selected/trailing. ",
        "selected/e\u0301.py",
    ),
)
def test_policy_paths_are_literal_portable_and_normalized(tmp_path, invalid_path):
    _write(tmp_path, "selected/app.py")
    _write_policy(tmp_path, include=[invalid_path])

    with pytest.raises(SourceSelectionError):
        resolve_source_selection(tmp_path)


@pytest.mark.parametrize(
    ("include", "exclude"),
    (
        (["selected", "selected/pkg"], []),
        (["selected", "selected"], []),
        (["Selected", "selected"], []),
        (["selected"], ["outside"]),
        (["selected"], ["selected"]),
        (["selected"], ["selected/private", "selected/private/nested"]),
        (["a/one", "A/two"], []),
    ),
)
def test_overlaps_case_collisions_and_unowned_excludes_fail(
    tmp_path,
    include,
    exclude,
):
    _write(tmp_path, "selected/app.py")
    _write(tmp_path, "a/one/app.py")
    _write(tmp_path, "A/two/app.py")
    _write_policy(tmp_path, include=include, exclude=exclude)

    with pytest.raises(SourceSelectionError):
        resolve_source_selection(tmp_path)


def test_missing_include_roots_are_allowed_when_aggregate_is_readable(tmp_path):
    _write(tmp_path, "selected/app.py")
    _write_policy(tmp_path, include=["deleted", "selected"])

    policy = resolve_source_selection(tmp_path)
    assert policy is not None
    assert policy.include == ("deleted", "selected")

    _write_policy(tmp_path, include=["deleted", "also-deleted"])
    with pytest.raises(SourceSelectionError, match="at least one readable"):
        resolve_source_selection(tmp_path)


@pytest.mark.parametrize(
    ("include", "exclude", "create_directory"),
    (
        (["selected"], [], "selected"),
        (["selected"], ["selected/private"], None),
        (["missing", "also-missing"], [], None),
    ),
)
def test_policy_requires_an_effective_regular_file_after_excludes(
    tmp_path,
    include,
    exclude,
    create_directory,
):
    if create_directory is not None:
        (tmp_path / create_directory).mkdir(parents=True)
    if exclude:
        _write(tmp_path, "selected/private/app.py")
    _write_policy(tmp_path, include=include, exclude=exclude)

    with pytest.raises(SourceSelectionError, match="readable regular file"):
        resolve_source_selection(tmp_path)


def test_selected_filesystem_case_collision_is_rejected_portably(
    tmp_path,
    monkeypatch,
):
    first = _write(tmp_path, "selected/Foo.py")
    second = _write(tmp_path, "selected/foo.py")
    _write_policy(tmp_path)
    if len(list((tmp_path / "selected").iterdir())) == 1:
        original = source_selection_module._bounded_directory_entries

        class _CaseVariantEntry:
            def __init__(self, name, path):
                self.name = name
                self.path = str(path)

        def case_variant_entries(directory, **kwargs):
            if directory == tmp_path / "selected":
                return [
                    _CaseVariantEntry("Foo.py", first),
                    _CaseVariantEntry("foo.py", second),
                ]
            return original(directory, **kwargs)

        monkeypatch.setattr(
            source_selection_module,
            "_bounded_directory_entries",
            case_variant_entries,
        )

    with pytest.raises(SourceSelectionError, match="collide across supported"):
        resolve_source_selection(tmp_path)


def test_policy_path_and_include_component_case_must_be_consistent(tmp_path):
    _write(tmp_path, "Config/app.py")
    _write_policy(
        tmp_path,
        include=["Config"],
        rel_path="config/source-selection.json",
    )

    with pytest.raises(SourceSelectionError, match="filesystem case|inconsistent case"):
        resolve_source_selection(tmp_path, "config/source-selection.json")


def test_filesystem_case_mismatch_fails_instead_of_platform_broadening(tmp_path):
    _write(tmp_path, "selected/app.py")
    _write_policy(tmp_path, include=["Selected"])

    with pytest.raises(SourceSelectionError, match="filesystem case"):
        resolve_source_selection(tmp_path)


def test_policy_filters_every_snapshot_bucket_and_intersects_only_files(tmp_path):
    _write(tmp_path, ".gitignore", "ignored-root/\n")
    _write(tmp_path, "selected/.gitignore", "ignored.py\n")
    _write(tmp_path, "selected/app.py", "def app(): ...\n")
    _write(tmp_path, "selected/ignored.py", "def ignored(): ...\n")
    _write(tmp_path, "selected/ui.ts", "export const ui = true;\n")
    _write(tmp_path, "selected/tool.sh", "#!/bin/sh\n")
    _write(tmp_path, "selected/Dockerfile", "FROM scratch\n")
    _write(tmp_path, "selected/compose.yml", "services: {}\n")
    _write(tmp_path, "selected/action.yaml", "name: action\n")
    _write(tmp_path, "selected/package.json", "{}\n")
    _write(tmp_path, "selected/private/private.py", "def private(): ...\n")
    _write(tmp_path, "outside/out.py", "def out(): ...\n")
    _write(tmp_path, "outside/Dockerfile", "FROM scratch\n")
    _write(tmp_path, "outside/package.json", "{}\n")
    _write_policy(tmp_path, exclude=["selected/private"])

    snapshot = build_source_snapshot(tmp_path)

    assert snapshot.language_paths("python") == ["selected/app.py"]
    assert snapshot.language_paths("typescript") == ["selected/ui.ts"]
    assert snapshot.unsupported_language_paths("shell") == ["selected/tool.sh"]
    assert [item.rel_path for item in snapshot.dockerfile_candidates] == [
        "selected/Dockerfile"
    ]
    assert [item.rel_path for item in snapshot.compose_candidates] == [
        "selected/compose.yml"
    ]
    assert [item.rel_path for item in snapshot.yaml_candidates] == [
        "selected/action.yaml",
        "selected/compose.yml",
    ]
    assert [item.rel_path for item in snapshot.package_markers] == [
        "selected/package.json"
    ]
    assert set(snapshot.captured_input_kinds) >= {
        ".gitignore",
        SOURCE_SELECTION_PATH,
        "selected/.gitignore",
        "selected/app.py",
        "selected/ui.ts",
    }
    assert not any(
        path.startswith("outside/") for path in snapshot.captured_input_kinds
    )
    assert not any(
        path.startswith("selected/private/") for path in snapshot.captured_input_kinds
    )

    restricted = build_source_snapshot(
        tmp_path,
        only_files=["selected/app.py", "outside/out.py"],
    )
    assert restricted.language_paths("python") == ["selected/app.py"]
    assert restricted.language_paths("typescript") == []
    assert [item.rel_path for item in restricted.dockerfile_candidates] == [
        "selected/Dockerfile"
    ]
    assert [item.rel_path for item in restricted.package_markers] == [
        "selected/package.json"
    ]


def test_configured_selection_fails_when_every_regular_file_is_ignored(tmp_path):
    _write(tmp_path, "selected/.gitignore", "*.py\n")
    _write(tmp_path, "selected/app.py")
    _write_policy(tmp_path)

    with pytest.raises(SourceSnapshotError, match="effectively empty"):
        build_source_snapshot(tmp_path)


def test_configured_ignored_package_markers_are_not_captured(tmp_path):
    _write(
        tmp_path,
        "selected/.gitignore",
        "Cargo.toml\nCargo.lock\npackage-lock.json\n",
    )
    _write(tmp_path, "selected/app.py")
    _write(tmp_path, "selected/Cargo.toml", "[package]\nname='decoy'\n")
    _write(tmp_path, "selected/Cargo.lock", "decoy\n")
    _write(tmp_path, "selected/package-lock.json", '{"name":"decoy"}\n')
    _write_policy(tmp_path)

    snapshot = build_source_snapshot(tmp_path)

    assert snapshot.language_paths("python") == ["selected/app.py"]
    assert [item.rel_path for item in snapshot.package_markers] == []
    assert not any(
        path.endswith(("Cargo.toml", "Cargo.lock", "package-lock.json"))
        for path in snapshot.captured_content_hashes
    )


def test_configured_applicable_gitignore_read_failure_is_closed(
    tmp_path,
    monkeypatch,
):
    gitignore = _write(tmp_path, "selected/.gitignore", "ignored.py\n")
    _write(tmp_path, "selected/app.py")
    _write_policy(tmp_path)
    original = Path.read_bytes

    def guarded_read_bytes(path):
        if path == gitignore:
            raise PermissionError("denied")
        return original(path)

    monkeypatch.setattr(Path, "read_bytes", guarded_read_bytes)

    with pytest.raises(SourceSnapshotError, match="cannot read applicable"):
        build_source_snapshot(tmp_path)


def test_configured_applicable_gitignore_link_is_closed_but_excluded_is_irrelevant(
    tmp_path,
):
    _write(tmp_path, "selected/app.py")
    foreign = _write(tmp_path, "foreign.ignore", "*.py\n")
    applicable = tmp_path / ".gitignore"
    try:
        applicable.symlink_to(foreign)
    except (NotImplementedError, OSError):
        pytest.skip("symlinks unavailable")
    _write_policy(tmp_path)

    with pytest.raises(SourceSnapshotError, match="selection input.*symlink"):
        build_source_snapshot(tmp_path)

    applicable.unlink()
    excluded = tmp_path / "selected/private/.gitignore"
    excluded.parent.mkdir(parents=True)
    excluded.symlink_to(foreign)
    _write_policy(tmp_path, exclude=["selected/private"])

    assert build_source_snapshot(tmp_path).language_paths("python") == [
        "selected/app.py"
    ]


def test_configured_applicable_gitignore_reparse_is_closed(
    tmp_path,
    monkeypatch,
):
    _write(tmp_path, ".gitignore", "outside/\n")
    _write(tmp_path, "selected/app.py")
    _write_policy(tmp_path)
    original = source_snapshot_module.path_is_link_or_reparse

    def fake_reparse(path):
        if path == tmp_path / ".gitignore":
            return True
        return original(path)

    monkeypatch.setattr(
        source_snapshot_module,
        "path_is_link_or_reparse",
        fake_reparse,
    )

    with pytest.raises(SourceSnapshotError, match="selection input.*reparse"):
        build_source_snapshot(tmp_path)


def test_plugin_capture_drops_valid_out_of_policy_paths_without_hash_leak(tmp_path):
    selected = _write(tmp_path, "selected/plugin.custom", "selected\n")
    _write(tmp_path, "outside/plugin.custom", "outside\n")
    _write(tmp_path, "selected/private/plugin.custom", "private\n")
    _write_policy(tmp_path, exclude=["selected/private"])

    snapshot = build_source_snapshot(tmp_path).with_captured_inventory_paths(
        [
            "outside/plugin.custom",
            "selected/private/plugin.custom",
            "selected/plugin.custom",
        ]
    )

    assert "selected/plugin.custom" in snapshot.all_source_paths
    assert snapshot.captured_content_hashes["selected/plugin.custom"] == _sha256(
        selected.read_bytes()
    )
    assert "outside/plugin.custom" not in snapshot.captured_content_hashes
    assert "selected/private/plugin.custom" not in snapshot.captured_content_hashes
    assert snapshot.source_selection_policy is not None


def test_plugin_capture_keeps_legacy_virtual_inventory_compatibility(tmp_path):
    plugin = _write(tmp_path, "outside/plugin.custom", "outside\n")

    snapshot = build_source_snapshot(tmp_path).with_captured_inventory_paths(
        ["outside/plugin.custom"]
    )

    assert snapshot.captured_content_hashes["outside/plugin.custom"] == _sha256(
        plugin.read_bytes()
    )


def test_plugin_capture_rejects_selected_ancestor_symlink_created_after_snapshot(
    tmp_path,
):
    _write(tmp_path, "selected/app.py")
    _write_policy(tmp_path)
    snapshot = build_source_snapshot(tmp_path)
    target = tmp_path / "target"
    _write(target, "plugin.custom")
    link = tmp_path / "selected/link"
    try:
        link.symlink_to(target, target_is_directory=True)
    except (NotImplementedError, OSError):
        pytest.skip("symlinks unavailable")

    with pytest.raises(SourceSnapshotError, match="traverse a symlink"):
        snapshot.with_captured_inventory_paths(["selected/link/plugin.custom"])


def test_selected_file_symlink_fails_closed_but_excluded_symlink_is_not_followed(
    tmp_path,
):
    _write(tmp_path, "selected/app.py")
    foreign = tmp_path / "foreign.py"
    foreign.write_text("def foreign(): ...\n", encoding="utf-8")
    _write_policy(tmp_path)
    link = tmp_path / "selected/link.py"
    try:
        link.symlink_to(foreign)
    except (NotImplementedError, OSError):
        pytest.skip("symlinks unavailable")

    with pytest.raises(SourceSnapshotError, match="symlink or reparse"):
        build_source_snapshot(tmp_path)

    link.unlink()
    foreign_dir = tmp_path / "foreign-dir"
    _write(foreign_dir, "secret.py")
    _write(tmp_path, "selected/.gitignore", "ignored-link/\n")
    ignored_link = tmp_path / "selected/ignored-link"
    ignored_link.symlink_to(foreign_dir, target_is_directory=True)
    with pytest.raises(SourceSnapshotError, match="symlink or reparse"):
        build_source_snapshot(tmp_path)
    ignored_link.unlink()

    private_link = tmp_path / "selected/private"
    private_link.symlink_to(foreign_dir, target_is_directory=True)
    _write_policy(tmp_path, exclude=["selected/private"])

    snapshot = build_source_snapshot(tmp_path)
    assert snapshot.language_paths("python") == ["selected/app.py"]


def test_selected_root_and_config_symlinks_fail_closed(tmp_path):
    real_selected = tmp_path / "real-selected"
    _write(real_selected, "app.py")
    selected_link = tmp_path / "selected"
    try:
        selected_link.symlink_to(real_selected, target_is_directory=True)
    except (NotImplementedError, OSError):
        pytest.skip("symlinks unavailable")
    _write_policy(tmp_path)

    with pytest.raises(SourceSelectionError, match="symlink or reparse"):
        resolve_source_selection(tmp_path)

    selected_link.unlink()
    selected_link.mkdir()
    _write(selected_link, "app.py")
    real_policy = _write_policy(tmp_path, rel_path="real-policy.json")
    default_policy = tmp_path / SOURCE_SELECTION_PATH
    default_policy.unlink()
    default_policy.symlink_to(real_policy)

    with pytest.raises(SourceSelectionError, match="symlink or reparse"):
        resolve_source_selection(tmp_path)


def test_stale_or_different_prebuilt_policy_is_rejected(tmp_path):
    _write(tmp_path, "selected/app.py")
    policy_path = _write_policy(tmp_path)
    policy = resolve_source_selection(tmp_path)
    assert policy is not None

    policy_path.write_text(
        json.dumps(_policy_payload(), separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    with pytest.raises(SourceSnapshotError, match="does not match"):
        build_source_snapshot(tmp_path, selection_policy=policy)

    current = resolve_source_selection(tmp_path)
    assert current is not None
    _write_policy(tmp_path, rel_path="config/other.json")
    with pytest.raises(SourceSnapshotError, match="does not match"):
        build_source_snapshot(
            tmp_path,
            source_selection="config/other.json",
            selection_policy=current,
        )

    policy_path.unlink()
    with pytest.raises(SourceSnapshotError, match="readable explicit"):
        build_source_snapshot(tmp_path, selection_policy=current)


def test_prebuilt_policy_must_belong_to_snapshot_root(tmp_path):
    first = tmp_path / "first"
    second = tmp_path / "second"
    _write(first, "selected/app.py")
    _write(second, "selected/app.py")
    _write_policy(first)
    _write_policy(second)
    policy = resolve_source_selection(first)
    assert policy is not None

    with pytest.raises(SourceSnapshotError, match="same resolved source root"):
        build_source_snapshot(second, selection_policy=policy)


def test_generation_input_helpers_preserve_siblings_and_validate_identity(tmp_path):
    _write(tmp_path, "selected/app.py")
    _write_policy(tmp_path)
    policy = resolve_source_selection(tmp_path)
    assert policy is not None
    snapshot = build_source_snapshot(tmp_path, selection_policy=policy)
    siblings: dict[str, object] = {"runtime": {"jobs": 1}}

    merged = with_source_selection_generation_input(
        siblings,
        policy.identity,
        snapshot.source_selection_inputs,
    )

    assert siblings == {"runtime": {"jobs": 1}}
    assert merged["runtime"] == {"jobs": 1}
    assert merged[SOURCE_SELECTION_GENERATION_INPUT_KEY] == policy.identity
    assert source_selection_identity_from_generation_inputs(merged) == policy.identity
    assert with_source_selection_generation_input(merged, None) == siblings
    assert source_selection_identity_from_generation_inputs(siblings) is None
    assert source_selection_identity_from_generation_inputs(None) is None

    malformed = dict(merged)
    malformed[SOURCE_SELECTION_GENERATION_INPUT_KEY] = {
        **policy.identity,
        "unknown": True,
    }
    with pytest.raises(SourceSelectionError, match="unknown"):
        source_selection_identity_from_generation_inputs(malformed)
    with pytest.raises(SourceSelectionError, match="sha256"):
        with_source_selection_generation_input(
            siblings,
            {**policy.identity, "fingerprint": "not-a-hash"},
        )
    with pytest.raises(SourceSelectionError, match="source_selection_inputs"):
        with_source_selection_generation_input(siblings, policy.identity)


def test_persisted_identity_gate_distinguishes_reads_and_writer_convergence(
    tmp_path: Path,
) -> None:
    _write(tmp_path, "selected/app.py")
    _write_policy(tmp_path)
    first = resolve_source_selection(tmp_path)
    assert first is not None
    snapshot = build_source_snapshot(tmp_path, selection_policy=first)
    persisted = with_source_selection_generation_input(
        {},
        first.identity,
        snapshot.source_selection_inputs,
    )

    validate_persisted_source_selection_identity(
        persisted,
        first.identity,
        operation="read",
    )
    validate_persisted_source_selection_identity(
        None,
        first.identity,
        operation="read without a manifest",
    )
    with pytest.raises(SourceSelectionError, match="run llm-wiki sync"):
        validate_persisted_source_selection_identity(
            {},
            first.identity,
            operation="read",
        )

    changed_identity = {
        **first.identity,
        "fingerprint": "sha256:" + "1" * 64,
    }
    with pytest.raises(SourceSelectionError, match="persisted"):
        validate_persisted_source_selection_identity(
            persisted,
            changed_identity,
            operation="read",
        )
    validate_persisted_source_selection_identity(
        persisted,
        changed_identity,
        operation="sync",
        allow_same_path_update=True,
    )
    with pytest.raises(SourceSelectionError, match="restore"):
        validate_persisted_source_selection_identity(
            persisted,
            None,
            operation="sync",
            allow_same_path_update=True,
        )
    validate_persisted_source_selection_identity(
        persisted,
        None,
        operation="sync",
        explicit_path_authorized=True,
        allow_same_path_update=True,
    )


def test_persisted_gate_detects_applicable_selection_input_changes(
    tmp_path: Path,
) -> None:
    _write(tmp_path, "selected/keep.py", "KEEP = 1\n")
    _write(tmp_path, "selected/drop.py", "DROP = 1\n")
    _write(tmp_path, "selected/.gitignore", "outside.py\n")
    _write_policy(tmp_path)
    before = build_source_snapshot(tmp_path)
    persisted = with_source_selection_generation_input(
        {},
        before.source_selection_identity,
        before.source_selection_inputs,
    )
    assert (
        source_selection_inputs_from_generation_inputs(persisted)
        == before.source_selection_inputs
    )
    assert SOURCE_SELECTION_INPUTS_GENERATION_INPUT_KEY in persisted
    validate_persisted_source_selection_identity(
        persisted,
        before.source_selection_identity,
        operation="read",
        live_selection_inputs=before.source_selection_inputs,
    )

    _write(tmp_path, "selected/.gitignore", "drop.py\n")
    after = build_source_snapshot(tmp_path)
    assert after.source_selection_identity == before.source_selection_identity
    assert after.source_selection_inputs != before.source_selection_inputs
    with pytest.raises(SourceSelectionError, match="selection inputs changed"):
        validate_persisted_source_selection_identity(
            persisted,
            after.source_selection_identity,
            operation="read",
            live_selection_inputs=after.source_selection_inputs,
        )
    validate_persisted_source_selection_identity(
        persisted,
        after.source_selection_identity,
        operation="sync",
        allow_same_path_update=True,
        live_selection_inputs=after.source_selection_inputs,
    )

    _write(tmp_path, "selected/keep.py", "KEEP = 2\n")
    ordinary_edit = build_source_snapshot(tmp_path)
    assert ordinary_edit.source_selection_inputs == after.source_selection_inputs


@pytest.mark.parametrize(
    "boundary_path",
    (SOURCE_SELECTION_PATH, ".gitignore"),
)
def test_changed_selection_input_forces_full_extract_re_evaluation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    boundary_path: str,
) -> None:
    _write(tmp_path, "selected/a.py", "A = 1\n")
    _write(tmp_path, "selected/b.py", "B = 1\n")
    _write(tmp_path, ".gitignore", "outside/\n")
    _write_policy(tmp_path)
    monkeypatch.setattr(
        extraction_service,
        "_git_changed_files",
        lambda _src: [boundary_path],
    )
    monkeypatch.chdir(tmp_path)

    result = build_extract_payload(".", changed=True)

    assert sorted(result.payload["inventory"]) == [
        "selected/a.py",
        "selected/b.py",
    ]
    assert result.changed_file_count == 1
    assert result.no_changed_files is False


@pytest.mark.parametrize("control", ("root-gitignore", "profile"))
def test_git_changed_control_reaches_full_extract_before_policy_filtering(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    control: str,
) -> None:
    _write(tmp_path, "selected/a.py", "A = 1\n")
    _write(tmp_path, "selected/b.py", "B = 1\n")
    _write(tmp_path, "also/c.py", "C = 1\n")
    _write(tmp_path, ".gitignore", "outside/\n")
    _write_policy(tmp_path)
    subprocess.run(["git", "init", "--quiet"], cwd=tmp_path, check=True)
    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True)
    subprocess.run(
        [
            "git",
            "-c",
            "user.name=Selection Test",
            "-c",
            "user.email=selection@example.invalid",
            "commit",
            "--quiet",
            "-m",
            "baseline",
        ],
        cwd=tmp_path,
        check=True,
    )
    if control == "root-gitignore":
        _write(tmp_path, ".gitignore", "outside/\nselected/b.py\n")
        expected = ["selected/a.py"]
    else:
        _write_policy(tmp_path, include=["also"])
        expected = ["also/c.py"]
    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True)
    subprocess.run(
        [
            "git",
            "-c",
            "user.name=Selection Test",
            "-c",
            "user.email=selection@example.invalid",
            "commit",
            "--quiet",
            "-m",
            "change control",
        ],
        cwd=tmp_path,
        check=True,
    )
    monkeypatch.chdir(tmp_path)

    result = build_extract_payload(".", changed=True)

    assert sorted(result.payload["inventory"]) == expected
    assert result.changed_file_count == 1
    assert result.no_changed_files is False


def test_changed_gitignore_makes_all_context_sources_high_priority(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _write(tmp_path, "selected/a.py", "A = 1\n")
    _write(tmp_path, "selected/b.py", "B = 1\n")
    _write(tmp_path, ".gitignore", "outside/\n")
    _write_policy(tmp_path)
    snapshot = build_source_snapshot(tmp_path)
    monkeypatch.setattr(
        context_service,
        "_git_changed_files",
        lambda _src: [".gitignore"],
    )

    assert context_service._selected_git_changed_files(
        str(tmp_path), snapshot
    ) == ["selected/a.py", "selected/b.py"]


@pytest.mark.parametrize(
    "requested_path",
    (
        "selected/ignored.py",
        "selected/.claude/worktrees/task/agent.py",
    ),
)
def test_configured_only_files_cannot_readmit_ignored_or_agent_paths(
    tmp_path: Path,
    requested_path: str,
) -> None:
    _write(tmp_path, "selected/keep.py", "KEEP = 1\n")
    _write(tmp_path, "selected/ignored.py", "IGNORED = 1\n")
    _write(
        tmp_path,
        "selected/.claude/worktrees/task/agent.py",
        "AGENT = 1\n",
    )
    _write(tmp_path, "selected/.gitignore", "ignored.py\n")
    _write_policy(tmp_path)

    snapshot = build_source_snapshot(
        tmp_path,
        only_files=(requested_path,),
    )

    assert snapshot.language_paths("python") == []
    assert requested_path not in snapshot.captured_content_hashes
    assert requested_path not in snapshot.selected_regular_paths


def test_changed_and_diff_filters_drop_ignored_and_global_excluded_paths(
    tmp_path: Path,
) -> None:
    _write(tmp_path, "selected/keep.py", "KEEP = 1\n")
    _write(tmp_path, "selected/ignored.py", "IGNORED = 'secret'\n")
    _write(tmp_path, "selected/build/secret.py", "BUILD = 'secret'\n")
    _write(tmp_path, "selected/.gitignore", "ignored.py\n")
    _write_policy(tmp_path)
    subprocess.run(["git", "init", "--quiet"], cwd=tmp_path, check=True)
    snapshot = build_source_snapshot(tmp_path)
    changed, boundary = extraction_service._partition_snapshot_git_changes(
        [
            "selected/ignored.py",
            "selected/build/secret.py",
            "selected/deleted.py",
        ],
        snapshot,
    )
    assert changed == ["selected/deleted.py"]
    assert boundary is False

    def block(path: str, value: str) -> str:
        return (
            f"diff --git a/{path} b/{path}\n"
            f"--- a/{path}\n"
            f"+++ b/{path}\n"
            "@@ -1 +1 @@\n"
            f"-{value}\n+changed\n"
        )

    selected = block("selected/keep.py", "KEEP = 1")
    ignored = block("selected/ignored.py", "IGNORED = 'secret'")
    build = block("selected/build/secret.py", "BUILD = 'secret'")
    deleted = (
        "diff --git a/selected/deleted.py b/selected/deleted.py\n"
        "deleted file mode 100644\n"
        "--- a/selected/deleted.py\n"
        "+++ /dev/null\n"
        "@@ -1 +0,0 @@\n"
        "-REMOVED = True\n"
    )
    filtered = filter_source_diff(
        selected + ignored + build + deleted,
        snapshot.source_selection_policy,
        source_snapshot=snapshot,
    )

    assert filtered == selected + deleted
    assert "IGNORED" not in filtered
    assert "BUILD" not in filtered


def test_git_rename_retains_old_applicable_gitignore_boundary(
    tmp_path: Path,
) -> None:
    repository = tmp_path / "repository"
    _write(repository, "selected/app.py", "VALUE = 1\n")
    _write(repository, "selected/.gitignore", "ignored.py\n")
    _write_policy(repository)
    subprocess.run(["git", "init", "--quiet"], cwd=repository, check=True)
    subprocess.run(["git", "add", "."], cwd=repository, check=True)
    subprocess.run(
        [
            "git",
            "-c",
            "user.name=Selection Test",
            "-c",
            "user.email=selection@example.invalid",
            "commit",
            "--quiet",
            "-m",
            "selection baseline",
        ],
        cwd=repository,
        check=True,
    )
    (repository / "outside").mkdir()
    subprocess.run(
        ["git", "mv", "selected/.gitignore", "outside/.gitignore"],
        cwd=repository,
        check=True,
    )
    subprocess.run(
        [
            "git",
            "-c",
            "user.name=Selection Test",
            "-c",
            "user.email=selection@example.invalid",
            "commit",
            "--quiet",
            "-m",
            "move ignore control",
        ],
        cwd=repository,
        check=True,
    )
    snapshot = build_source_snapshot(repository)

    changed = extraction_service._git_changed_files(str(repository))
    assert changed == ["selected/.gitignore", "outside/.gitignore"]
    selected, boundary_changed = extraction_service._partition_snapshot_git_changes(
        changed or (),
        snapshot,
    )
    assert selected == []
    assert boundary_changed is True


def test_diff_filter_normalizes_nested_git_coordinates_and_keeps_controls(
    tmp_path: Path,
) -> None:
    repository = tmp_path / "repository"
    source = repository / "packages" / "application"
    _write(source, "selected/app.py", "VALUE = 1\n")
    _write(source, ".gitignore", "outside/\n")
    _write_policy(source)
    subprocess.run(
        ["git", "init", "--quiet"],
        cwd=repository,
        check=True,
    )
    snapshot = build_source_snapshot(source)
    prefix = "packages/application"

    def block(path: str, content: str) -> str:
        return (
            f"diff --git a/{path} b/{path}\n"
            f"--- a/{path}\n"
            f"+++ b/{path}\n"
            "@@ -1 +1 @@\n"
            f"-{content}\n+changed\n"
        )

    selected = block(f"{prefix}/selected/app.py", "VALUE = 1")
    profile = block(f"{prefix}/{SOURCE_SELECTION_PATH}", "profile")
    gitignore = block(f"{prefix}/.gitignore", "outside/")
    wiki_root = repository / "docs" / "llm_wiki"
    wiki_root.mkdir(parents=True)
    wiki = block("docs/llm_wiki/index.md", "wiki")
    excluded = block("outside/secret.py", "SECRET")

    filtered = filter_source_diff(
        selected + profile + gitignore + wiki + excluded,
        snapshot.source_selection_policy,
        retained_roots=(wiki_root.as_posix(),),
        source_snapshot=snapshot,
    )

    assert filtered == selected + profile + gitignore + wiki
    assert "outside/secret.py" not in filtered
    assert "SECRET" not in filtered


def test_diff_filter_does_not_alias_local_wiki_into_external_source_repo(
    tmp_path: Path,
) -> None:
    source_repository = tmp_path / "external-source"
    _write(source_repository, "selected/app.py", "VALUE = 1\n")
    _write_policy(source_repository)
    subprocess.run(
        ["git", "init", "--quiet"],
        cwd=source_repository,
        check=True,
    )
    snapshot = build_source_snapshot(source_repository)
    local_wiki = tmp_path / "local-project" / "docs" / "llm_wiki"
    local_wiki.mkdir(parents=True)
    leaked = (
        "diff --git a/docs/llm_wiki/secret.md b/docs/llm_wiki/secret.md\n"
        "--- a/docs/llm_wiki/secret.md\n"
        "+++ b/docs/llm_wiki/secret.md\n"
        "@@ -1 +1 @@\n"
        "-SECRET = 'must-not-leak'\n"
        "+SECRET = 'still-must-not-leak'\n"
    )

    filtered = filter_source_diff(
        leaked,
        snapshot.source_selection_policy,
        retained_roots=(local_wiki.as_posix(),),
        source_snapshot=snapshot,
    )

    assert filtered == ""
    assert "secret.md" not in filtered


@pytest.mark.parametrize("operation", ("rename", "copy"))
def test_mixed_boundary_git_diff_blocks_are_dropped_without_path_or_content_leak(
    tmp_path: Path,
    operation: str,
) -> None:
    _write(tmp_path, "selected/keep.py", "KEEP = True\n")
    _write_policy(tmp_path)
    policy = resolve_source_selection(tmp_path)
    assert policy is not None
    mixed = (
        "diff --git a/selected/keep.py b/outside/secret.py\n"
        "similarity index 100%\n"
        f"{operation} from selected/keep.py\n"
        f"{operation} to outside/secret.py\n"
        "--- a/selected/keep.py\n"
        "+++ b/outside/secret.py\n"
        "@@ -1 +1 @@\n"
        "-KEEP = True\n"
        "+SECRET = 'must-not-leak'\n"
    )
    selected = (
        "diff --git a/selected/keep.py b/selected/keep.py\n"
        "--- a/selected/keep.py\n"
        "+++ b/selected/keep.py\n"
        "@@ -1 +1 @@\n"
        "-KEEP = True\n"
        "+KEEP = False\n"
    )

    filtered = filter_source_diff(mixed + selected, policy)

    assert filtered == selected
    assert "outside/secret.py" not in filtered
    assert "must-not-leak" not in filtered


def test_path_membership_is_exact_case_posix_and_excludes_win(tmp_path):
    _write(tmp_path, "selected/app.py")
    _write(tmp_path, "selected/private/hidden.py")
    _write_policy(tmp_path, exclude=["selected/private"])
    policy = resolve_source_selection(tmp_path)
    assert policy is not None

    assert path_is_selected(policy, "selected")
    assert path_is_selected(policy, "selected/app.py")
    assert not path_is_selected(policy, "selected/private")
    assert not path_is_selected(policy, "selected/private/hidden.py")
    assert not path_is_selected(policy, "Selected/app.py")
    assert not path_is_selected(policy, "outside.py")
    assert path_is_selected(None, "outside.py")
    with pytest.raises(SourceSelectionError):
        path_is_selected(policy, "../escape.py")


def test_snapshot_rechecks_controls_before_hashing_newly_admitted_source(
    tmp_path,
    monkeypatch,
):
    _write(tmp_path, "selected/keep.py", "KEEP = 1\n")
    secret = _write(tmp_path, "selected/secret.py", "SECRET = 1\n")
    ignore = _write(tmp_path, "selected/.gitignore", "secret.py\n")
    _write_policy(tmp_path)
    policy = resolve_source_selection(tmp_path)
    assert policy is not None
    controls = capture_source_selection_inputs(
        tmp_path,
        selection_policy=policy,
    )
    original_collect = source_snapshot_module._collect_source_tree

    def broaden_before_collection(root, only_set, buckets):
        ignore.unlink()
        return original_collect(root, only_set, buckets)

    real_hash = source_snapshot_module._sha256_file

    def reject_secret_hash(path):
        if Path(path).resolve() == secret.resolve():
            pytest.fail("changed controls must fail before newly admitted source hash")
        return real_hash(path)

    monkeypatch.setattr(
        source_snapshot_module,
        "_collect_source_tree",
        broaden_before_collection,
    )
    monkeypatch.setattr(source_snapshot_module, "_sha256_file", reject_secret_hash)

    with pytest.raises(SourceSnapshotError, match="changed during snapshot capture"):
        build_source_snapshot(
            tmp_path,
            selection_policy=policy,
            expected_selection_inputs=controls,
        )


def test_committed_profile_freezes_intended_product_census():
    repository = Path(__file__).resolve().parents[1]
    raw_profile = json.loads((repository / SOURCE_SELECTION_PATH).read_text("utf-8"))
    assert raw_profile == {
        "schema_version": SOURCE_SELECTION_SCHEMA_VERSION,
        "include": [
            "pyproject.toml",
            "src/llm_wiki_cli",
            "integrations/github-action",
            "integrations/wiki-integrity",
            "integrations/obsidian/llm-wiki",
        ],
        "exclude": [],
    }

    snapshot = build_source_snapshot(repository)
    assert {
        language: len(files) for language, files in snapshot.files_by_language.items()
    } == {
        "python": 157,
        "typescript": 2,
        "go": 0,
        "rust": 0,
        "haskell": 0,
    }
    assert len(snapshot.all_source_paths) == 159
    assert snapshot.language_paths("typescript") == [
        "integrations/obsidian/llm-wiki/main.js",
        "integrations/obsidian/llm-wiki/src/main.ts",
    ]
    assert "integrations/github-action/render_summary.py" in snapshot.language_paths(
        "python"
    )
    assert [item.rel_path for item in snapshot.yaml_candidates] == [
        "integrations/github-action/action.yml",
        "integrations/wiki-integrity/action.yml",
    ]
    assert all(not path.startswith("tests/") for path in snapshot.all_source_paths)
    assert all(not path.startswith("release/") for path in snapshot.all_source_paths)
