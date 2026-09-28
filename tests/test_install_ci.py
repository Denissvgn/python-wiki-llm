"""Focused contracts for the portable ``llm-wiki install-ci`` command."""

from __future__ import annotations

import json
import re
import subprocess
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


def _symlink_or_emulate_unsafe_component(
    path: Path,
    target: Path,
    *,
    monkeypatch: pytest.MonkeyPatch,
    fallback_content: bytes | None = None,
) -> None:
    """Exercise a real link or deterministically inject the guard result.

    The path-guard suites own native symlink and reparse-point detection.  These
    installer tests own the service's fail-closed response and must not add a
    hosted skip merely because the test account cannot create symlinks.
    """

    try:
        path.symlink_to(target)
        return
    except OSError:
        if path.is_symlink():
            path.unlink()
        elif path.exists():
            raise AssertionError("failed symlink creation left an unexpected path")

    if fallback_content is not None:
        path.write_bytes(fallback_content)

    real_guard = ci_installer.first_unsafe_path_component

    def injected_guard(candidate, *args, **kwargs):
        candidate_path = Path(candidate)
        if candidate_path == path:
            return candidate_path
        return real_guard(candidate, *args, **kwargs)

    monkeypatch.setattr(
        ci_installer,
        "first_unsafe_path_component",
        injected_guard,
    )


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
    assert job["steps"][1]["with"]["report-schema"] == "v4"
    assert job["steps"][1]["with"]["comparison-policy"] == "auto"
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


@pytest.mark.parametrize("crlf", [False, True])
@pytest.mark.parametrize("modified", [False, True])
def test_prior_workflow_upgrades_without_overwriting_user_changes(
    tmp_path, crlf, modified
):
    root = _managed_project(tmp_path)
    target = root / MANAGED_WORKFLOW_PATH
    target.parent.mkdir(parents=True)
    # Exact installer output from a55a3973, before explicit schema/policy inputs.
    old = (Path(__file__).parent / "fixtures/install-ci-legacy.yml").read_bytes()
    if modified:
        old = old.replace(b"timeout-minutes: 45", b"timeout-minutes: 60")
    if crlf:
        old = old.replace(b"\n", b"\r\n")
    target.write_bytes(old)
    if modified:
        with pytest.raises(InstallCiError, match="--force"):
            install_ci_workflow(action_ref=ACTION_REF, project_root=root)
        assert target.read_bytes() == old
        return
    preview = install_ci_workflow(action_ref=ACTION_REF, project_root=root, dry_run=True)
    assert preview.operation == "update" and target.read_bytes() == old
    applied = install_ci_workflow(action_ref=ACTION_REF, project_root=root)
    assert applied.operation == "update"
    assert target.read_bytes() == render_managed_workflow(action_ref=ACTION_REF)
    unchanged = install_ci_workflow(action_ref=ACTION_REF, project_root=root)
    assert unchanged.operation == "unchanged"


