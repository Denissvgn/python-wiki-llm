"""Focused contracts for the portable ``llm-wiki install-ci`` command."""

from __future__ import annotations

import json
import re
import sys
import types
from pathlib import Path

import pytest
import yaml

from llm_wiki_cli import cli
from llm_wiki_cli.commands import uninstall_cmd
from llm_wiki_cli.services import ci_installer, io
from llm_wiki_cli.services.ci_installer import (
    CHECKOUT_ACTION_REF,
    InstallCiError,
    MANAGED_WORKFLOW_PATH,
    WIKI_INTEGRITY_ACTION,
    install_ci_workflow,
    is_unmodified_managed_workflow,
    normalize_action_ref,
    render_managed_workflow,
)
from llm_wiki_cli.services.sync_manifest import MANIFEST_FILENAME
from llm_wiki_cli.services.source_selection import (
    SOURCE_SELECTION_IDENTITY_SCHEMA_VERSION,
    SOURCE_SELECTION_SCHEMA_VERSION,
    resolve_source_selection,
    with_source_selection_generation_input,
)
from llm_wiki_cli.services.source_snapshot import capture_source_selection_inputs
from llm_wiki_cli.services.sync_manifest import SyncManifest


ACTION_REF = "A" * 40
CANONICAL_ACTION_REF = "a" * 40
NEXT_ACTION_REF = "b" * 40


def _managed_project(
    tmp_path: Path,
    *,
    src_dir: str = ".",
    wiki_dir: str = "docs/llm_wiki",
) -> Path:
    root = tmp_path / "project"
    root.mkdir()
    if src_dir != ".":
        (root / src_dir).mkdir(parents=True)
    wiki = root / wiki_dir
    wiki.mkdir(parents=True)
    SyncManifest().save(wiki)
    return root


@pytest.mark.parametrize(
    "value",
    [
        "a" * 39,
        "a" * 41,
        "g" * 40,
        "v1.6.0",
        " a" + "0" * 38,
        "",
        None,
    ],
)
def test_action_ref_requires_one_full_hex_commit(value):
    with pytest.raises(InstallCiError, match="exactly 40 hexadecimal"):
        normalize_action_ref(value)


def test_workflow_contract_is_portable_read_only_and_checksum_owned():
    rendered = render_managed_workflow(
        action_ref=ACTION_REF,
        src_dir="source tree",
        wiki_dir="project docs/wiki",
    )
    text = rendered.decode("utf-8")

    assert is_unmodified_managed_workflow(rendered)
    assert f"uses: actions/checkout@{CHECKOUT_ACTION_REF}" in text
    assert f"uses: {WIKI_INTEGRITY_ACTION}@{CANONICAL_ACTION_REF}" in text
    assert "on:\n  push:\n  pull_request:\n" in text
    assert "runs-on: ubuntu-24.04" in text
    assert "timeout-minutes: 45" in text
    assert text.count("contents: read") == 2
    assert "persist-credentials: false" in text
    assert 'src-dir: "source tree"' in text
    assert 'wiki-dir: "project docs/wiki"' in text
    assert "source-selection" not in text
    assert "paths:" not in text
    assert "secrets" not in text.casefold()

    workflow = yaml.safe_load(text)
    assert workflow[True] == {"push": None, "pull_request": None}
    job = workflow["jobs"]["integrity"]
    assert job["permissions"] == {"contents": "read"}
    assert [step["name"] for step in job["steps"]] == [
        "Check out the repository without credentials",
        "Check LLM Wiki integrity",
    ]
    for step in job["steps"]:
        repository, separator, ref = step["uses"].rpartition("@")
        assert repository and separator
        assert re.fullmatch(r"[0-9a-f]{40}", ref)

    modified = rendered.replace(b"ubuntu-24.04", b"ubuntu-latest")
    assert not is_unmodified_managed_workflow(modified)


