"""Dogfood invariants for generated entity relationship reference tables."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ENTITIES = ROOT / "docs" / "llm_wiki" / "entities"


def _reference_rows(path: Path) -> list[tuple[str, str, str, str]]:
    content = path.read_text(encoding="utf-8")
    if "### References" not in content:
        return []
    section = content.split("### References", 1)[1]
    rows: list[tuple[str, str, str, str]] = []
    for line in section.splitlines():
        if not line.startswith("|"):
            if rows:
                break
            continue
        cells = tuple(cell.strip() for cell in line.strip("|").split("|"))
        if cells[0] in {"Reference", "---"}:
            continue
        assert len(cells) == 4, f"unexpected References table row in {path}: {line}"
        rows.append(cells)
    return rows


def test_generated_entity_reference_tables_have_no_duplicate_call_rows() -> None:
    duplicates: list[str] = []
    for path in sorted(ENTITIES.rglob("*.md")):
        seen: set[tuple[str, str, str]] = set()
        for reference, kind, source, _call_sites in _reference_rows(path):
            if kind != "call":
                continue
            key = (reference, kind, source)
            if key in seen:
                duplicates.append(f"{path.relative_to(ROOT)}: {key}")
            seen.add(key)

    assert duplicates == []


def test_agent_config_inspection_dogfood_has_complete_logical_references() -> None:
    rows = _reference_rows(ENTITIES / "AgentConfigInspection.md")

    assert len(rows) == 10
    assert (
        "`inspect_config_path`",
        "call",
        "[config](../modules/config.md)",
        "10",
    ) in rows
    assert (
        "`inspect_config`",
        "call",
        "[config](../modules/config.md)",
        "1",
    ) in rows
    assert (
        "`inspect_config`",
        "type_reference",
        "[config](../modules/config.md)",
        "—",
    ) in rows
    assert (
        "`inspect_config_path`",
        "type_reference",
        "[config](../modules/config.md)",
        "—",
    ) in rows
    assert (
        "`require_config_inspection_unchanged`",
        "type_reference",
        "[config](../modules/config.md)",
        "—",
    ) in rows
