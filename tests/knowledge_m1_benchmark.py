"""Deterministic in-memory benchmark harness for M1 knowledge generation."""

from __future__ import annotations

import json
import statistics
import tempfile
import time
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path

from llm_wiki_cli.services.knowledge_envelope import (
    ConsumedInput,
    ConsumedInputKind,
    ProducerComponentInput,
    RepositoryEvidence,
)
from llm_wiki_cli.services.knowledge_evidence import hash_json, sha256_bytes
from llm_wiki_cli.services.knowledge_generation import (
    KnowledgeGenerationInputs,
    build_knowledge_generation_plan,
)
from llm_wiki_cli.services.wiki_surface import (
    PageKind,
    WikiSurfacePage,
    canonical_path,
    iter_page_kinds,
    mcp_uri,
)


@dataclass(frozen=True)
class M1BenchmarkScale:
    """One accepted representative fixture and its CI-safe budget."""

    name: str
    source_count: int
    entities_per_source: int
    max_knowledge_bytes: int
    max_build_seconds: float

    @property
    def page_count(self) -> int:
        return 1 + self.source_count * (1 + self.entities_per_source)


M1_BENCHMARK_SCALES = (
    M1BenchmarkScale(
        name="small",
        source_count=2,
        entities_per_source=2,
        max_knowledge_bytes=128 * 1024,
        max_build_seconds=2.0,
    ),
    M1BenchmarkScale(
        name="medium",
        source_count=20,
        entities_per_source=4,
        max_knowledge_bytes=2 * 1024 * 1024,
        max_build_seconds=8.0,
    ),
    M1BenchmarkScale(
        name="large",
        source_count=75,
        entities_per_source=6,
        max_knowledge_bytes=12 * 1024 * 1024,
        max_build_seconds=30.0,
    ),
)


@dataclass(frozen=True)
class M1BenchmarkResult:
    """Measured planner result with deterministic artifact sizes."""

    scale: str
    source_count: int
    page_count: int
    knowledge_bytes: int
    surface_bytes: int
    manifest_bytes: int
    median_build_seconds: float
    max_build_seconds: float
    repeats: int


def build_m1_benchmark_inputs(
    wiki_dir: Path,
    scale: M1BenchmarkScale,
) -> KnowledgeGenerationInputs:
    """Build a deterministic, extraction-free planner input at *scale*."""

    registry = {entry.kind: entry for entry in iter_page_kinds()}
    inventory: dict[str, dict] = {}
    content_by_page: dict[str, str] = {}
    source_hashes: dict[str, str] = {}
    module_page_map: dict[str, str] = {}
    occurrence_page_map: dict[tuple[str, str, int], str] = {}
    pages_by_path: dict[str, WikiSurfacePage] = {}
    surface_by_path: dict[str, dict] = {}

    def add_page(
        *,
        kind: PageKind,
        page_id: str,
        title: str,
        content: str,
        source_path: str | None,
        outgoing: list[str] | None = None,
    ) -> None:
        entry = registry[kind]
        relative_path = canonical_path(
            kind,
            page_id if entry.requires_page_id else None,
        )
        locator = mcp_uri(
            kind,
            page_id if entry.requires_page_id else None,
        )
        pages_by_path[relative_path] = WikiSurfacePage(
            kind=kind,
            page_id=page_id,
            label=entry.label,
            path=wiki_dir / relative_path,
            relative_path=relative_path,
            mcp_uri=locator,
            obsidian_mirror_dir=entry.obsidian_mirror_dir,
            role=entry.role,
        )
        content_by_page[relative_path] = content
        surface_by_path[relative_path] = {
            "kind": kind.value,
            "id": page_id,
            "title": title,
            "canonical_path": relative_path,
            "source_path": source_path,
            "role": entry.role.value,
            "mcp_uri": locator,
            "outgoing_internal_links": outgoing or [],
        }

    add_page(
        kind=PageKind.INDEX,
        page_id=PageKind.INDEX.value,
        title="M1 benchmark",
        content="# M1 benchmark\n\nDeterministic generated-observation fixture.\n",
        source_path=None,
    )

    for source_index in range(scale.source_count):
        source_path = f"src/benchmark/module_{source_index:03d}.py"
        module_page_id = f"module_{source_index:03d}"
        module_page_map[source_path] = module_page_id
        classes: list[dict] = []
        entity_paths: list[str] = []
        module_links: list[str] = []
        source_lines = [f'"""Benchmark module {source_index}."""', ""]
        for entity_index in range(scale.entities_per_source):
            entity_name = f"Entity_{source_index:03d}_{entity_index:02d}"
            entity_page_id = entity_name
            coordinate = (entity_name, source_path, 1)
            occurrence_page_map[coordinate] = entity_page_id
            entity_path = canonical_path(PageKind.ENTITIES, entity_page_id)
            entity_paths.append(entity_path)
            module_links.append(f"- [{entity_name}](../{entity_path})")
            classes.append(
                {
                    "name": entity_name,
                    "kind": "class",
                    "line": 3 + entity_index * 3,
                    "bases": [],
                    "decorators": [],
                    "attributes": [],
                    "methods": [],
                }
            )
            source_lines.extend((f"class {entity_name}:", "    pass", ""))
            add_page(
                kind=PageKind.ENTITIES,
                page_id=entity_page_id,
                title=entity_name,
                content=f"# {entity_name}\n\nGenerated structure.\n",
                source_path=source_path,
            )
        inventory[source_path] = {
            "language": "python",
            "module_docstring": f"Benchmark module {source_index}.",
            "classes": classes,
            "functions": [],
            "imports": [],
        }
        source_hashes[source_path] = sha256_bytes(
            ("\n".join(source_lines) + "\n").encode("utf-8")
        )
        add_page(
            kind=PageKind.MODULES,
            page_id=module_page_id,
            title=f"{module_page_id} Module",
            content=(f"# {module_page_id} Module\n\n" + "\n".join(module_links) + "\n"),
            source_path=source_path,
            outgoing=entity_paths,
        )

    kind_rank = {entry.kind: index for index, entry in enumerate(iter_page_kinds())}
    pages = tuple(
        sorted(
            pages_by_path.values(),
            key=lambda page: (
                kind_rank[page.kind],
                page.relative_path.casefold(),
                page.relative_path,
            ),
        )
    )
    surface_pages = [surface_by_path[page.relative_path] for page in pages]
    counts = Counter(page.kind.value for page in pages)
    by_kind = {
        entry.kind.value: counts[entry.kind.value] for entry in registry.values()
    }
    surface_payload = {
        "schema_version": "llm-wiki-surface-index/v1",
        "counts": {
            "total": len(pages),
            "by_kind": by_kind,
            "dependency_architecture": 0,
            "assets": {
                "total": 0,
                "referenced": 0,
                "unreferenced": 0,
                "by_media_type": {"image": 0, "video": 0, "other": 0},
            },
        },
        "dependency_pages": {
            "dependencies": False,
            "load_order": False,
            "count": 0,
        },
        "assets": {"by_page": {}, "referenced": [], "unreferenced": []},
        "flows": [],
        "pages": surface_pages,
        "source_hash": hash_json(
            {
                "benchmark": scale.name,
                "source_count": scale.source_count,
                "entities_per_source": scale.entities_per_source,
                "pages": [page["canonical_path"] for page in surface_pages],
            }
        ),
    }
    return KnowledgeGenerationInputs(
        wiki_dir=wiki_dir,
        inventory=inventory,
        pages=pages,
        content_by_page=content_by_page,
        surface_index_bytes=None,
        surface_index_payload=surface_payload,
        source_content_hashes=source_hashes,
        consumed_inputs=tuple(
            ConsumedInput(
                path=path,
                content_hash=content_hash,
                kind=ConsumedInputKind.SOURCE,
            )
            for path, content_hash in source_hashes.items()
        ),
        module_page_map=module_page_map,
        entity_occurrence_page_map=occurrence_page_map,
        extractor_ref_by_source={path: "python-ast" for path in inventory},
        inventory_complete_by_source={path: True for path in inventory},
        repository_evidence=RepositoryEvidence(),
        configured_public_identity="example.invalid/llm-wiki/m1-benchmark",
        generation_options={"benchmark_scale": scale.name},
        generation_option_defaults={"benchmark_scale": scale.name},
        generation_option_allowlist=("benchmark_scale",),
        tool=ProducerComponentInput(
            component_id="agent-wiki-cli",
            version="1.4.0",
            configuration={"profile": "m1-benchmark"},
        ),
        extractors=(
            ProducerComponentInput(
                component_id="python-ast",
                version="stdlib",
                configuration={"inventory_mode": "deep"},
                limitations=("syntax-only",),
            ),
        ),
        manifest_generation_inputs={"benchmark_scale": scale.name},
    )