def test_create_is_atomic_and_rerun_is_an_exact_noop(tmp_path, monkeypatch):
    root = _managed_project(tmp_path)

    created = install_ci_workflow(action_ref=ACTION_REF, project_root=root)

    target = root / MANAGED_WORKFLOW_PATH
    assert created.operation == "create"
    assert created.changed
    assert target.read_bytes() == render_managed_workflow(action_ref=ACTION_REF)
    assert not list(target.parent.glob(f".{target.name}.*.tmp"))

    def unexpected_write(*args, **kwargs):
        raise AssertionError("an already-current workflow must not be rewritten")

    monkeypatch.setattr(ci_installer, "write_bytes_atomic", unexpected_write)
    unchanged = install_ci_workflow(action_ref=ACTION_REF, project_root=root)

    assert unchanged.operation == "unchanged"
    assert not unchanged.changed


def test_crlf_checkout_of_current_workflow_is_also_a_noop(tmp_path, monkeypatch):
    root = _managed_project(tmp_path)
    target = root / MANAGED_WORKFLOW_PATH
    target.parent.mkdir(parents=True)
    target.write_bytes(
        render_managed_workflow(action_ref=ACTION_REF).replace(b"\n", b"\r\n")
    )

    monkeypatch.setattr(
        ci_installer,
        "write_bytes_atomic",
        lambda *args, **kwargs: pytest.fail("CRLF normalization should be current"),
    )

    result = install_ci_workflow(action_ref=ACTION_REF, project_root=root)
    assert result.operation == "unchanged"


def test_unmodified_managed_workflow_auto_updates_to_new_action_ref(tmp_path):
    root = _managed_project(tmp_path)
    target = root / MANAGED_WORKFLOW_PATH
    target.parent.mkdir(parents=True)
    target.write_bytes(render_managed_workflow(action_ref=ACTION_REF))

    result = install_ci_workflow(action_ref=NEXT_ACTION_REF, project_root=root)

    assert result.operation == "update"
    assert result.changed
    content = target.read_bytes()
    assert f"@{NEXT_ACTION_REF}".encode() in content
    assert f"@{CANONICAL_ACTION_REF}".encode() not in content
    assert is_unmodified_managed_workflow(content)


def test_modified_managed_workflow_requires_force_and_dry_run_is_read_only(
    tmp_path,
):
    root = _managed_project(tmp_path)
    target = root / MANAGED_WORKFLOW_PATH
    target.parent.mkdir(parents=True)
    original = render_managed_workflow(action_ref=ACTION_REF).replace(
        b"timeout-minutes: 45", b"timeout-minutes: 60"
    )
    target.write_bytes(original)

    with pytest.raises(InstallCiError, match="--force"):
        install_ci_workflow(action_ref=NEXT_ACTION_REF, project_root=root)
    assert target.read_bytes() == original

    preview = install_ci_workflow(
        action_ref=NEXT_ACTION_REF,
        project_root=root,
        dry_run=True,
        force=True,
    )
    assert preview.operation == "update"
    assert not preview.changed
    assert target.read_bytes() == original

    updated = install_ci_workflow(
        action_ref=NEXT_ACTION_REF,
        project_root=root,
        force=True,
    )
    assert updated.changed
    assert is_unmodified_managed_workflow(target.read_bytes())


def test_unmanaged_target_requires_force(tmp_path):
    root = _managed_project(tmp_path)
    target = root / MANAGED_WORKFLOW_PATH
    target.parent.mkdir(parents=True)
    target.write_text("name: Existing project workflow\n", encoding="utf-8")

    with pytest.raises(InstallCiError, match="not an unmodified"):
        install_ci_workflow(action_ref=ACTION_REF, project_root=root)

    install_ci_workflow(action_ref=ACTION_REF, project_root=root, force=True)
    assert is_unmodified_managed_workflow(target.read_bytes())


