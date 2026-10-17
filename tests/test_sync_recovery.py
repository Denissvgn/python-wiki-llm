"""Rejected publication recovery keeps source, prose and authority separate."""

import json
from pathlib import Path

import pytest

from llm_wiki_cli import cli
from llm_wiki_cli.commands import bootstrap_cmd, sync_cmd
from llm_wiki_cli.services import knowledge_orchestration as ko
from llm_wiki_cli.services import sync_recovery as recovery
from llm_wiki_cli.services.knowledge_storage import canonical_bytes, digest
from llm_wiki_cli.services.knowledge_storage_diagnostics import storage_report
from llm_wiki_cli.services.maintenance_protocol import snapshot_wiki


def rejected(tmp_path, monkeypatch, capsys, layout: str | None = "v1"):
    monkeypatch.chdir(tmp_path)
    source = tmp_path / "src"
    source.mkdir()
    (source / "app.py").write_text("def value():\n    return 1\n")
    wiki = tmp_path / "wiki"
    args = [
        "bootstrap",
        "--src-dir",
        "src",
        "--wiki-dir",
        "wiki",
        "--skip-workflows",
        "--skip-flows",
    ]
    if layout is not None:
        args += ["--knowledge-format", layout]
    bootstrap_cmd.run(cli._build_parser().parse_args(args))
    capsys.readouterr()
    (wiki / "personal.md").write_bytes(b"User-owned notes\r\n")
    sync_cmd.run(
        cli._build_parser().parse_args(
            ["sync", "--src-dir", "src", "--wiki-dir", "wiki"]
        )
    )
    capsys.readouterr()
    assert storage_report(wiki, full=True)["ok"]
    anchors = recovery._anchors(wiki)
    (source / "new_module.py").write_text("class NewEntity:\n    pass\n")
    original = ko._require_runtime_source_current
    injected = []

    def mutate(snapshot):
        if not injected and (wiki / "modules/new_module.md").exists():
            (source / "app.py").write_text("def value():\n    return 2\n")
            injected.append(True)
        return original(snapshot)

    with monkeypatch.context() as patch:
        patch.setattr(ko, "_require_runtime_source_current", mutate)
        with pytest.raises((ko.KnowledgeGenerationError, SystemExit)):
            sync_cmd.run(
                cli._build_parser().parse_args(
                    ["sync", "--src-dir", "src", "--wiki-dir", "wiki"]
                )
            )
    assert injected
    diagnostic = capsys.readouterr().err
    info = next(
        json.loads(line)["new_page_recovery"]
        for line in diagnostic.splitlines()
        if line.startswith('{"new_page_recovery"')
    )
    directory = Path(info["recovery_dir"])
    record = json.loads((directory / "sync-recovery.json").read_bytes())
    assert record["status"] == "rejected"
    assert {"modules/new_module.md", "entities/NewEntity.md"} <= record["pages"].keys()
    assert recovery._anchors(wiki) == anchors
    return wiki, directory, info, record


def recover(wiki, directory, info, **kwargs):
    return recovery.recover_new_sync_pages(
        wiki,
        recovery_dir=directory,
        expected_journal_hash=info["expected_journal_hash"],
        **kwargs,
    )


@pytest.mark.parametrize(
    "layout",
    [
        "v1",
        "sharded-v2",
        "packed-v3",
        "packed-v3-deflate",
        "packed-v4",
        "packed-v4-deflate",
        None,
    ],
)
def test_rejected_sync_cli_preview_recovery_and_retry(
    tmp_path, monkeypatch, capsys, layout
):
    wiki, directory, info, record = rejected(tmp_path, monkeypatch, capsys, layout)
    assert (wiki / "entities/NewEntity.md").exists()  # No implicit rollback.
    before = snapshot_wiki(wiki)
    source_before = {p.name: p.read_bytes() for p in Path("src").iterdir()}
    storage_report(wiki, full=True)  # The rejected generation need not be ready.
    assert snapshot_wiki(wiki) == before  # A reader never repairs pages.
    args = [
        "maintenance",
        "recover-new-pages",
        "--wiki-dir",
        str(wiki),
        "--recovery-dir",
        str(directory),
        "--expected-journal-hash",
        info["expected_journal_hash"],
    ]
    with monkeypatch.context() as patch:
        patch.setattr("sys.argv", ["llm-wiki", *args, "--dry-run"])
        cli.main()
    preview = json.loads(capsys.readouterr().out)
    assert preview["dry_run"] and snapshot_wiki(wiki) == before
    with monkeypatch.context() as patch:
        patch.setattr("sys.argv", ["llm-wiki", *args])
        cli.main()
    result = json.loads(capsys.readouterr().out)
    assert not result["dry_run"] and set(result["pages"]) == set(record["pages"])
    after = snapshot_wiki(wiki)
    assert after == {k: v for k, v in before.items() if k not in record["pages"]}
    assert after["personal.md"] == b"User-owned notes\r\n"
    assert {p.name: p.read_bytes() for p in Path("src").iterdir()} == source_before
    for name in record["pages"]:
        assert (directory / (digest(before[name])[7:] + ".bin")).read_bytes() == before[
            name
        ]
    sync_args = cli._build_parser().parse_args(
        ["sync", "--src-dir", "src", "--wiki-dir", "wiki"]
    )
    sync_cmd.run(sync_args)
    assert storage_report(wiki, full=True)["ok"]
    complete = snapshot_wiki(wiki)
    sync_cmd.run(sync_args)
    assert snapshot_wiki(wiki) == complete


