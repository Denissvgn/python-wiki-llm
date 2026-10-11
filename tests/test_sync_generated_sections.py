"""Owning generated repairs retain source and authored data or fail before writes."""

from pathlib import Path
from types import SimpleNamespace as NS
from unittest.mock import patch

import pytest

from llm_wiki_cli.commands import bootstrap_cmd, sync_cmd
from llm_wiki_cli.services.markdown_sections import section_body
from llm_wiki_cli.services.sync_manifest import SyncManifest
from llm_wiki_cli.services.knowledge_loader import load_knowledge_state
from llm_wiki_cli.services.lint_service import build_report

SOURCE = """import math

class Item:
    count: int = 1
    def compute(self, value: int = 3) -> int:
        return self.count + value

def compute(value: int = 3) -> int:
    return value + 1
"""


def sync(**kwargs):
    return sync_cmd.run(
        NS(src_dir="src", wiki_dir="wiki", no_plugins=True, cache_dir="cache", **kwargs)
    )


@pytest.fixture(params=("v1", "packed-v4-deflate"))
def project(tmp_path, monkeypatch, request):
    monkeypatch.chdir(tmp_path)
    Path("src").mkdir()
    Path("src/app.py").write_text(SOURCE)
    Path("src/keeper.py").write_text("class Keeper:\n    pass\n")
    bootstrap_cmd.run(
        NS(
            src_dir="src",
            wiki_dir="wiki",
            depth="full",
            overwrite=False,
            source_adapter=True,
            knowledge_format=request.param,
        )
    )
    # Establish the native history/cache with actual authored prose.
    p = Path("wiki/modules/app.md")
    p.write_text(
        p.read_text().replace(
            "_Auto-generated from `app.py`._", "AUTHORED module description."
        )
        + "\n\n## Operator notes\n\nAUTHORED custom section.\n"
    )
    sync()
    return tmp_path


def snapshots():
    return {
        p: (p.read_bytes(), p.stat().st_mtime_ns)
        for p in Path("wiki").rglob("*")
        if p.is_file()
    }


@pytest.mark.parametrize(
    "path,heading,change",
    [
        ("modules/app.md", "Functions", "name"),
        ("modules/app.md", "Functions", "signature"),
        ("modules/app.md", "Classes", "name"),
        ("entities/Item.md", "Methods", "signature"),
        ("entities/Item.md", "Attributes", "type"),
        ("modules/app.md", "Functions", "missing"),
        ("entities/Item.md", "Methods", "missing"),
        ("modules/app.md", "Imports", "missing"),
    ],
)
def test_repairs_current_source_projection_and_preserves_other_content(
    project, path, heading, change
):
    page = Path("wiki") / path
    original = page.read_text()
    expected = section_body(original, heading)
    assert expected is not None
    if change == "name":
        damaged = (
            original.replace("| `compute` |", "| `invented` |")
            if heading == "Functions"
            else original.replace(
                "[Item](../entities/Item.md)", "[Invented](../entities/Item.md)"
            )
        )
    elif change == "signature":
        damaged = original.replace("value: int = 3", "value: str = 99")
    elif change == "type":
        damaged = original.replace("`int`", "`str`")
    else:
        from llm_wiki_cli.services.markdown_sections import parse_markdown_document

        section = next(
            s
            for s in parse_markdown_document(original, "llm-wiki://test").sections
            if s.level == 2 and s.title == heading
        )
        damaged = original[: section.start] + original[section.end :]
    assert damaged != original
    page.write_text(damaged)
    source = Path("src/app.py").read_bytes()
    old_hash = SyncManifest.load(Path("wiki")).sources["app.py"]["hash"]
    keeper = {
        p: (p.read_bytes(), p.stat().st_mtime_ns)
        for p in [Path("wiki/modules/keeper.md"), Path("wiki/entities/Keeper.md")]
    }
    sync()
    restored = section_body(page.read_text(), heading)
    assert restored is not None
    assert restored.strip() == expected.strip()
    if path.startswith("modules"):
        assert "AUTHORED module description." in page.read_text()
        assert "AUTHORED custom section." in page.read_text()
    assert Path("src/app.py").read_bytes() == source
    assert SyncManifest.load(Path("wiki")).sources["app.py"]["hash"] == old_hash
    assert all((p.read_bytes(), p.stat().st_mtime_ns) == v for p, v in keeper.items())
    assert build_report("wiki", "src", strict=True).passed
    stable = snapshots()
    sync()
    assert snapshots() == stable


def test_signature_repair_keeps_authored_table_cell_and_notes(project):
    page = Path("wiki/entities/Item.md")
    page.write_text(
        page.read_text()
        .replace("| — |\n", "| AUTHORED method rationale. |\n")
        .replace("value: int = 3", "value: str = 99")
        + "\n\n## Notes\n\nAUTHORED entity note.\n"
    )
    sync()
    assert "value: int = 3" in page.read_text()
    assert "AUTHORED method rationale." in page.read_text()
    assert "AUTHORED entity note." in page.read_text()