def test_install_preserves_unrelated_workflows_and_refuses_target_directory(tmp_path):
    root = _managed_project(tmp_path)
    unrelated = root / ".github/workflows/ci.yml"
    unrelated.parent.mkdir(parents=True)
    original = b"name: Existing CI\n"
    unrelated.write_bytes(original)

    install_ci_workflow(action_ref=ACTION_REF, project_root=root)
    assert unrelated.read_bytes() == original

    target = root / MANAGED_WORKFLOW_PATH
    target.unlink()
    target.mkdir()
    with pytest.raises(InstallCiError, match="not a regular file"):
        install_ci_workflow(
            action_ref=ACTION_REF,
            project_root=root,
            force=True,
        )


def test_install_refuses_a_symlinked_workflow_target(tmp_path):
    root = _managed_project(tmp_path)
    target = root / MANAGED_WORKFLOW_PATH
    target.parent.mkdir(parents=True)
    victim = root / "victim.yml"
    original = b"name: Victim\n"
    victim.write_bytes(original)
    try:
        target.symlink_to(victim)
    except OSError:
        pytest.skip("Symlinks are unavailable to this test account.")

    with pytest.raises(InstallCiError, match="symlink|unsafe path component"):
        install_ci_workflow(
            action_ref=ACTION_REF,
            project_root=root,
            force=True,
        )
    assert victim.read_bytes() == original


def test_install_rejects_portable_case_collision_in_workflow_prefix(tmp_path):
    root = _managed_project(tmp_path)
    (root / ".GITHUB").mkdir()

    with pytest.raises(InstallCiError, match="not portable|filesystem case"):
        install_ci_workflow(action_ref=ACTION_REF, project_root=root)
    assert {entry.name for entry in root.iterdir()} >= {".GITHUB"}
    assert not (root / ".GITHUB/workflows").exists()


def test_dry_run_does_not_create_workflow_directories(tmp_path):
    root = _managed_project(tmp_path)

    result = install_ci_workflow(
        action_ref=ACTION_REF,
        project_root=root,
        dry_run=True,
    )

    assert result.operation == "create"
    assert not result.changed
    assert not (root / ".github").exists()


def test_install_requires_an_existing_managed_wiki_even_with_force(tmp_path):
    root = tmp_path / "project"
    wiki = root / "docs/llm_wiki"
    wiki.mkdir(parents=True)
    (wiki / "index.md").write_text("# Existing wiki\n", encoding="utf-8")

    with pytest.raises(InstallCiError, match="requires an initialized managed wiki"):
        install_ci_workflow(
            action_ref=ACTION_REF,
            project_root=root,
            force=True,
        )
    assert not (root / MANAGED_WORKFLOW_PATH).exists()


def test_install_rejects_a_malformed_managed_manifest(tmp_path):
    root = _managed_project(tmp_path)
    manifest = root / "docs/llm_wiki" / MANIFEST_FILENAME
    manifest.write_text("{}\n", encoding="utf-8")

    with pytest.raises(InstallCiError, match="not valid"):
        install_ci_workflow(action_ref=ACTION_REF, project_root=root)
    assert not (root / MANAGED_WORKFLOW_PATH).exists()


def test_install_rejects_a_symlinked_managed_manifest(tmp_path):
    root = _managed_project(tmp_path)
    manifest = root / "docs/llm_wiki" / MANIFEST_FILENAME
    victim = root / "manifest-victim.json"
    original = manifest.read_bytes()
    victim.write_bytes(original)
    manifest.unlink()
    try:
        manifest.symlink_to(victim)
    except OSError:
        pytest.skip("Symlinks are unavailable to this test account.")

    with pytest.raises(InstallCiError, match="regular file"):
        install_ci_workflow(action_ref=ACTION_REF, project_root=root)
    assert victim.read_bytes() == original
    assert not (root / MANAGED_WORKFLOW_PATH).exists()


