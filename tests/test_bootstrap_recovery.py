"""First-use failures retain a retry route without inventing provenance."""

from __future__ import annotations

import errno
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

from llm_wiki_cli import api, cli
from llm_wiki_cli.services import bootstrap_recovery as recovery
from llm_wiki_cli.services import bootstrap_runtime as runtime
from llm_wiki_cli.services import knowledge_governance as governance
from llm_wiki_cli.services.bootstrap_service import BootstrapRequest
from llm_wiki_cli.services.maintenance_protocol import (
    ADOPTION_FILENAME,
    MaintenanceProtocolError,
    guard_maintenance_owner,
    snapshot_wiki,
    WikiWriteBasis,
)
from llm_wiki_cli.services.sync_manifest import SyncManifest


def run_cli(monkeypatch, *arguments):
    monkeypatch.setattr(sys, "argv", ["llm-wiki", *arguments])
    try:
        cli.main()
    except SystemExit as exc:
        return exc.code
    return 0


def test_foreign_root_alias_keeps_recovery_outside_wiki(tmp_path, monkeypatch):
    wiki = tmp_path / "wiki"
    wiki.mkdir()
    canonical_alias = tmp_path / "canonical-spelling/wiki"
    resolve = Path.resolve

    def resolve_alias(path, *args, **kwargs):
        # Windows short names can resolve to another spelling of the same
        # directory without traversing a symbolic link or reparse point.
        return canonical_alias if path == wiki else resolve(path, *args, **kwargs)

    monkeypatch.setattr(Path, "resolve", resolve_alias)
    assert governance._governance_lock_root(wiki) == wiki
    record = recovery._record_path(wiki)
    assert not record.is_relative_to(wiki)
    assert not record.is_relative_to(canonical_alias)


@pytest.mark.parametrize("knowledge_format", ["v1", None], ids=["legacy", "current"])
@pytest.mark.parametrize("writer", ["api", "cli", "subprocess"])
def test_foreign_bootstrap_tracks_all_published_files(tmp_path, monkeypatch, knowledge_format, writer):
    monkeypatch.chdir(tmp_path)
    source = tmp_path / "state-consumer/template/src"
    source.mkdir(parents=True)
    (source / "item.py").write_text(
        "raise RuntimeError('target application must never execute')\n\n"
        "class Item:\n    value: int\n    label: str\n\n"
        "    def render(self, prefix: str = '') -> str:\n        return prefix + self.label\n",
        encoding="utf-8",
    )
    wiki = source.parent / "wiki"
    assert governance._governance_lock_root(wiki) == wiki
    original = WikiWriteBasis.assert_current

    def verify_publication(self):
        try:
            original(self)
        except MaintenanceProtocolError as error:
            actual = snapshot_wiki(self.root, include_transient=self.include_transient)
            differences = {
                "added": sorted(actual.keys() - self.expected.keys()),
                "removed": sorted(self.expected.keys() - actual.keys()),
                "changed": sorted(name for name in actual.keys() & self.expected.keys()
                                  if actual[name] != self.expected[name]),
            }
            raise AssertionError(differences) from error

    monkeypatch.setattr(WikiWriteBasis, "assert_current", verify_publication)
    if writer == "api":
        api.bootstrap_wiki(str(source), str(wiki), knowledge_format=knowledge_format)
    elif writer == "subprocess":
        cwd = source.parent
        if os.name == "nt":
            import ctypes
            from ctypes import wintypes

            short_path = ctypes.WinDLL("kernel32", use_last_error=True).GetShortPathNameW
            short_path.argtypes = [wintypes.LPCWSTR, wintypes.LPWSTR, wintypes.DWORD]
            short_path.restype = wintypes.DWORD
            required = short_path(str(cwd), None, 0)
            assert required, ctypes.get_last_error()
            buffer = ctypes.create_unicode_buffer(required)
            written = short_path(str(cwd), buffer, required)
            assert 0 < written < required, ctypes.get_last_error()
            cwd = Path(buffer.value)
            assert cwd.samefile(source.parent)
        arguments = [sys.executable, "-X", "utf8", "-I", "-m", "llm_wiki_cli.cli",
                     "bootstrap", "--src-dir", "src", "--wiki-dir", "wiki"]
        if knowledge_format is not None:
            arguments += ["--knowledge-format", knowledge_format]
        result = subprocess.run(arguments, cwd=cwd, capture_output=True, text=True,
                                encoding="utf-8", timeout=180, check=False,
                                env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1",
                                     "PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8"})
        assert result.returncode == 0, (result.stdout, result.stderr)
    else:
        arguments = ["bootstrap", "--src-dir", str(source), "--wiki-dir", str(wiki)]
        if knowledge_format is not None:
            arguments += ["--knowledge-format", knowledge_format]
        assert run_cli(monkeypatch, *arguments) == 0
    assert SyncManifest.load(wiki).artifact_hashes is not None
    assert not recovery.pending_bootstrap(wiki)


