"""P2 resilience coverage for enriched Site and Obsidian projections."""

from __future__ import annotations

import json
import sys
from dataclasses import replace
from pathlib import Path

import pytest

import llm_wiki_cli.cli as cli
from llm_wiki_cli.commands import obsidian_cmd, site_cmd
from llm_wiki_cli.services import io as wiki_io
from llm_wiki_cli.services import obsidian, site_export
from llm_wiki_cli.services.knowledge_consumption import load_knowledge_read_view
from llm_wiki_cli.services.knowledge_projection import project_knowledge
from tests.knowledge_fixtures import FIXTURE_REPOSITORY_IDENTITY
from tests.test_knowledge_projection_e2e import (
    _commit_governed_fixture,
    _tree_bytes,
)


def _tree_paths(root: Path) -> tuple[str, ...]:
    return tuple(
        sorted(path.relative_to(root).as_posix() for path in root.rglob("*"))
    )


def test_site_check_compares_every_supplied_knowledge_selection(tmp_path):
    wiki = _commit_governed_fixture(tmp_path)
    view = load_knowledge_read_view(
        wiki,
        snapshot_only=True,
        include_machine_verification=True,
    )
    projection = project_knowledge(
        view,
        profile="public-portable",
        public_repository_identity=FIXTURE_REPOSITORY_IDENTITY,
    )
    out = tmp_path / "site"
    site_export.export_site_mirror(
        wiki_dir=wiki,
        out_dir=out,
        format="mkdocs",
        knowledge_metadata="summary",
        knowledge_projection=projection,
    )

    matching = site_export.check_site_mirror(
        wiki_dir=wiki,
        out_dir=out,
        format="mkdocs",
        link_mode="http",
        knowledge_metadata="summary",
        knowledge_projection=projection,
    )
    omitted_selection = site_export.check_site_mirror(
        wiki_dir=wiki,
        out_dir=out,
        format="mkdocs",
        link_mode="http",
    )

    assert matching.ok is True
    assert {
        issue.get("target")
        for issue in omitted_selection.issues
        if issue["category"] == "publication_selection_mismatch"
    } == {
        "knowledge_metadata",
        "knowledge_profile",
        "public_identity_digest",
    }
    assert any(
        issue["category"] == "publication_projection_mismatch"
        for issue in omitted_selection.issues
    )


