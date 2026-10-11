"""Source-grounded repairs of retained entity/module generated sections."""

from __future__ import annotations

from collections import Counter
from dataclasses import replace
from pathlib import Path
from typing import Mapping

from .bootstrap_runtime import _generate_entity_md, _generate_module_md
from .knowledge_storage import MAX_EXPANDED_BYTES, KnowledgeStorageError
from .knowledge_storage_io import StorageReadSession
from .markdown_sections import (
    description_table_cells,
    is_placeholder_description,
    mixed_table_projection,
    normalize_markdown,
    parse_markdown_document,
    preserve_table_description_cells,
)
from .section_ownership import observe_page_sections, SectionOwnership
from .sync_manifest import ManifestPageSource
from .sync_transitions import (
    PageTransitionError,
    PageTransitionPlan,
    RetainedPageRepair,
)
from .wiki_surface import PageKind


# These projections require live graph context, not merely source declarations.
_GRAPH_HEADINGS = {"relationships", "local dependency map"}


def _sections(markdown, kind):
    document = parse_markdown_document(
        normalize_markdown(markdown), "llm-wiki://repair"
    )
    ownership = {
        s.locator: s
        for s in observe_page_sections(markdown, document.page_locator, kind).sections
    }
    return document, {
        s.title.casefold(): (s, ownership[s.locator].ownership)
        for s in document.sections
        if s.level == 2
        and ownership[s.locator].ownership
        in {
            SectionOwnership.GENERATED,
            SectionOwnership.MIXED,
        }
        and s.title.casefold() not in _GRAPH_HEADINGS
    }


def _structural(section, ownership):
    text = section.exact_text.rstrip() + "\n"
    return (
        mixed_table_projection(text).structural_hash
        if ownership is SectionOwnership.MIXED
        else text
    )


def _preserve_cells(current, generated, path):
    """Reject ambiguous attribution instead of using last-duplicate-wins."""
    existing = description_table_cells(current.exact_text)
    expected = description_table_cells(generated.exact_text)
    existing_counts = Counter(c.key for c in existing)
    expected_counts = Counter(c.key for c in expected)
    descriptions = {}
    for cell in existing:
        if is_placeholder_description(cell.description):
            continue
        if existing_counts[cell.key] != 1 or expected_counts[cell.key] != 1:
            raise PageTransitionError(
                f"Generated section drift at {path!r}/{current.title}: "
                f"ambiguous Description cell for {cell.key!r}; preserve it before repairing identity"
            )
        descriptions[cell.key] = cell.description
    if not existing and "|" in current.body and expected:
        raise PageTransitionError(
            f"Generated section drift at {path!r}/{current.title}: unsupported Description table structure"
        )
    # With unchanged source, each uniquely attributed non-placeholder cell is
    # retained verbatim, including values equal to the generated default.
    repaired, _ = preserve_table_description_cells(
        generated.exact_text,
        generated.title,
        descriptions,
        should_preserve=lambda *args: True,
    )
    return repaired


def repair_source_sections(
    existing: str, generated: str, kind: PageKind, path: str
) -> str:
    """Replace only source-derived generated projections, retaining other text."""
    normalized = normalize_markdown(existing)
    document, current = _sections(normalized, kind)
    _, expected = _sections(generated, kind)
    counts = Counter(s.title.casefold() for s in document.sections if s.level == 2)
    replacements = []
    missing = []
    for title, (target, ownership) in expected.items():
        found = current.get(title)
        if found is not None and _structural(found[0], found[1]) == _structural(
            target, ownership
        ):
            continue
        if counts[title] > 1:
            raise PageTransitionError(
                f"Generated section drift at {path!r}: ambiguous repeated heading {target.title!r}"
            )
        if found is None:
            if counts[title]:
                raise PageTransitionError(
                    f"Generated section drift at {path!r}: unknown ownership for {target.title!r}"
                )
            missing.append(target.exact_text.rstrip())
            continue
        section = found[0]
        replacement = (
            _preserve_cells(section, target, path)
            if ownership is SectionOwnership.MIXED
            else target.exact_text
        )
        padding = section.exact_text[len(section.exact_text.rstrip()) :]
        replacements.append(
            (section.start, section.end, replacement.rstrip() + padding)
        )
    for title, (section, ownership) in current.items():
        if title in expected:
            continue
        if counts[title] > 1 or (
            ownership is SectionOwnership.MIXED
            and any(
                not is_placeholder_description(cell.description)
                for cell in description_table_cells(section.exact_text)
            )
        ):
            raise PageTransitionError(
                f"Generated section drift at {path!r}: cannot attribute retained content in {section.title!r}"
            )
        replacements.append((section.start, section.end, ""))
    if not replacements and not missing:
        return existing
    for start, end, text in sorted(replacements, reverse=True):
        normalized = normalized[:start] + text + normalized[end:]
    if missing:
        normalized = normalized.rstrip() + "\n\n" + "\n\n".join(missing) + "\n"
    return normalized


def _source_markdown(
    owner, inventory, module_pages, entity_pages, module_renderer, entity_renderer
):
    data = inventory[owner.source_path]
    if owner.scope == "module":
        entity_names = {}
        for (name, source, _occurrence), page in sorted(entity_pages.items()):
            if source == owner.source_path:
                entity_names.setdefault(name, page)
        return module_renderer(
            owner.source_path,
            data,
            entity_names,
            module_page_map=module_pages,
            entity_occurrence_page_map=entity_pages,
        )
    matches = [c for c in data.get("classes", []) if c["name"] == owner.entity_name]
    if not owner.occurrence or owner.occurrence > len(matches):
        raise PageTransitionError(f"Cannot attribute generated repair to {owner!r}")
    return entity_renderer(
        matches[owner.occurrence - 1],
        owner.source_path,
        {},
        module_pages[owner.source_path],
        module_page_map=module_pages,
    )


def plan_generated_source_repairs(
    wiki_dir: Path,
    plan: PageTransitionPlan,
    inventory: Mapping,
    module_pages: Mapping,
    entity_pages: Mapping,
    *,
    module_renderer=_generate_module_md,
    entity_renderer=_generate_entity_md,
) -> tuple[PageTransitionPlan, dict[str, ManifestPageSource]]:
    """Preflight all retained owners and semantic attribution before any write."""
    repairs = []
    owners = {}
    reader = StorageReadSession(wiki_dir)
    try:
        with reader.phase():
            for item in plan.transitions:
                if item.action != "retain" or item.owner != item.previous_owner:
                    continue
                raw = reader.read(item.final_path, MAX_EXPANDED_BYTES)
                text = raw.decode("utf-8")
                generated = _source_markdown(
                    item.owner,
                    inventory,
                    module_pages,
                    entity_pages,
                    module_renderer,
                    entity_renderer,
                )
                kind = (
                    PageKind.MODULES
                    if item.owner.scope == "module"
                    else PageKind.ENTITIES
                )
                repaired = repair_source_sections(
                    text, generated, kind, item.final_path
                )
                if repaired == text:
                    continue
                owners[item.final_path] = item.owner
                repairs.append(
                    RetainedPageRepair(
                        item.final_path,
                        raw,
                        repaired,
                        f"generated-{len(repairs):06d}",
                        "generated sections",
                    )
                )
    except (OSError, UnicodeError, KnowledgeStorageError) as exc:
        raise PageTransitionError(
            f"Cannot inspect generated source sections: {exc}"
        ) from exc
    return replace(
        plan, retained_page_repairs=plan.retained_page_repairs + tuple(repairs)
    ), owners