@pytest.mark.parametrize(
    "change",
    [
        "edited",
        "replaced",
        "symlink",
        "hardlink",
        "authority",
        "backup",
        "hash",
        "wrong-wiki",
        "preexisting",
        "source-owned",
        "traversal",
        "committed",
        "policy",
        "unrelated",
    ],
)
def test_recovery_refuses_changed_or_unrelated_state_before_deletion(
    tmp_path, monkeypatch, capsys, change
):
    wiki, directory, info, record = rejected(tmp_path, monkeypatch, capsys)
    page = wiki / "entities/NewEntity.md"
    if change == "edited":
        page.write_bytes(page.read_bytes() + b"user edit")
    elif change == "replaced":
        content = page.read_bytes()
        page.unlink()
        page.write_bytes(content)
    elif change in {"symlink", "hardlink"}:
        content = page.read_bytes()
        other = tmp_path / "outside.md"
        other.write_bytes(content)
        page.unlink()
        if change == "symlink":
            page.symlink_to(other)
        else:
            import os

            os.link(other, page)
    elif change == "authority":
        (wiki / ".llm-wiki-manifest.json").write_bytes(b"changed authority")
    elif change == "backup":
        (directory / (digest(page.read_bytes())[7:] + ".bin")).write_bytes(
            b"changed backup"
        )
    elif change == "hash":
        info["expected_journal_hash"] = "sha256:" + "0" * 64
    elif change == "wrong-wiki":
        wiki = tmp_path / "other-wiki"
        wiki.mkdir()
    elif change == "policy":
        (tmp_path / "src/.gitignore").write_text("wiki/\n")
    else:
        if change == "preexisting":
            record["preexisting_pages"].append("entities/NewEntity.md")
        elif change == "source-owned":
            record["source_paths"].append(str(page))
        elif change == "traversal":
            record["pages"]["../outside.md"] = record["pages"].pop(
                "entities/NewEntity.md"
            )
        elif change == "unrelated":
            (wiki / "unrelated.md").write_bytes(page.read_bytes())
            record["pages"]["unrelated.md"] = record["pages"].pop(
                "entities/NewEntity.md"
            )
        else:
            record["status"] = "committed"
        raw = canonical_bytes(record)
        (directory / "sync-recovery.json").write_bytes(raw)
        info["expected_journal_hash"] = digest(raw)
    before = {
        p: p.read_bytes() for p in wiki.rglob("*") if p.is_file() and not p.is_symlink()
    }
    with pytest.raises((ValueError, OSError)):
        recover(wiki, directory, info)
    assert {p: p.read_bytes() for p in before} == before
    assert page.exists()


def test_journal_hash_rejects_modified_inventory(tmp_path, monkeypatch, capsys):
    wiki, directory, info, record = rejected(tmp_path, monkeypatch, capsys)
    record["pages"] = {}
    (directory / "sync-recovery.json").write_bytes(canonical_bytes(record))
    with pytest.raises(ValueError, match="rejection-bound hash"):
        recover(wiki, directory, info)


def test_recovery_io_failure_preserves_backups_and_never_claims_success(
    tmp_path, monkeypatch, capsys
):
    wiki, directory, info, record = rejected(tmp_path, monkeypatch, capsys)
    contents = {name: (wiki / name).read_bytes() for name in record["pages"]}
    original = recovery.unlink_guarded_bytes
    calls = []

    def fail_second(path, **kwargs):
        calls.append(path)
        if len(calls) == 2:
            raise OSError("controlled unlink failure")
        return original(path, **kwargs)

    monkeypatch.setattr(recovery, "unlink_guarded_bytes", fail_second)
    with pytest.raises((ValueError, OSError), match="controlled unlink failure"):
        recover(wiki, directory, info)
    for raw in contents.values():
        assert (directory / (digest(raw)[7:] + ".bin")).read_bytes() == raw
    assert recovery._anchors(wiki) == record["anchors"]


