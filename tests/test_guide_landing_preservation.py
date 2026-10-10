"""Advisory landing signals follow the existing owning index splice."""

from pathlib import Path
import subprocess
import sys

import pytest

from llm_wiki_cli import api, cli
from llm_wiki_cli.services.documentation_worklist import build_documentation_worklist
from llm_wiki_cli.services.markdown_sections import GENERATED_INDEX_INTROS


PURPOSE = (
    "This project gathers qualified source declarations and authored documentation for coding tasks. "
    "The host still verifies behavior and decides what to edit. A direct source read can be simpler "
    "for a small isolated change."
)
NAV = "## Start Here\n\n- [Orient yourself](guides/orientation.md).\n"


def has_landing(wiki):
    return any(item.category == "landing_context" for item in build_documentation_worklist(wiki).items)


def sync(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["llm-wiki", "sync", "--src-dir", "src", "--wiki-dir", "wiki", "--jobs", "1"])
    cli.main()


def test_real_owning_sync_keeps_purpose_in_notes_and_clears_only_landing_signal(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    Path("src").mkdir()
    Path("src/app.py").write_text("def limit(value=3):\n    return value\n")
    api.bootstrap_wiki("src", "wiki")
    wiki = Path("wiki")
    assert has_landing(wiki)
    (wiki / "guides/orientation.md").write_text("# Orientation\n\nRead the exact source and its limits.\n")
    index = wiki / "index.md"
    generated = index.read_text()
    intro = next(value for value in GENERATED_INDEX_INTROS if value in generated)
    index.write_text(generated.replace(intro, PURPOSE, 1) + "\n" + NAV)
    sync(monkeypatch)
    anchored = index.read_text()
    assert anchored.count(PURPOSE) == 1
    assert "## Notes\n\n" + PURPOSE in anchored
    assert NAV.strip() in anchored
    assert not has_landing(wiki)
    assert any(item.priority == "P2" for item in build_documentation_worklist(wiki, p1_budget=0).items)
    sync(monkeypatch)
    assert index.read_text().count(PURPOSE) == 1
    assert not has_landing(wiki)


@pytest.mark.parametrize("custom", [
    NAV,
    "## Notes\n\n—\n\n" + NAV,
    "```markdown\n## Notes\n\n" + PURPOSE + "\n```\n\n" + NAV,
    "## Notes\n\n```text\n" + PURPOSE + "\n```\n\n" + NAV,
    "## Notes\n\nShort purpose. <!-- " + "hidden " * 25 + "-->\n\n" + NAV,
    "## Notes\n\n    " + PURPOSE + "\n\n" + NAV,
    "## Notes\n\n" + PURPOSE + "\n\n## Start Here\n\n`[Fake guide](guides/orientation.md)`\n",
    "## Notes\n\n" + (sorted(GENERATED_INDEX_INTROS)[0] + "\n\n") * 3 + NAV,
    "## Notes\n\n" + ("**" + sorted(GENERATED_INDEX_INTROS)[0].upper() + "** ") * 20 + "\n\n" + NAV,
    "## Notes\n\n" + "Replace this placeholder with authored purpose and examples. " * 8 + "\n\n" + NAV,
    "## Notes\n\n" + PURPOSE + "\n\n## Start Here\n\n[Wrong](guides/../modules/cli.md)\n",
    "## Notes\n\n" + PURPOSE + "\n\n## Start Here\n\n[Wrong](guides/fixture.py)\n",
    "## Notes\n\n" + PURPOSE + "\n\n## Start Here\n\n[Wrong](guides/%2e%2e/modules/cli.md)\n",
    "## Notes\n\n" + PURPOSE + "\n\n## Notes\n\nAmbiguous.\n\n" + NAV,
    "## Notes\n\n" + PURPOSE + "\n\n## Start Here\n\n- [Inventory](#modules).\n",
])
def test_placeholder_code_only_ambiguous_or_inventory_only_landing_stays_pending(tmp_path, custom):
    wiki = tmp_path / "wiki"
    wiki.mkdir()
    (wiki / "index.md").write_text("# LLM Wiki Index\n\n" + sorted(GENERATED_INDEX_INTROS)[0] + "\n\n" + custom)
    assert has_landing(wiki)


def test_core_import_and_landing_signal_need_no_development_markdown_parser(tmp_path):
    source = Path(__file__).resolve().parents[1] / "src"
    script = f"""
import sys
sys.path.insert(0, {str(source)!r})
class BlockDevelopmentParser:
    def find_spec(self, fullname, path=None, target=None):
        if fullname == 'markdown_it' or fullname.startswith('markdown_it.'):
            raise ModuleNotFoundError('development-only parser unavailable')
sys.meta_path.insert(0, BlockDevelopmentParser())
from llm_wiki_cli import api
from llm_wiki_cli.services.documentation_worklist import _index_needs_context
text = '# LLM Wiki Index\\n\\nGuides lead supported tasks. The generated indexes are exhaustive reference inventories of the selected source.\\n\\n## Notes\\n\\n' + {PURPOSE!r} + '\\n\\n' + {NAV!r}
assert not _index_needs_context(text)
"""
    completed = subprocess.run([sys.executable, "-I", "-c", script], cwd=tmp_path,
                               capture_output=True, text=True, check=False)
    assert completed.returncode == 0, completed.stderr