def test_install_rejects_a_nondefault_persisted_source_selection(tmp_path):
    root = _managed_project(tmp_path)
    wiki = root / "docs/llm_wiki"
    manifest = SyncManifest(
        generation_inputs={
            "source_selection": {
                "schema_version": SOURCE_SELECTION_IDENTITY_SCHEMA_VERSION,
                "path": "config/private-selection.json",
                "fingerprint": "sha256:" + "a" * 64,
            },
            "source_selection_inputs": {
                "schema_version": "llm-wiki-source-selection-inputs/v1",
                "inputs": [
                    {
                        "path": "config/private-selection.json",
                        "content_hash": "sha256:" + "b" * 64,
                    }
                ],
            },
        }
    )
    manifest.save(wiki)

    with pytest.raises(InstallCiError, match="default source-selection"):
        install_ci_workflow(action_ref=ACTION_REF, project_root=root)
    assert not (root / MANAGED_WORKFLOW_PATH).exists()


def test_install_accepts_the_canonical_default_source_selection(tmp_path):
    root = _managed_project(tmp_path)
    source = root / "app.py"
    source.write_text("VALUE = 1\n", encoding="utf-8")
    profile = root / ".llm-wiki/source-selection.json"
    profile.parent.mkdir()
    profile.write_text(
        json.dumps(
            {
                "schema_version": SOURCE_SELECTION_SCHEMA_VERSION,
                "include": ["app.py"],
                "exclude": [],
            }
        )
        + "\n",
        encoding="utf-8",
    )
    policy = resolve_source_selection(root)
    assert policy is not None
    generation_inputs = with_source_selection_generation_input(
        {},
        policy.identity,
        capture_source_selection_inputs(root, selection_policy=policy),
    )
    SyncManifest(generation_inputs=generation_inputs).save(root / "docs/llm_wiki")

    result = install_ci_workflow(action_ref=ACTION_REF, project_root=root)

    assert result.operation == "create"
    content = (root / MANAGED_WORKFLOW_PATH).read_text(encoding="utf-8")
    assert "source-selection" not in content


def test_project_paths_are_strict_portable_and_cannot_escape(tmp_path):
    root = _managed_project(
        tmp_path,
        src_dir="source tree",
        wiki_dir="project docs/wiki",
    )

    install_ci_workflow(
        action_ref=ACTION_REF,
        src_dir="source tree",
        wiki_dir="project docs/wiki",
        project_root=root,
    )
    text = (root / MANAGED_WORKFLOW_PATH).read_text(encoding="utf-8")
    assert 'src-dir: "source tree"' in text
    assert 'wiki-dir: "project docs/wiki"' in text

    for invalid in (
        "../outside",
        str(root / "source tree"),
        "./source tree",
        "source\\tree",
        "source//tree",
        " source tree",
    ):
        with pytest.raises(
            InstallCiError,
            match="project-relative|normalized|POSIX",
        ):
            install_ci_workflow(
                action_ref=ACTION_REF,
                src_dir=invalid,
                wiki_dir="project docs/wiki",
                project_root=root,
            )


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("src_dir", "src-${{github.sha}}"),
        ("wiki_dir", "docs/${{ github.ref }}"),
    ],
)
def test_project_paths_reject_github_expression_injection(tmp_path, field, value):
    root = _managed_project(tmp_path)
    options = {
        "action_ref": ACTION_REF,
        "project_root": root,
        field: value,
    }

    with pytest.raises(InstallCiError, match="GitHub Actions expression"):
        install_ci_workflow(**options)
    assert not (root / MANAGED_WORKFLOW_PATH).exists()


def test_atomic_replace_failure_preserves_existing_workflow(tmp_path, monkeypatch):
    root = _managed_project(tmp_path)
    target = root / MANAGED_WORKFLOW_PATH
    target.parent.mkdir(parents=True)
    original = b"name: Existing project workflow\n"
    target.write_bytes(original)

    def fail_replace(source, destination):
        raise OSError("injected replacement failure")

    monkeypatch.setattr(io.os, "replace", fail_replace)

    with pytest.raises(InstallCiError, match="injected replacement failure"):
        install_ci_workflow(
            action_ref=ACTION_REF,
            project_root=root,
            force=True,
        )

    assert target.read_bytes() == original
    assert not list(target.parent.glob(f".{target.name}.*.tmp"))