@pytest.mark.parametrize(
    "field,value",
    [
        ("transaction_id", None),
        ("preexisting_pages", [False]),
        ("source_paths", {}),
        ("pages", {"x.md": [1]}),
        ("policy_inputs", []),
    ],
)
def test_malformed_bound_journal_has_domain_refusal(
    tmp_path, monkeypatch, capsys, field, value
):
    wiki, directory, info, record = rejected(tmp_path, monkeypatch, capsys)
    record[field] = value
    raw = canonical_bytes(record)
    (directory / "sync-recovery.json").write_bytes(raw)
    info["expected_journal_hash"] = digest(raw)
    before = snapshot_wiki(wiki)
    with pytest.raises(ValueError):
        recover(wiki, directory, info)
    assert snapshot_wiki(wiki) == before


def test_committed_authority_change_during_apply_stops_remaining_deletions(
    tmp_path, monkeypatch, capsys
):
    wiki, directory, info, record = rejected(tmp_path, monkeypatch, capsys)
    original = recovery.unlink_guarded_bytes
    removed = []

    def change_after_first(path, **kwargs):
        original(path, **kwargs)
        removed.append(path)
        (wiki / ".llm-wiki-manifest.json").write_bytes(b"newer owner")

    monkeypatch.setattr(recovery, "unlink_guarded_bytes", change_after_first)
    with pytest.raises(ValueError, match="stopped after 1 page"):
        recover(wiki, directory, info)
    assert len(removed) == 1
    assert (wiki / ".llm-wiki-manifest.json").read_bytes() == b"newer owner"
    assert (wiki / "modules/new_module.md").exists()


def test_read_only_and_no_new_page_operations_create_no_journal(tmp_path):
    from llm_wiki_cli.services.source_snapshot import build_source_snapshot

    source, wiki = tmp_path / "src", tmp_path / "wiki"
    source.mkdir()
    wiki.mkdir()
    (source / "app.py").write_text("x=1\n")
    snapshot = build_source_snapshot(source)
    with recovery.capture_new_sync_pages(wiki, snapshot):
        assert list(wiki.iterdir()) == []
    assert list(wiki.iterdir()) == []


def test_oversized_new_page_fails_before_file_write(tmp_path):
    from llm_wiki_cli.services.io import write_bytes_atomic
    from llm_wiki_cli.services.source_snapshot import build_source_snapshot

    source, wiki = tmp_path / "src", tmp_path / "wiki"
    source.mkdir()
    wiki.mkdir()
    with pytest.raises(ValueError, match="bound"):
        with recovery.capture_new_sync_pages(wiki, build_source_snapshot(source)):
            write_bytes_atomic(wiki / "oversized.md", b"x" * (recovery.MAX_FILE + 1))
    assert list(wiki.iterdir()) == []


def test_current_manifest_owner_cannot_be_deleted_by_modified_journal(
    tmp_path, monkeypatch, capsys
):
    from llm_wiki_cli.services.knowledge_storage_io import read_guarded

    wiki, directory, info, record = rejected(tmp_path, monkeypatch, capsys)
    owned = wiki / "modules/app.md"
    observed = read_guarded(owned, recovery.MAX_FILE)
    record["preexisting_pages"].remove("modules/app.md")
    record["pages"]["modules/app.md"] = [
        {
            "hash": digest(observed.content),
            "bytes": len(observed.content),
            "identity": list(observed.identity),
        }
    ]
    (directory / (digest(observed.content)[7:] + ".bin")).write_bytes(observed.content)
    raw = canonical_bytes(record)
    (directory / "sync-recovery.json").write_bytes(raw)
    info["expected_journal_hash"] = digest(raw)
    before = snapshot_wiki(wiki)
    with pytest.raises(ValueError, match="source-owned"):
        recover(wiki, directory, info)
    assert snapshot_wiki(wiki) == before