@pytest.fixture
def project(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".git").mkdir()
    (tmp_path / ".gitignore").write_text("docs/\n.llm-wiki/\nAGENTS.md\n__pycache__/\n")
    (tmp_path / "demo.py").write_text(
        'class Greeter:\n    def greet(self, name: str) -> str:\n        return f"Hello, {name}"\n'
    )
    assert run_cli(monkeypatch, "init", "--agent", "generic", "--no-skills") == 0
    return tmp_path / "docs/llm_wiki"


def bootstrap(wiki):
    options = runtime._bootstrap_run_options_from_args(
        cli._build_parser().parse_args(
            [
                "bootstrap",
                "--src-dir",
                ".",
                "--wiki-dir",
                str(wiki),
            ]
        )
    )
    return runtime._execute_bootstrap_options(options)


def assert_healthy(wiki, monkeypatch):
    manifest = SyncManifest.load(wiki)
    assert manifest.maintenance_state is not None
    assert manifest.evidence_baselines
    assert all(
        row.unknown_reason != "manifest-state-unavailable"
        for row in manifest.evidence_baselines.values()
    )
    guard_maintenance_owner(wiki)
    assert not recovery.pending_bootstrap(wiki)
    common = ["--src-dir", ".", "--wiki-dir", str(wiki), "--jobs", "1", "--no-cache"]
    assert run_cli(monkeypatch, "lint", "--strict", *common) == 0
    assert run_cli(monkeypatch, "ci-check", "--no-report", *common) == 0


@pytest.mark.parametrize("number", [errno.EPERM, errno.EACCES])
@pytest.mark.parametrize(
    "filename", ["llm-wiki-governance.lock", "llm-wiki-storage.lock"]
)
def test_lock_denial_precedes_every_wiki_write_and_retry_is_healthy(
    project, monkeypatch, number, filename
):
    before = snapshot_wiki(project)
    original = os.open
    locks = []

    def denied(path, flags, *args, **kwargs):
        if Path(path).name in recovery.LOCK_FILES:
            locks.append(Path(path).name)
            if Path(path).name == filename:
                raise PermissionError(number, "controlled lock denial", str(path))
        return original(path, flags, *args, **kwargs)

    with monkeypatch.context() as fault:
        fault.setattr(governance.os, "open", denied)
        with pytest.raises(governance.GovernanceError, match="lock-open-failed"):
            bootstrap(project)
    assert locks == (
        ["llm-wiki-governance.lock"]
        if filename == "llm-wiki-governance.lock"
        else ["llm-wiki-governance.lock", "llm-wiki-storage.lock"]
    )
    assert snapshot_wiki(project) == before
    assert not recovery.pending_bootstrap(project)
    bootstrap(project)
    assert_healthy(project, monkeypatch)


@pytest.mark.skipif(
    os.name == "nt" or (hasattr(os, "geteuid") and os.geteuid() == 0),
    reason="requires non-root POSIX permissions",
)
def test_actual_readonly_storage_lock_is_retryable(project, monkeypatch):
    path = Path(".git/llm-wiki-storage.lock")
    path.touch()
    before = snapshot_wiki(project)
    path.chmod(0o400)
    try:
        assert run_cli(monkeypatch, "bootstrap") == 1
        assert snapshot_wiki(project) == before
    finally:
        path.chmod(0o600)
    assert run_cli(monkeypatch, "bootstrap") == 0
    assert_healthy(project, monkeypatch)