@pytest.mark.parametrize("legacy", [False, True])
def test_generated_workflow_evaluates_migrated_and_legacy_knowledge(
    tmp_path, monkeypatch, legacy
):
    from llm_wiki_cli import api
    from llm_wiki_cli.services import analysis_capture, analysis_compatibility, ci_report
    from llm_wiki_cli.services.knowledge_loader import load_knowledge_state
    from tests.test_knowledge_health_refresh import _version

    monkeypatch.chdir(tmp_path)
    (tmp_path / ".git").write_text("gitdir: absent\n", encoding="utf-8")
    source = tmp_path / "source"
    source.mkdir()
    (source / "model.py").write_text("class User:\n    name: str\n", encoding="utf-8")
    with monkeypatch.context() as producer:
        if legacy:
            # Produce the historical configuration form before writing artifacts.
            producer.setattr(analysis_capture, "capture_analysis", lambda *a, **kw: None)
        api.bootstrap_wiki(
            "source", "wiki", skip_workflows=True,
            skip_flows=True, skip_dependencies=True,
        )
        producer.setattr(sys, "argv", [
            "llm-wiki", "sync", "--src-dir", "source", "--wiki-dir", "wiki",
            "--no-cache", "--no-plugins",
        ])
        cli.main()
    knowledge = load_knowledge_state("wiki").knowledge
    assert knowledge is not None
    assert analysis_compatibility.has_contract(knowledge.bundle.producer) is not legacy
    install_ci_workflow(
        action_ref=ACTION_REF, src_dir="source", wiki_dir="wiki", project_root=tmp_path
    )
    workflow = yaml.safe_load((tmp_path / MANAGED_WORKFLOW_PATH).read_text(encoding="utf-8"))
    configured = workflow["jobs"]["integrity"]["steps"][1]["with"]
    action_path = Path(__file__).parents[1] / "integrations/wiki-integrity/action.yml"
    action = yaml.safe_load(action_path.read_text(encoding="utf-8"))
    inputs = {
        name: configured.get(name, row.get("default"))
        for name, row in action["inputs"].items()
    }
    command = [
        sys.executable, "-I", "-m", "llm_wiki_cli.cli", "ci-check",
        "--format", "json", "--no-report", "--no-cache", "--no-plugins",
    ]
    for name in ("src-dir", "wiki-dir", "report-schema", "comparison-policy"):
        command.extend(["--" + name, inputs[name]])
    result = subprocess.run(
        command, cwd=tmp_path, stdin=subprocess.DEVNULL, capture_output=True,
        text=True, check=False, timeout=60,
    )
    assert result.returncode == 0, result.stderr
    report = ci_report.validate_ci_check_payload(json.loads(result.stdout), cli_exit=0)
    assert report["schema_version"] == "llm-wiki-ci-check/v4"
    health = report["knowledge_health"]
    assert health["status"] == "healthy"
    details = health["health_details"]
    assert details["basis"]["policy"] == ("exact-v1" if legacy else "auto")
    assert details["coverage"]["modeled"] > 0
    assert details["coverage"]["outcomes"]["current"] == details["coverage"]["modeled"]
    if legacy:
        _version(monkeypatch, "9.8.7")
        changed = api.doctor(
            "source", wiki_dir="wiki", strict=True,
            report_schema="v4", comparison_policy="auto",
        )
        assert changed["status"] == "unhealthy"
        assert "producer-tool-version-changed" in changed["drift"]["reasons"]


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


def test_unreadable_target_fails_without_mutation(tmp_path, monkeypatch):
    root = _managed_project(tmp_path)
    target = root / MANAGED_WORKFLOW_PATH
    target.parent.mkdir(parents=True)
    original = b"name: Existing project workflow\n"
    target.write_bytes(original)
    real_read_bytes = Path.read_bytes

    def guarded_read_bytes(path):
        if path == target:
            raise OSError("injected read failure")
        return real_read_bytes(path)

    monkeypatch.setattr(Path, "read_bytes", guarded_read_bytes)

    with pytest.raises(InstallCiError, match="injected read failure"):
        install_ci_workflow(
            action_ref=ACTION_REF,
            project_root=root,
            force=True,
        )
    assert real_read_bytes(target) == original


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


def test_install_refuses_a_symlinked_workflow_target(tmp_path, monkeypatch):
    root = _managed_project(tmp_path)
    target = root / MANAGED_WORKFLOW_PATH
    target.parent.mkdir(parents=True)
    victim = root / "victim.yml"
    original = b"name: Victim\n"
    victim.write_bytes(original)
    _symlink_or_emulate_unsafe_component(
        target,
        victim,
        monkeypatch=monkeypatch,
    )

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


def test_install_rejects_a_symlinked_managed_manifest(tmp_path, monkeypatch):
    root = _managed_project(tmp_path)
    manifest = root / "docs/llm_wiki" / MANIFEST_FILENAME
    victim = root / "manifest-victim.json"
    original = manifest.read_bytes()
    victim.write_bytes(original)
    manifest.unlink()
    _symlink_or_emulate_unsafe_component(
        manifest,
        victim,
        monkeypatch=monkeypatch,
        fallback_content=original,
    )

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
    assert "v4-capable" in help_text
    assert "SHA spelling checked offline" in " ".join(help_text.split())
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
    assert (
        f"  WOULD REMOVE: {MANAGED_WORKFLOW_PATH.as_posix()}" in output.splitlines()
    )
    assert "Dry run complete. 1 item(s) would be affected." in output
    assert target.exists()

    monkeypatch.setattr("builtins.input", lambda _: "y")
    args.dry_run = False
    uninstall_cmd.run(args)

    output = capsys.readouterr().out
    assert f"  REMOVED: {MANAGED_WORKFLOW_PATH.as_posix()}" in output.splitlines()
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
