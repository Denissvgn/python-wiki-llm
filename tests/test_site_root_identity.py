"""Trusted output-root aliases retain publication identity and containment."""

from dataclasses import replace
import json
from pathlib import Path
import subprocess
import sys

import pytest

from llm_wiki_cli.services import site_export


def _wiki(root: Path) -> Path:
    wiki = root / "wiki"
    (wiki / "guides").mkdir(parents=True)
    (wiki / "index.md").write_text("# Docs\n\n[Intro](guides/intro.md)\n")
    (wiki / "guides" / "intro.md").write_text("# Intro\n\n[Home](../index.md)\n")
    return wiki


def _aliased_output(root: Path, kind: str) -> Path:
    if kind == "host" and str(root).startswith("/private/var/"):
        alias = Path("/var") / root.relative_to("/private/var")
        if alias.resolve() == root:
            return alias / "site"
    # The portable spelling also reproduces the lexical/resolved mismatch.
    parent = root / "parent"
    parent.mkdir()
    return parent / ".." / "site"


@pytest.mark.parametrize("kind", ["parent", "host"])
@pytest.mark.parametrize("format", ["plain", "mkdocs", "docusaurus"])
def test_publication_root_alias_preserves_commitments(tmp_path, kind, format):
    root = tmp_path.resolve()
    wiki = _wiki(root)
    out = _aliased_output(root, kind)

    first = site_export.export_site_mirror(wiki_dir=wiki, out_dir=out, format=format)
    assert first.ok
    receipt_path = out / site_export.SITE_PUBLICATION_RECEIPT
    receipt = receipt_path.read_bytes()
    assert site_export.check_site_mirror(wiki_dir=wiki, out_dir=out, format=format).ok
    assert site_export.check_site_mirror(wiki_dir=wiki, out_dir=out.resolve(), format=format).ok
    second = site_export.export_site_mirror(wiki_dir=wiki, out_dir=out.resolve(), format=format)
    assert first.export_id == second.export_id
    assert receipt_path.read_bytes() == receipt
    assert all(".." not in item["path"].split("/") for item in json.loads(receipt)["commitments"])


@pytest.mark.parametrize("kind", ["parent", "host"])
def test_site_cli_accepts_trusted_output_root_alias(tmp_path, kind):
    root = tmp_path.resolve()
    wiki = _wiki(root)
    out = _aliased_output(root, kind)
    for action in ("export", "check"):
        result = subprocess.run(
            [sys.executable, "-m", "llm_wiki_cli.cli", "site", action,
             "--wiki-dir", str(wiki), "--out-dir", str(out),
             "--format", "plain", "--output-format", "json"],
            cwd=root, capture_output=True, text=True, check=True, timeout=30,
        )
        assert json.loads(result.stdout)["ok"] is True


def test_aliased_root_still_rejects_outside_publication_commitment(tmp_path):
    root = tmp_path.resolve()
    wiki = _wiki(root)
    out = _aliased_output(root, "parent")
    report = site_export.export_site_mirror(wiki_dir=wiki, out_dir=out)
    outside = root / "outside.md"
    outside.write_text("# Unowned\n")
    report.operations.append(replace(report.operations[0], path=str(outside)))
    with pytest.raises(site_export.SiteExportError, match="escapes output directory"):
        site_export._publication_commitments(report, out=out)
