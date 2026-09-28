"""Equivalence and freshness controls for documentation scan acceleration."""

import os
import unicodedata

import pytest

from tests import test_public_docs_vocabulary as docs


def test_invisible_filter_matches_original_policy_for_every_unicode_codepoint():
    ignored = {
        point
        for start, end in docs._DEFAULT_IGNORABLE_RANGES
        for point in range(start, end + 1)
    }
    # Bound working memory while checking every codepoint, including surrogates.
    for start in range(0, 0x110000, 4096):
        text = "".join(
            chr(point) for point in range(start, min(start + 4096, 0x110000))
        )
        expected = "".join(
            c for c in text if unicodedata.category(c) != "Cf" and ord(c) not in ignored
        )
        assert docs._without_invisible_formatting(text) == expected


@pytest.mark.parametrize(
    "files",
    [
        {"README.md", "docs/guide.md", "docs/nested/page.md", "unicodé/guide.md"},
        {
            "docs//guide.md",
            "./docs/file.md",
            "/absolute/file.md",
            "back\\slash/file.md",
        },
        set(),
    ],
)
def test_directory_index_matches_the_original_lexical_prefix_rule(files):
    inventory = docs.DocumentationInventory.capture(files)
    for destination in [
        ".",
        "..",
        "docs",
        "docs/",
        "docs/nested",
        "docs/../docs",
        "unicodé/",
        "missing/",
        "README.md/",
        "/absolute/",
        "back%5Cslash",
    ]:
        local = docs._normalize_local_destination("README.md", destination)
        assert local is not None
        original = local.path == "." or any(
            path.startswith(local.path.rstrip("/") + "/") for path in files
        )
        assert (local.path in inventory.directories) == original


def test_link_target_existence_is_never_cached(tmp_path):
    target = tmp_path / "reference.md"
    target.write_text("# Reference\n")
    inventory = docs.DocumentationInventory.capture(["README.md", "reference.md"])

    def scan():
        return docs.scan_markdown_links(
            "[reference](reference.md#section)",
            path="README.md",
            tracked_files=inventory,
            root=tmp_path,
        )

    assert scan() == []
    target.unlink()
    assert [f.rule for f in scan()] == ["missing-or-untracked-local-link"]
    target.write_text("# Other section\n")
    assert scan() == []


def test_link_target_type_is_rechecked_with_the_same_inventory(tmp_path):
    target = tmp_path / "reference"
    target.mkdir()
    inventory = docs.DocumentationInventory.capture(["README.md", "reference/page.md"])

    def scan():
        return docs.scan_markdown_links(
            "[reference](reference/)",
            path="README.md",
            tracked_files=inventory,
            root=tmp_path,
        )

    assert scan() == []
    target.rmdir()
    target.write_text("regular file")
    assert [f.rule for f in scan()] == ["missing-or-untracked-local-link"]


def test_changed_caller_inventory_is_not_reused():
    files = {"README.md"}
    kwargs = {"path": "README.md", "tracked_files": files}
    text = "[new](docs/new.md#fragment)"
    assert docs.scan_markdown_links(text, **kwargs)
    files.add("docs/new.md")
    assert docs.scan_markdown_links(text, **kwargs) == []
    files.remove("docs/new.md")
    assert docs.scan_markdown_links(text, **kwargs)


def test_full_scan_includes_added_docs_and_same_mtime_content(tmp_path, monkeypatch):
    readme = tmp_path / "README.md"
    readme.write_text("# Guide\n", encoding="utf-8")
    tracked = ["README.md"]
    monkeypatch.setattr(docs, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(docs, "_tracked_files", lambda: tuple(tracked))
    docs.test_tracked_public_documentation_has_no_internal_vocabulary_or_dead_links()
    new = tmp_path / "docs" / "new.md"
    new.parent.mkdir()
    new.write_text("[broken](missing.md#changed)\n", encoding="utf-8")
    tracked.append("docs/new.md")
    with pytest.raises(AssertionError, match="docs/new.md"):
        docs.test_tracked_public_documentation_has_no_internal_vocabulary_or_dead_links()
    new.write_text("# Reference\n", encoding="utf-8")
    before = readme.stat()
    readme.write_text(docs._STAGE_MARKER + "\n", encoding="utf-8")
    os.utime(readme, ns=(before.st_atime_ns, before.st_mtime_ns))
    with pytest.raises(AssertionError, match="delivery-stage-label"):
        docs.test_tracked_public_documentation_has_no_internal_vocabulary_or_dead_links()


@pytest.mark.parametrize(
    "destination",
    [
        "missing.md#first",
        "missing.md#second",
        "missing.md?query#third",
        "missing%23name.md#fourth",
    ],
)
def test_fragments_never_hide_a_broken_target(destination):
    result = docs.scan_markdown_links(
        f"[link]({destination})", path="README.md", tracked_files={"README.md"}
    )
    assert [finding.rule for finding in result] == ["missing-or-untracked-local-link"]


def test_source_selection_and_decoding_are_preserved():
    paths = {
        "docs/llm_wiki/concepts/generated.md",
        "examples/guide.md",
        "README.md",
        "src/llm_wiki_cli/skills/guide/SKILL.md",
        "reports/private.md",
    }
    inventory = docs.DocumentationInventory.capture(paths)
    assert docs.public_documentation_files(
        inventory
    ) == docs.public_documentation_files(paths)
    assert "docs/llm_wiki/concepts/generated.md" in docs.public_documentation_files(
        inventory
    )
    assert "reports/private.md" not in docs.public_documentation_files(inventory)
    with pytest.raises(AssertionError, match="UTF-8"):
        docs._decode_public_text("docs/guide.md", b"\xff")
    assert docs._decode_public_text("examples/image.bin", b"\xff") is None