def run_m1_benchmark(
    wiki_dir: Path,
    scale: M1BenchmarkScale,
    *,
    repeats: int = 2,
) -> M1BenchmarkResult:
    """Measure planner construction while proving deterministic output bytes."""

    if isinstance(repeats, bool) or not isinstance(repeats, int) or repeats < 1:
        raise ValueError("repeats must be a positive integer")
    inputs = build_m1_benchmark_inputs(wiki_dir, scale)
    durations: list[float] = []
    expected_artifacts: tuple[bytes, bytes, bytes] | None = None
    last_artifacts: tuple[bytes, bytes, bytes] | None = None
    for _index in range(repeats):
        started = time.perf_counter()
        plan = build_knowledge_generation_plan(inputs)
        durations.append(time.perf_counter() - started)
        last_artifacts = (
            plan.surface_index.content,
            plan.knowledge_index.content,
            plan.manifest.content,
        )
        if expected_artifacts is None:
            expected_artifacts = last_artifacts
        elif last_artifacts != expected_artifacts:
            raise AssertionError("M1 planner emitted non-deterministic bytes")
    assert last_artifacts is not None
    return M1BenchmarkResult(
        scale=scale.name,
        source_count=scale.source_count,
        page_count=scale.page_count,
        knowledge_bytes=len(last_artifacts[1]),
        surface_bytes=len(last_artifacts[0]),
        manifest_bytes=len(last_artifacts[2]),
        median_build_seconds=statistics.median(durations),
        max_build_seconds=max(durations),
        repeats=repeats,
    )


def _main() -> None:
    with tempfile.TemporaryDirectory(prefix="llm-wiki-m1-benchmark-") as temp:
        root = Path(temp)
        results = [
            asdict(run_m1_benchmark(root / scale.name, scale))
            for scale in M1_BENCHMARK_SCALES
        ]
    print(json.dumps(results, indent=2, sort_keys=True))


if __name__ == "__main__":
    _main()


__all__ = [
    "M1_BENCHMARK_SCALES",
    "M1BenchmarkResult",
    "M1BenchmarkScale",
    "build_m1_benchmark_inputs",
    "run_m1_benchmark",
]