@pytest.mark.parametrize("case", ["orphan", "duplicate", "heading"])
def test_ambiguous_semantics_fail_before_any_wiki_write(project, case):
    page = Path("wiki/modules/app.md")
    text = page.read_text()
    line = next(row for row in text.splitlines() if row.startswith("| `compute` |"))
    authored = line.replace("— |", "AUTHORED cell. |")
    if case == "orphan":
        text = text.replace(line, authored.replace("`compute`", "`invented`"))
    elif case == "duplicate":
        text = text.replace(line, authored + "\n" + authored)
    else:
        text = (
            text.replace("value: int = 3", "value: str = 99")
            + "\n\n## Functions\n\nAUTHORED repeated heading.\n"
        )
    page.write_text(text)
    before = snapshots()
    with pytest.raises(SystemExit) as error:
        sync()
    assert error.value.code == 2
    assert snapshots() == before


def test_dry_run_and_failed_finalization_keep_recovery_contract(project, monkeypatch):
    page = Path("wiki/modules/app.md")
    page.write_text(page.read_text().replace("`compute`", "`invented`"))
    before = snapshots()
    sync(dry_run=True)
    assert snapshots() == before
    marker = Path("wiki/.llm-wiki-manifest.json").read_bytes()
    with monkeypatch.context() as m:
        m.setattr(
            sync_cmd,
            "finalize_runtime_knowledge",
            lambda *a, **kw: (_ for _ in ()).throw(RuntimeError("interrupted")),
        )
        with pytest.raises(RuntimeError, match="interrupted"):
            sync()
    assert Path("wiki/.llm-wiki-manifest.json").read_bytes() == marker
    from tests.test_sync_transition_execution import _assert_originals

    recovery, _ = _assert_originals(
        Path("wiki"), {str(p.relative_to("wiki")): value for p, value in before.items()}
    )
    after = snapshots()
    with pytest.raises(SystemExit):
        sync()
    assert snapshots() == after
    # Resolve this fixture's retained recovery only after checking its exact
    # originals, mirroring the existing explicit recovery contract.
    page.write_bytes(before[page][0])
    import shutil

    shutil.rmtree(recovery)
    sync()
    assert "| `compute` |" in page.read_text()
    assert "AUTHORED module description." in page.read_text()
    assert load_knowledge_state("wiki").knowledge is not None
    assert build_report("wiki", "src", strict=True).passed


def test_repair_does_not_trust_previously_committed_drift(project):
    page = Path("wiki/modules/app.md")
    page.write_text(page.read_text().replace("| `compute` |", "| `invented` |"))
    # Reproduce the predecessor's valid but stale generated projection through
    # ordinary native publication, without editing machine artifacts.
    with patch.object(
        sync_cmd,
        "plan_generated_source_repairs",
        lambda root, plan, *a, **kw: (plan, {}),
    ):
        sync()
    assert "| `invented` |" in page.read_text()
    sync()
    assert "| `compute` |" in page.read_text()
    assert "AUTHORED custom section." in page.read_text()


def test_semantic_cell_only_edit_keeps_the_canonical_page_bytes(project):
    page = Path("wiki/modules/app.md")
    text = page.read_text().replace("| `compute` |", "| `compute` |")
    lines = text.splitlines()
    index = next(i for i, row in enumerate(lines) if row.startswith("| `compute` |"))
    lines[index] = lines[index].rsplit("—", 1)[0] + "AUTHORED cell. |"
    page.write_text("\n".join(lines))
    before = page.read_bytes(), page.stat().st_mtime_ns
    sync()
    assert (page.read_bytes(), page.stat().st_mtime_ns) == before


def test_post_plan_page_mutation_cannot_publish_a_repair(project, monkeypatch):
    page = Path("wiki/modules/app.md")
    page.write_text(page.read_text().replace("| `compute` |", "| `invented` |"))
    marker = Path("wiki/.llm-wiki-manifest.json").read_bytes()
    original = sync_cmd._apply_prepared_sync

    def raced(*args):
        page.write_text(page.read_text() + "\nConcurrent authored change.\n")
        return original(*args)

    monkeypatch.setattr(sync_cmd, "_apply_prepared_sync", raced)
    with pytest.raises((SystemExit, ValueError)):
        sync()
    assert Path("wiki/.llm-wiki-manifest.json").read_bytes() == marker
    assert "| `invented` |" in page.read_text()
    assert "Concurrent authored change." in page.read_text()


def test_unowned_and_excluded_page_is_not_repaired(project):
    page = Path("wiki/modules/unowned.md")
    text = "# Unowned\n\n## Functions\n\n| Function | Signature | Description |\n|---|---|---|\n| `invented` | `()` | AUTHORED |\n"
    page.write_text(text)
    target = Path("wiki/modules/app.md")
    target.write_text(target.read_text().replace("| `compute` |", "| `invented` |"))
    sync()
    assert page.read_text() == text
    assert "| `compute` |" in target.read_text()