def test_cli_parses_install_ci_contract_and_requires_action_ref(monkeypatch):
    seen = {}

    monkeypatch.setattr(
        cli.install_ci_cmd,
        "run",
        lambda args: seen.update(vars(args)),
    )
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "llm-wiki",
            "install-ci",
            "--action-ref",
            ACTION_REF,
            "--src-dir",
            "source",
            "--wiki-dir",
            "wiki",
            "--dry-run",
            "--force",
        ],
    )

    cli.main()

    assert seen == {
        "command": "install-ci",
        "action_ref": ACTION_REF,
        "src_dir": "source",
        "wiki_dir": "wiki",
        "dry_run": True,
        "force": True,
    }

    monkeypatch.setattr(sys, "argv", ["llm-wiki", "install-ci"])
    with pytest.raises(SystemExit) as exc_info:
        cli.main()
    assert exc_info.value.code == 2


def test_cli_adapter_creates_workflow_and_reports_canonical_ref(
    tmp_path,
    monkeypatch,
    capsys,
):
    root = _managed_project(tmp_path)
    monkeypatch.chdir(root)
    monkeypatch.setattr(
        sys,
        "argv",
        ["llm-wiki", "install-ci", "--action-ref", ACTION_REF],
    )

    cli.main()

    output = capsys.readouterr().out
    assert "Created LLM Wiki integrity workflow" in output
    assert f"Pinned reusable action commit: {CANONICAL_ACTION_REF}" in output
    assert (root / MANAGED_WORKFLOW_PATH).is_file()


def test_cli_help_exposes_only_default_source_selection_discovery(
    monkeypatch,
    capsys,
):
    monkeypatch.setattr(sys, "argv", ["llm-wiki", "install-ci", "--help"])

    with pytest.raises(SystemExit) as exc_info:
        cli.main()

    assert exc_info.value.code == 0
    help_text = capsys.readouterr().out
    assert "--action-ref SHA" in help_text
    assert "--src-dir" in help_text
    assert "--wiki-dir" in help_text
    assert "--dry-run" in help_text
    assert "--force" in help_text
    assert "--source-selection" not in help_text


def test_uninstall_dry_run_counts_then_removes_unmodified_managed_workflow(
    tmp_path,
    monkeypatch,
    capsys,
):
    root = _managed_project(tmp_path)
    target = root / MANAGED_WORKFLOW_PATH
    target.parent.mkdir(parents=True)
    target.write_bytes(render_managed_workflow(action_ref=ACTION_REF))
    monkeypatch.chdir(root)
    args = types.SimpleNamespace(
        wiki_dir="docs/llm_wiki",
        remove_wiki=False,
        dry_run=True,
    )

    uninstall_cmd.run(args)

    output = capsys.readouterr().out
    assert "Managed CI Workflow" in output
    assert f"WOULD REMOVE: {MANAGED_WORKFLOW_PATH}" in output
    assert "Dry run complete. 1 item(s) would be affected." in output
    assert target.exists()

    monkeypatch.setattr("builtins.input", lambda _: "y")
    args.dry_run = False
    uninstall_cmd.run(args)
    assert not target.exists()


@pytest.mark.parametrize(
    "content",
    [
        b"name: Project-owned workflow\n",
        render_managed_workflow(action_ref=ACTION_REF).replace(
            b"timeout-minutes: 45",
            b"timeout-minutes: 60",
        ),
    ],
)
def test_uninstall_preserves_unmanaged_or_modified_workflow(
    tmp_path,
    monkeypatch,
    content,
):
    root = _managed_project(tmp_path)
    target = root / MANAGED_WORKFLOW_PATH
    target.parent.mkdir(parents=True)
    target.write_bytes(content)
    monkeypatch.chdir(root)
    monkeypatch.setattr(
        "builtins.input",
        lambda _: pytest.fail("preserved workflow must not require confirmation"),
    )

    uninstall_cmd.run(
        types.SimpleNamespace(
            wiki_dir="docs/llm_wiki",
            remove_wiki=False,
            dry_run=False,
        )
    )

    assert target.read_bytes() == content