@pytest.mark.parametrize("knowledge_profile", ["public-portable", "internal"])
def test_enriched_existing_outputs_dry_run_plan_every_write_without_mutation(
    tmp_path,
    monkeypatch,
    capsys,
    knowledge_profile,
):
    wiki = _commit_governed_fixture(tmp_path)
    native_before = _tree_bytes(wiki)
    native_paths_before = _tree_paths(wiki)
    view = load_knowledge_read_view(
        wiki,
        snapshot_only=True,
        include_machine_verification=True,
    )
    public_projection = project_knowledge(view, profile="public-portable")
    requested_projection = project_knowledge(view, profile=knowledge_profile)
    assert requested_projection.profile.value == knowledge_profile

    site = tmp_path / "existing-site"
    vault = tmp_path / "existing-vault"
    site_export.export_site_mirror(
        wiki_dir=wiki,
        out_dir=site,
        format="mkdocs",
        knowledge_metadata="summary",
        knowledge_projection=requested_projection,
    )
    obsidian.export_obsidian_vault(
        src_dir=str(tmp_path / "source-is-not-read"),
        wiki_dir=wiki,
        vault_dir=vault,
        knowledge_metadata="summary",
        knowledge_projection=public_projection,
    )
    human_sidecar = (
        vault
        / ".llm-wiki"
        / "obsidian-notes"
        / "entity"
        / "User.md"
    )
    human_sidecar.write_text(
        "# Human-owned notes\n\nKeep this exact text.\n",
        encoding="utf-8",
    )

    site_before = _tree_bytes(site)
    site_paths_before = _tree_paths(site)
    vault_before = _tree_bytes(vault)
    vault_paths_before = _tree_paths(vault)

    site_report = site_export.export_site_mirror(
        wiki_dir=wiki,
        out_dir=site,
        format="mkdocs",
        dry_run=True,
        knowledge_metadata="summary",
        knowledge_projection=requested_projection,
    )
    assert site_report.dry_run is True
    assert {operation.action for operation in site_report.operations} == {
        "would_write"
    }
    assert {
        operation.action for operation in site_report.asset_operations
    }.issubset({"would_copy", "stale_asset"})
    planned_site_files = {
        Path(operation.path).relative_to(site).as_posix()
        for operation in (
            *site_report.operations,
            *[
                operation
                for operation in site_report.asset_operations
                if operation.action == "would_copy"
            ],
        )
    }
    assert planned_site_files == set(site_before)

    obsidian_report = obsidian.export_obsidian_vault(
        src_dir=str(tmp_path / "source-is-not-read"),
        wiki_dir=wiki,
        vault_dir=vault,
        dry_run=True,
        knowledge_metadata="summary",
        knowledge_projection=requested_projection,
    )
    assert obsidian_report.dry_run is True
    assert {operation.action for operation in obsidian_report.operations} == {
        "would_write"
    }
    planned_obsidian_pages = {
        Path(operation.path).relative_to(vault).as_posix()
        for operation in obsidian_report.operations
    }
    assert planned_obsidian_pages == {
        path for path in vault_before if path.startswith(f"{obsidian.MIRROR_ROOT}/")
    }

    site_calls: list[dict[str, object]] = []
    obsidian_calls: list[dict[str, object]] = []
    real_site_export = site_cmd.export_site_mirror
    real_obsidian_export = obsidian_cmd.export_obsidian_vault

    def observed_site_export(**kwargs):
        site_calls.append(dict(kwargs))
        return real_site_export(**kwargs)

    def observed_obsidian_export(**kwargs):
        obsidian_calls.append(dict(kwargs))
        return real_obsidian_export(**kwargs)

    monkeypatch.setattr(site_cmd, "export_site_mirror", observed_site_export)
    monkeypatch.setattr(
        obsidian_cmd,
        "export_obsidian_vault",
        observed_obsidian_export,
    )
    monkeypatch.chdir(tmp_path)

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "llm-wiki",
            "site",
            "export",
            "--wiki-dir",
            str(wiki),
            "--out-dir",
            str(site),
            "--format",
            "mkdocs",
            "--dry-run",
            "--output-format",
            "json",
            "--knowledge-metadata",
            "summary",
            "--knowledge-profile",
            knowledge_profile,
        ],
    )
    cli.main()
    site_cli_report = json.loads(capsys.readouterr().out)
    assert site_cli_report["dry_run"] is True
    assert {operation["action"] for operation in site_cli_report["operations"]} == {
        "would_write"
    }

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "llm-wiki",
            "obsidian",
            "export",
            "--src-dir",
            str(tmp_path / "source-is-not-read"),
            "--wiki-dir",
            str(wiki),
            "--vault-dir",
            str(vault),
            "--dry-run",
            "--format",
            "json",
            "--knowledge-metadata",
            "summary",
            "--knowledge-profile",
            knowledge_profile,
        ],
    )
    cli.main()
    obsidian_cli_report = json.loads(capsys.readouterr().out)
    assert obsidian_cli_report["dry_run"] is True
    assert {
        operation["action"] for operation in obsidian_cli_report["operations"]
    } == {"would_write"}

    assert len(site_calls) == 1
    assert site_calls[0]["dry_run"] is True
    assert site_calls[0]["knowledge_metadata"] == "summary"
    assert site_calls[0]["knowledge_projection"].profile.value == knowledge_profile
    assert len(obsidian_calls) == 1
    assert obsidian_calls[0]["dry_run"] is True
    assert obsidian_calls[0]["knowledge_metadata"] == "summary"
    assert (
        obsidian_calls[0]["knowledge_projection"].profile.value
        == knowledge_profile
    )

    assert _tree_bytes(site) == site_before
    assert _tree_paths(site) == site_paths_before
    assert _tree_bytes(vault) == vault_before
    assert _tree_paths(vault) == vault_paths_before
    assert human_sidecar.read_text(encoding="utf-8") == (
        "# Human-owned notes\n\nKeep this exact text.\n"
    )
    assert _tree_bytes(wiki) == native_before
    assert _tree_paths(wiki) == native_paths_before