def test_adopted_complete_preimage_recovery_remains_available(
    tmp_path, monkeypatch, capsys
):
    from llm_wiki_cli import api
    from llm_wiki_cli.services import maintenance_protocol

    captured = []
    original = maintenance_protocol.save_recovery_snapshot

    def retain(directory, files, **kwargs):
        result = original(directory, files, **kwargs)
        if kwargs.get("kind") == "captured-preimage":
            captured.append((directory, dict(files)))
        return result

    monkeypatch.setattr(maintenance_protocol, "save_recovery_snapshot", retain)
    wiki, _, _, _ = rejected(tmp_path, monkeypatch, capsys, None)
    directory, before = captured[-1]
    marker = json.loads(before[maintenance_protocol.ADOPTION_FILENAME])
    api.recover_maintenance(
        str(wiki),
        recovery_dir=directory,
        expected_adoption_id=marker["adoption_id"],
        allow_captured_preimage=True,
    )
    assert snapshot_wiki(wiki) == before
    assert (Path("src") / "app.py").read_text() == "def value():\n    return 2\n"


def test_journal_bounds_do_not_block_operations_without_new_pages(
    tmp_path, monkeypatch
):
    from llm_wiki_cli.services.io import write_bytes_atomic
    from llm_wiki_cli.services.source_snapshot import build_source_snapshot

    source, wiki = tmp_path / "src", tmp_path / "wiki"
    source.mkdir()
    wiki.mkdir()
    (wiki / "one.md").write_bytes(b"one")
    (wiki / "two.md").write_bytes(b"two")
    monkeypatch.setattr(recovery, "MAX_PAGES", 1)
    with recovery.capture_new_sync_pages(wiki, build_source_snapshot(source)):
        write_bytes_atomic(wiki / "one.md", b"updated existing page")
    assert (wiki / "one.md").read_bytes() == b"updated existing page"


def test_changed_selection_before_capture_does_not_authorize_new_pages(tmp_path):
    from llm_wiki_cli.services.source_snapshot import build_source_snapshot

    source, wiki = tmp_path / "src", tmp_path / "wiki"
    source.mkdir()
    wiki.mkdir()
    (source / "app.py").write_text("x=1\n")
    (source / ".gitignore").write_text("excluded/\n")
    snapshot = build_source_snapshot(source, respect_ignores=True, coherent=True)
    (source / ".gitignore").write_text("another-selection/\n")
    with pytest.raises(ValueError, match="selection changed"):
        with recovery.capture_new_sync_pages(wiki, snapshot):
            pytest.fail("Changed source selection must refuse before writes")
    assert list(wiki.iterdir()) == []


def test_cli_refuses_wiki_outside_project_before_reading_journal(
    tmp_path, monkeypatch, capsys
):
    project = tmp_path / "project"
    project.mkdir()
    monkeypatch.chdir(project)
    outside = tmp_path / "outside-wiki"
    outside.mkdir()
    monkeypatch.setattr(
        "sys.argv",
        [
            "llm-wiki",
            "maintenance",
            "recover-new-pages",
            "--wiki-dir",
            str(outside),
            "--recovery-dir",
            str(tmp_path / "missing"),
            "--expected-journal-hash",
            "sha256:" + "0" * 64,
        ],
    )
    with pytest.raises(SystemExit) as exc:
        cli.main()
    assert exc.value.code == 1
    assert (
        "outside the project root"
        in json.loads(capsys.readouterr().out)["error"]["message"]
    )
    assert list(outside.iterdir()) == []


@pytest.mark.parametrize("foreign", [False, True])
def test_success_discards_only_unchanged_private_scratch(
    tmp_path, monkeypatch, capsys, foreign
):
    from llm_wiki_cli.services.io import write_bytes_atomic
    from llm_wiki_cli.services.source_snapshot import build_source_snapshot

    source, wiki = tmp_path / "src", tmp_path / "wiki"
    source.mkdir()
    wiki.mkdir()
    journals = []
    original = recovery.NewPageJournal.discard_committed

    def inspect(journal):
        journals.append(journal.directory)
        if foreign:
            (journal.directory / "unrelated.txt").write_bytes(b"preserve")
        return original(journal)

    monkeypatch.setattr(recovery.NewPageJournal, "discard_committed", inspect)
    with recovery.capture_new_sync_pages(wiki, build_source_snapshot(source)):
        write_bytes_atomic(wiki / "new.md", b"committed page")
    assert (wiki / "new.md").read_bytes() == b"committed page"
    directory = journals[0]
    if foreign:
        assert (directory / "unrelated.txt").read_bytes() == b"preserve"
        assert (
            json.loads((directory / "sync-recovery.json").read_bytes())["status"]
            == "committed"
        )
        assert (
            directory / (digest(b"committed page")[7:] + ".bin")
        ).read_bytes() == b"committed page"
        assert "scratch retained" in capsys.readouterr().err
    else:
        assert not directory.exists()
        assert capsys.readouterr().err == ""