def interrupt_after(monkeypatch, name, *, occurrence=1):
    from llm_wiki_cli.services import wiki_write_basis

    original = wiki_write_basis.after_wiki_write
    count = 0

    def interrupt(path, content):
        nonlocal count
        original(path, content)
        if Path(path).name == name:
            count += 1
            if count == occurrence:
                raise RuntimeError("interrupted bootstrap publication")

    monkeypatch.setattr(wiki_write_basis, "after_wiki_write", interrupt)


@pytest.mark.parametrize(
    ("name", "occurrence"),
    [
        ("Greeter.md", 1),
        (".llm-wiki-manifest.json", 1),
        (ADOPTION_FILENAME, 1),
        (".llm-wiki-knowledge.json", 3),
        (".llm-wiki-manifest.json", 3),
    ],
)
def test_interrupted_publication_recovers_with_fresh_evidence(
    project, monkeypatch, name, occurrence
):
    with monkeypatch.context() as fault:
        interrupt_after(fault, name, occurrence=occurrence)
        with pytest.raises(RuntimeError, match="interrupted bootstrap publication"):
            bootstrap(project)
    assert recovery.pending_bootstrap(project)
    before = snapshot_wiki(project)
    assert run_cli(monkeypatch, "sync", "--jobs", "1") == 2
    assert snapshot_wiki(project) == before
    # A retry must capture current source, not promote stale/unknown evidence.
    source = Path("demo.py")
    source.write_text(source.read_text().replace("Hello,", "Welcome,"))
    bootstrap(project)
    assert_healthy(project, monkeypatch)


@pytest.mark.parametrize(
    "change", ["edit", "add", "transient-name", "symlink", "authority"]
)
def test_retry_preserves_post_interruption_changes(project, monkeypatch, change):
    with monkeypatch.context() as fault:
        interrupt_after(fault, "Greeter.md")
        with pytest.raises(RuntimeError):
            bootstrap(project)
    page = project / "entities/Greeter.md"
    if change == "edit":
        page.write_text(page.read_text() + "\nUser-authored explanation.\n")
    elif change == "add":
        (project / "notes.md").write_text("# User notes\n")
    elif change == "transient-name":
        (project / ".llm-wiki-page-moves-user").write_text("User notes\n")
    elif change == "authority":
        (project / ADOPTION_FILENAME).write_text("{}\n")
    else:
        external = project.parent / "external.md"
        external.write_bytes(page.read_bytes())
        page.unlink()
        try:
            page.symlink_to(external)
        except OSError:
            pytest.skip("symlinks unavailable")
    before = {str(p): p.read_bytes() for p in project.rglob("*") if p.is_file()}
    with pytest.raises((MaintenanceProtocolError, ValueError, OSError)):
        bootstrap(project)
    assert {str(p): p.read_bytes() for p in project.rglob("*") if p.is_file()} == before
    assert recovery.pending_bootstrap(project)


def test_preserving_conflicting_tree_outside_target_allows_fresh_setup(
    project, monkeypatch
):
    with monkeypatch.context() as fault:
        interrupt_after(fault, "Greeter.md")
        with pytest.raises(RuntimeError):
            bootstrap(project)
    page = project / "entities/Greeter.md"
    page.write_bytes(page.read_bytes() + b"\nAuthored note.\n")
    before = snapshot_wiki(project)
    backup = project.with_name("preserved-incomplete-wiki")
    project.rename(backup)
    bootstrap(project)
    assert snapshot_wiki(backup) == before
    assert_healthy(project, monkeypatch)


def test_recovery_can_resume_after_its_own_interruption(project, monkeypatch):
    with monkeypatch.context() as fault:
        interrupt_after(fault, ".llm-wiki-manifest.json")
        with pytest.raises(RuntimeError):
            bootstrap(project)
    original = recovery.unlink_guarded_bytes
    count = 0

    def fail_second(*args, **kwargs):
        nonlocal count
        count += 1
        if count == 2:
            raise OSError("recovery write denied")
        return original(*args, **kwargs)

    with monkeypatch.context() as fault:
        fault.setattr(recovery, "unlink_guarded_bytes", fail_second)
        with pytest.raises(MaintenanceProtocolError, match="remains incomplete"):
            bootstrap(project)
    assert recovery.pending_bootstrap(project)
    bootstrap(project)
    assert_healthy(project, monkeypatch)