def test_enriched_site_main_page_interruptions_preserve_or_reject_output(
    tmp_path,
    monkeypatch,
):
    wiki = _commit_governed_fixture(tmp_path)
    native_before = _tree_bytes(wiki)
    native_paths_before = _tree_paths(wiki)
    view = load_knowledge_read_view(wiki, snapshot_only=True)
    public_projection = project_knowledge(view, profile="public-portable")
    updated_public_projection = replace(
        public_projection,
        source_knowledge_hash="sha256:" + "f" * 64,
    )

    prior_site = tmp_path / "site-prior"
    mixed_site = tmp_path / "site-mixed"
    expected_updated_site = tmp_path / "site-updated"
    for target in (prior_site, mixed_site):
        site_export.export_site_mirror(
            wiki_dir=wiki,
            out_dir=target,
            format="mkdocs",
            knowledge_metadata="summary",
            knowledge_projection=public_projection,
        )
    site_export.export_site_mirror(
        wiki_dir=wiki,
        out_dir=expected_updated_site,
        format="mkdocs",
        knowledge_metadata="summary",
        knowledge_projection=updated_public_projection,
    )

    prior_before = _tree_bytes(prior_site)
    prior_paths_before = _tree_paths(prior_site)
    prior_main = prior_site / "index.md"
    real_replace = wiki_io.os.replace

    def fail_main_replace(source, destination):
        if Path(destination) == prior_main:
            raise OSError("injected Site main-page replace failure")
        return real_replace(source, destination)

    with monkeypatch.context() as publication_fault:
        publication_fault.setattr(wiki_io.os, "replace", fail_main_replace)
        with pytest.raises(OSError, match="Site main-page"):
            site_export.export_site_mirror(
                wiki_dir=wiki,
                out_dir=prior_site,
                format="mkdocs",
                knowledge_metadata="summary",
                knowledge_projection=updated_public_projection,
            )

    prior_after = _tree_bytes(prior_site)
    assert {
        path: content
        for path, content in prior_after.items()
        if path != site_export.SITE_PUBLICATION_RECEIPT
    } == {
        path: content
        for path, content in prior_before.items()
        if path != site_export.SITE_PUBLICATION_RECEIPT
    }
    assert json.loads(
        (prior_site / site_export.SITE_PUBLICATION_RECEIPT).read_text(
            encoding="utf-8"
        )
    )["state"] == "incomplete"
    assert _tree_paths(prior_site) == prior_paths_before
    assert not tuple(prior_site.rglob("*.tmp"))
    interrupted_prior_check = site_export.check_site_mirror(
        wiki_dir=wiki,
        out_dir=prior_site,
        knowledge_metadata="summary",
        knowledge_projection=public_projection,
    )
    assert interrupted_prior_check.ok is False
    assert any(
        issue["category"] == "incomplete_publication_receipt"
        for issue in interrupted_prior_check.issues
    )
    stale_prior_check = site_export.check_site_mirror(
        wiki_dir=wiki,
        out_dir=prior_site,
        knowledge_metadata="summary",
        knowledge_projection=updated_public_projection,
    )
    assert stale_prior_check.ok is False
    assert any(
        issue["category"] == "publication_projection_mismatch"
        for issue in stale_prior_check.issues
    )

    mixed_before = _tree_bytes(mixed_site)
    mixed_main = mixed_site / "index.md"
    real_site_write = site_export.write_md

    def interrupt_after_main_publication(path, content):
        real_site_write(path, content)
        if Path(path) == mixed_main:
            raise RuntimeError("injected after Site main-page publication")

    with monkeypatch.context() as sequence_fault:
        sequence_fault.setattr(
            site_export,
            "write_md",
            interrupt_after_main_publication,
        )
        with pytest.raises(RuntimeError, match="after Site main-page"):
            site_export.export_site_mirror(
                wiki_dir=wiki,
                out_dir=mixed_site,
                format="mkdocs",
                knowledge_metadata="summary",
                knowledge_projection=updated_public_projection,
            )

    mixed_after = _tree_bytes(mixed_site)
    assert mixed_after["index.md"] == _tree_bytes(expected_updated_site)["index.md"]
    assert {
        path: content
        for path, content in mixed_after.items()
        if path not in {"index.md", site_export.SITE_PUBLICATION_RECEIPT}
    } == {
        path: content
        for path, content in mixed_before.items()
        if path not in {"index.md", site_export.SITE_PUBLICATION_RECEIPT}
    }
    assert json.loads(
        (mixed_site / site_export.SITE_PUBLICATION_RECEIPT).read_text(
            encoding="utf-8"
        )
    )["state"] == "incomplete"
    assert not tuple(mixed_site.rglob("*.tmp"))
    for projection in (public_projection, updated_public_projection):
        checked = site_export.check_site_mirror(
            wiki_dir=wiki,
            out_dir=mixed_site,
            knowledge_metadata="summary",
            knowledge_projection=projection,
        )
        assert checked.ok is False
        assert any(
            issue["category"] == "incomplete_publication_receipt"
            for issue in checked.issues
        )

    assert _tree_bytes(wiki) == native_before
    assert _tree_paths(wiki) == native_paths_before


