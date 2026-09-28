"""Credential-related identifiers survive storage and governance operations."""

import sys

import pytest

from llm_wiki_cli import api
from llm_wiki_cli.cli import main
from llm_wiki_cli.services.knowledge_governance import (
    GOVERNANCE_FILENAME, load_governance,
)
from llm_wiki_cli.services.knowledge_loader import load_knowledge_state
from llm_wiki_cli.services.knowledge_storage_access import capture_knowledge_slice
from llm_wiki_cli.services.knowledge_storage_diagnostics import storage_report
from llm_wiki_cli.services.knowledge_storage_lifecycle import (
    export_knowledge_v1, migrate_knowledge_storage, recover_knowledge_storage,
)
from llm_wiki_cli.services.section_ownership import observe_page_sections
from llm_wiki_cli.services.wiki_surface import PageKind
from tests.test_knowledge_storage_lifecycle import snapshot


NAMES = (
    "RuntimeSecretField", "SecretMaterialError", "ResetPasswordForm",
    "PasswdEntry", "ApiKeySettings", "AccessTokenProvider", "PrivateKeyStore",
)


@pytest.fixture(params=[False, True], ids=["ungoverned", "governed"])
def credential_named_wiki(tmp_path, monkeypatch, capsys, request):
    monkeypatch.chdir(tmp_path)
    # Do not discover the caller's Git repository under a custom pytest base.
    (tmp_path / ".git").write_text("gitdir: absent\n", encoding="utf-8")
    source = tmp_path / "source"
    source.mkdir()
    (source / "models.py").write_text(
        "\n\n".join(f'class {name}:\n    """A documented field type."""\n    pass' for name in NAMES),
        encoding="utf-8",
    )
    root = tmp_path / "wiki"
    api.bootstrap_wiki(str(source), str(root), skip_workflows=True,
                       skip_flows=True, skip_dependencies=True)

    def command(*args):
        monkeypatch.setattr(sys, "argv", ["llm-wiki", *args])
        main()
        return capsys.readouterr()

    page = root / "entities" / "RuntimeSecretField.md"
    content = page.read_text(encoding="utf-8")
    assert "## Description" in content
    page.write_text(content.replace("## Description", "## Description\n\nPreserve this authored explanation.", 1),
                    encoding="utf-8")
    command("sync", "--src-dir", "source", "--wiki-dir", "wiki", "--jobs", "1",
            "--no-plugins", "--progress", "never")
    selectors = [f"code-entity:entities/{name}.md" for name in NAMES]
    if request.param:
        command("knowledge", "init", "--wiki-dir", "wiki")
        ledger = load_governance(root).ledger
        assert ledger is not None
        allocation = next(a for a in ledger.concepts.values()
                          if a.locator == "llm-wiki://entities/RuntimeSecretField")
        historical = "llm-wiki://entities/PreviousSecretField"
        command("knowledge", "alias", "--wiki-dir", "wiki", "--uid", allocation.uid,
                "--type", "locator", "--value", historical)
        observed = observe_page_sections(page.read_text(encoding="utf-8"), allocation.locator, PageKind.ENTITIES)
        section = next(s for s in observed.sections if s.title == "Description" and s.semantic_hash is not None)
        command("knowledge", "review", "--wiki-dir", "wiki", "--uid", allocation.uid,
                "--section", section.locator, "--reviewer-kind", "human", "--reviewer-id", "reviewer-1",
                "--method", "manual-review", "--method-version", "1", "--authored-at", "2026-09-28T12:00:00Z")
        selectors.extend([allocation.uid, historical])
    else:
        assert not (root / GOVERNANCE_FILENAME).exists()
    return root, selectors, command


@pytest.mark.parametrize("format_name", [
    "sharded-v2", "packed-v3", "packed-v3-deflate", "packed-v4", "packed-v4-deflate",
])
def test_migration_preserves_named_concepts_authority_aliases_and_recovery(
    credential_named_wiki, tmp_path, format_name,
):
    root, selectors, _command = credential_named_wiki
    before = snapshot(root)
    logical = load_knowledge_state(root).knowledge
    recovery = tmp_path / "recovery"
    preview = migrate_knowledge_storage(root, to=format_name, dry_run=True, recovery_dir=recovery)
    assert preview["changed"]
    assert snapshot(root) == before
    assert not recovery.exists()

    applied = migrate_knowledge_storage(root, to=format_name, recovery_dir=recovery)
    assert applied["root_hash"] == preview["root_hash"]
    assert load_knowledge_state(root).knowledge == logical
    for name, raw in before.items():
        if name.endswith(".md") or name == GOVERNANCE_FILENAME:
            assert (root / name).read_bytes() == raw
    after = snapshot(root)
    assert not migrate_knowledge_storage(root, to=format_name)["changed"]
    assert snapshot(root) == after

    # Both manifest encodings must support lookup validation with these names.
    for indexed_manifest in (False, True):
        if indexed_manifest:
            migrate_knowledge_storage(root, to="indexed-v6", recovery_dir=tmp_path / "manifest-recovery")
        assert load_knowledge_state(root).knowledge == logical
        assert storage_report(root, full=True)["integrity"] == "valid-committed-snapshot"
        for selector in selectors:
            capture = capture_knowledge_slice(root, ["concept:" + selector], collections=("concepts",))
            selected = capture.slice.to_payload()
            assert selected["lookup_complete"]
            assert len(selected["records"]["concepts"]) == 1, selector
            assert selected["records"]["concepts"][0]["value"]["title"] in NAMES
            capture.finish()
        task = {
            "schema_version": "llm-wiki-task-request/v2",
            "options": {"read_scope": "snapshot", "knowledge_mode": "required"},
            "requirements": [{"id": "field", "facet": "concept", "selector": selectors[-1]}],
        }
        answer = api.build_task_context(task, wiki_dir=str(root))
        assert api.validate_task_context(answer.rendered, task)["state"] == "covered"

    export_knowledge_v1(root, tmp_path / "export.json")
    assert (tmp_path / "export.json").read_bytes() == before[".llm-wiki-knowledge.json"]
    recover_knowledge_storage(root, tmp_path / "manifest-recovery")
    recover_knowledge_storage(root, recovery)
    for name, raw in before.items():
        assert (root / name).read_bytes() == raw
    assert load_knowledge_state(root).knowledge == logical


def test_sync_preserves_named_concepts_and_governance_after_migration(credential_named_wiki, tmp_path):
    root, _selectors, command = credential_named_wiki
    before = snapshot(root)
    migrate_knowledge_storage(root, to="packed-v4-deflate", recovery_dir=tmp_path / "recovery")
    command("sync", "--src-dir", "source", "--wiki-dir", "wiki", "--jobs", "1",
            "--no-plugins", "--progress", "never")
    assert "Preserve this authored explanation." in (root / "entities" / "RuntimeSecretField.md").read_text(encoding="utf-8")
    if GOVERNANCE_FILENAME in before:
        assert (root / GOVERNANCE_FILENAME).read_bytes() == before[GOVERNANCE_FILENAME]
    report = storage_report(root, full=True)
    assert report["ok"] and report["format"] == "packed-v4-deflate"
    first_sync = snapshot(root)
    command("sync", "--src-dir", "source", "--wiki-dir", "wiki", "--jobs", "1",
            "--no-plugins", "--progress", "never")
    assert snapshot(root) == first_sync