def test_uninterrupted_control_does_not_recover_later_adopted_history_loss(
    project, monkeypatch
):
    bootstrap(project)
    assert_healthy(project, monkeypatch)
    (project / ".llm-wiki-manifest.json").unlink()
    before = snapshot_wiki(project)
    with pytest.raises(MaintenanceProtocolError, match="owner is missing"):
        bootstrap(project)
    assert run_cli(monkeypatch, "bootstrap", "--overwrite") == 1
    assert snapshot_wiki(project) == before


def test_unrelated_manifestless_wiki_keeps_unknown_provenance(
    project, monkeypatch, capsys
):
    bootstrap(project)
    # Simulate an older unjournaled manifestless wiki, not an active operation.
    for path in project.glob(".llm-wiki-*.json"):
        path.unlink()
    import shutil

    for name in (".llm-wiki-knowledge", ".llm-wiki-manifest"):
        if (project / name).exists():
            shutil.rmtree(project / name)
    before = snapshot_wiki(project)
    assert run_cli(monkeypatch, "bootstrap") == 2
    assert "unjournaled failed bootstrap" in capsys.readouterr().err
    assert snapshot_wiki(project) == before
    assert (
        run_cli(monkeypatch, "sync", "--jobs", "1", "--no-cache", "--rebuild-knowledge")
        == 0
    )
    manifest = SyncManifest.load(project)
    assert any(
        row.unknown_reason == "manifest-state-unavailable"
        for row in manifest.evidence_baselines.values()
    )
    capsys.readouterr()
    before = snapshot_wiki(project)
    assert run_cli(monkeypatch, "bootstrap") == 2
    assert "unjournaled failed bootstrap" in capsys.readouterr().err
    assert snapshot_wiki(project) == before


@pytest.mark.parametrize("wiki_name", ["wiki", ".llm-wiki"])
def test_non_git_empty_target_retry_keeps_lock_files_operational(
    tmp_path, monkeypatch, wiki_name
):
    monkeypatch.chdir(tmp_path)
    source = tmp_path / "src"
    source.mkdir()
    (source / "demo.py").write_text("class Greeter:\n    pass\n")
    wiki = tmp_path / wiki_name
    request = BootstrapRequest(source_root=source, wiki_root=wiki)
    with monkeypatch.context() as fault:
        interrupt_after(fault, "Greeter.md")
        with pytest.raises(RuntimeError):
            runtime.execute_bootstrap(request)
    runtime.execute_bootstrap(request)
    guard_maintenance_owner(wiki)
    assert not recovery.pending_bootstrap(wiki)
    assert not recovery._record_path(wiki).is_relative_to(wiki)


def test_non_git_source_adapter_recovery_does_not_write_beside_nested_wiki(
    tmp_path, monkeypatch
):
    source = tmp_path / "source"
    source.mkdir()
    monkeypatch.chdir(source)
    (source / "demo.py").write_text("class Greeter:\n    pass\n")
    (source / ".gitignore").write_text("docs/\n")
    wiki = source / "docs/wiki"

    def source_bytes():
        return {
            p.relative_to(source).as_posix(): p.read_bytes()
            for p in source.rglob("*")
            if p.is_file() and not p.is_relative_to(wiki)
        }

    before = source_bytes()
    arguments = cli._build_parser().parse_args(
        [
            "bootstrap",
            "--src-dir",
            ".",
            "--wiki-dir",
            str(wiki),
            "--source-adapter",
        ]
    )
    with monkeypatch.context() as fault:
        interrupt_after(fault, "Greeter.md")
        with pytest.raises(RuntimeError):
            runtime.run(arguments)
    assert source_bytes() == before
    assert not recovery._record_path(wiki).is_relative_to(source)
    runtime.run(arguments)
    assert source_bytes() == before
    assert not recovery.pending_bootstrap(wiki)