def test_enriched_obsidian_main_page_interruptions_preserve_sidecars_or_reject(
    tmp_path,
    monkeypatch,
):
    wiki = _commit_governed_fixture(tmp_path)
    native_before = _tree_bytes(wiki)
    native_paths_before = _tree_paths(wiki)
    view = load_knowledge_read_view(wiki, snapshot_only=True)
    public_projection = project_knowledge(view, profile="public-portable")
    internal_projection = project_knowledge(view, profile="internal")

    prior_vault = tmp_path / "vault-prior"
    mixed_vault = tmp_path / "vault-mixed"
    expected_internal_vault = tmp_path / "vault-internal"
    for target in (prior_vault, mixed_vault):
        obsidian.export_obsidian_vault(
            src_dir=str(tmp_path / "source-is-not-read"),
            wiki_dir=wiki,
            vault_dir=target,
            knowledge_metadata="summary",
            knowledge_projection=public_projection,
        )
    obsidian.export_obsidian_vault(
        src_dir=str(tmp_path / "source-is-not-read"),
        wiki_dir=wiki,
        vault_dir=expected_internal_vault,
        knowledge_metadata="summary",
        knowledge_projection=internal_projection,
    )

    for vault, marker in (
        (prior_vault, "prior"),
        (mixed_vault, "mixed"),
    ):
        (
            vault
            / ".llm-wiki"
            / "obsidian-notes"
            / "entity"
            / "User.md"
        ).write_text(
            f"# Human-owned {marker} notes\n\nKeep this exact text.\n",
            encoding="utf-8",
        )

    prior_before = _tree_bytes(prior_vault)
    prior_paths_before = _tree_paths(prior_vault)
    prior_notes_before = _tree_bytes(
        prior_vault / ".llm-wiki" / "obsidian-notes"
    )
    prior_main = prior_vault / obsidian.MIRROR_ROOT / "Index.md"
    real_replace = wiki_io.os.replace

    def fail_main_replace(source, destination):
        if Path(destination) == prior_main:
            raise OSError("injected Obsidian main-page replace failure")
        return real_replace(source, destination)

    with monkeypatch.context() as publication_fault:
        publication_fault.setattr(wiki_io.os, "replace", fail_main_replace)
        with pytest.raises(OSError, match="Obsidian main-page"):
            obsidian.export_obsidian_vault(
                src_dir=str(tmp_path / "source-is-not-read"),
                wiki_dir=wiki,
                vault_dir=prior_vault,
                knowledge_metadata="summary",
                knowledge_projection=internal_projection,
            )

    assert _tree_bytes(prior_vault) == prior_before
    assert _tree_paths(prior_vault) == prior_paths_before
    assert _tree_bytes(
        prior_vault / ".llm-wiki" / "obsidian-notes"
    ) == prior_notes_before
    assert not tuple(prior_vault.rglob("*.tmp"))
    assert obsidian.check_obsidian_vault(
        wiki_dir=wiki,
        vault_dir=prior_vault,
        knowledge_metadata="summary",
        knowledge_projection=public_projection,
    ).ok
    stale_prior_check = obsidian.check_obsidian_vault(
        wiki_dir=wiki,
        vault_dir=prior_vault,
        knowledge_metadata="summary",
        knowledge_projection=internal_projection,
    )
    assert stale_prior_check.ok is False
    assert any(
        issue["category"] == "knowledge_metadata_mismatch"
        for issue in stale_prior_check.issues
    )

    mixed_before = _tree_bytes(mixed_vault)
    mixed_notes_before = _tree_bytes(
        mixed_vault / ".llm-wiki" / "obsidian-notes"
    )
    mixed_main = mixed_vault / obsidian.MIRROR_ROOT / "Index.md"
    real_obsidian_write = obsidian.write_md

    def interrupt_after_main_publication(path, content):
        real_obsidian_write(path, content)
        if Path(path) == mixed_main:
            raise RuntimeError("injected after Obsidian main-page publication")

    with monkeypatch.context() as sequence_fault:
        sequence_fault.setattr(
            obsidian,
            "write_md",
            interrupt_after_main_publication,
        )
        with pytest.raises(RuntimeError, match="after Obsidian main-page"):
            obsidian.export_obsidian_vault(
                src_dir=str(tmp_path / "source-is-not-read"),
                wiki_dir=wiki,
                vault_dir=mixed_vault,
                knowledge_metadata="summary",
                knowledge_projection=internal_projection,
            )

    mixed_after = _tree_bytes(mixed_vault)
    main_relative = f"{obsidian.MIRROR_ROOT}/Index.md"
    assert mixed_after[main_relative] == _tree_bytes(expected_internal_vault)[
        main_relative
    ]
    assert {
        path: content for path, content in mixed_after.items() if path != main_relative
    } == {
        path: content for path, content in mixed_before.items() if path != main_relative
    }
    assert _tree_bytes(
        mixed_vault / ".llm-wiki" / "obsidian-notes"
    ) == mixed_notes_before
    assert not tuple(mixed_vault.rglob("*.tmp"))
    for projection in (public_projection, internal_projection):
        checked = obsidian.check_obsidian_vault(
            wiki_dir=wiki,
            vault_dir=mixed_vault,
            knowledge_metadata="summary",
            knowledge_projection=projection,
        )
        assert checked.ok is False
        assert any(
            issue["category"] == "knowledge_metadata_mismatch"
            for issue in checked.issues
        )

    assert _tree_bytes(wiki) == native_before
    assert _tree_paths(wiki) == native_paths_before