def test_process_exit_between_replacement_and_observation_is_recoverable(
    project, monkeypatch
):
    import llm_wiki_cli

    script = """
import os
from pathlib import Path
import sys
from llm_wiki_cli import cli
from llm_wiki_cli.services import wiki_write_basis
original = wiki_write_basis.after_wiki_write
def stop(path, content):
    if Path(path).name == 'Greeter.md':
        os._exit(73)
    original(path, content)
wiki_write_basis.after_wiki_write = stop
sys.argv = ['llm-wiki', 'bootstrap']
cli.main()
"""
    env = {
        **os.environ,
        "PYTHONPATH": str(Path(llm_wiki_cli.__file__).resolve().parent.parent),
    }
    result = subprocess.run(
        [sys.executable, "-c", script], env=env, capture_output=True, text=True
    )
    assert result.returncode == 73, result.stdout + result.stderr
    assert recovery.pending_bootstrap(project)
    bootstrap(project)
    assert_healthy(project, monkeypatch)


def test_unadopted_writers_cannot_enter_during_bootstrap_capture(project, monkeypatch):
    from concurrent.futures import ThreadPoolExecutor
    from llm_wiki_cli.services.maintenance_protocol import maintenance_write_operation

    original = runtime._extract_bootstrap_inventory

    def writer():
        with maintenance_write_operation(project):
            pytest.fail("another writer entered bootstrap's critical section")

    def extract(state):
        with ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(writer)
            with pytest.raises(governance.GovernanceConflictError):
                future.result()
        return original(state)

    monkeypatch.setattr(runtime, "_extract_bootstrap_inventory", extract)
    bootstrap(project)
    assert_healthy(project, monkeypatch)


@pytest.mark.parametrize("damage", ["root", "path", "preimage", "journal-hash"])
def test_invalid_recovery_proof_never_changes_wiki(project, monkeypatch, damage):
    with monkeypatch.context() as fault:
        interrupt_after(fault, "Greeter.md")
        with pytest.raises(RuntimeError):
            bootstrap(project)
    path = recovery._record_path(project)
    record = json.loads(path.read_bytes())
    directory = path.parent / record["operation_id"]
    if damage == "root":
        record["wiki_root"] = str(project.parent / "another-wiki")
        path.write_bytes(recovery.canonical_bytes(record))
    elif damage == "preimage":
        (directory / "index.md").write_bytes(b"different preimage")
    else:
        journal_path = directory / "publication-journal.json"
        journal = json.loads(journal_path.read_bytes())
        if damage == "path":
            journal["eligible_images"]["../outside.md"] = [None]
        else:
            journal["preimage_metadata_hash"] = "sha256:" + "0" * 64
        journal_path.write_bytes(recovery.canonical_bytes(journal))
    before = snapshot_wiki(project)
    with pytest.raises(MaintenanceProtocolError):
        bootstrap(project)
    assert snapshot_wiki(project) == before


def test_failed_completion_never_reports_success(project, monkeypatch, capsys):
    original = recovery._complete

    def fail(root, record, *, status="complete"):
        if status == "complete":
            raise OSError("cannot commit recovery completion")
        return original(root, record, status=status)

    capsys.readouterr()
    with monkeypatch.context() as fault:
        fault.setattr(recovery, "_complete", fail)
        assert run_cli(fault, "bootstrap", "--format", "json") == 1
    output = capsys.readouterr()
    assert output.out == ""
    assert "Bootstrap complete" not in output.err
    assert "Retry the same bootstrap command" in output.err
    assert recovery.pending_bootstrap(project)
    bootstrap(project)
    assert_healthy(project, monkeypatch)


def test_overwrite_refusal_for_interrupted_setup_points_back_to_bootstrap(
    project, monkeypatch, capsys
):
    with monkeypatch.context() as fault:
        interrupt_after(fault, ".llm-wiki-manifest.json")
        with pytest.raises(RuntimeError):
            bootstrap(project)
    before = snapshot_wiki(project)
    capsys.readouterr()
    assert run_cli(monkeypatch, "bootstrap", "--overwrite") == 2
    error = capsys.readouterr().err
    assert "interrupted first-use bootstrap" in error
    assert "llm-wiki sync" not in error
    assert snapshot_wiki(project) == before
