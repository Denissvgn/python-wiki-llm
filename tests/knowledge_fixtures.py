"""Reusable, extraction-free fixtures for the native knowledge roadmap.

The builders in this module deliberately return precomputed inputs. Bootstrap,
sync, lint, API, context, and MCP tests can reuse the same evaluated inventory,
evidence, page maps, and projection bytes without running an extractor or
walking a source tree again.
"""

from __future__ import annotations

import hashlib
import json
import re
import tempfile
from copy import deepcopy
from dataclasses import asdict, dataclass, is_dataclass
from pathlib import Path
from typing import Any, Mapping, Optional

from llm_wiki_cli.services.contracts import KNOWLEDGE_SCHEMA_VERSION
from llm_wiki_cli.services.knowledge_model import (
    REPOSITORY_IDENTITY_SOURCE_EXTENSION,
    ComputedFreshness,
    KnowledgeLoadState,
    KnowledgeProjectionProfile,
    RepositoryIdentitySource,
    parse_knowledge_index,
    serialize_knowledge_index,
)
from llm_wiki_cli.services.wiki_media import normalize_markdown_link_target
from llm_wiki_cli.services.wiki_surface_index import (
    SURFACE_INDEX_FILENAME,
    build_surface_index,
)

FIXTURE_REPOSITORY_IDENTITY = "example.invalid/acme/knowledge-fixture"
FIXTURE_GIT_REVISION = "git:0123456789abcdef0123456789abcdef01234567"
FIXTURE_SOURCE_PATH = "src/accounts.py"
FIXTURE_WIKI_DIR = "docs/llm_wiki"
FIXTURE_KNOWLEDGE_FILENAME = ".llm-wiki-knowledge.json"
FIXTURE_CONSUMERS = ("bootstrap", "sync", "lint", "api", "context", "mcp")
FIXTURE_ASSETS = {
    "assets/account-flow.svg": (
        b'<svg xmlns="http://www.w3.org/2000/svg" width="1" height="1"></svg>\n'
    )
}


def fixture_hash(label: str) -> str:
    """Return a deterministic SHA-256 wire value for a fixture label."""

    return "sha256:" + hashlib.sha256(label.encode("utf-8")).hexdigest()


def _projection_hash(value: bytes) -> str:
    return "sha256:" + hashlib.sha256(value).hexdigest()


def _canonical_json_bytes(value: Mapping[str, Any]) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")


def _tree_snapshot_hash(files: Mapping[str, str]) -> str:
    """Hash an exact, path-keyed set of UTF-8 fixture bytes."""

    encoded = json.dumps(
        dict(files),
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return _projection_hash(encoded)


def fail_if_extraction_runs(*_args: Any, **_kwargs: Any) -> None:
    """Reusable monkeypatch target proving a consumer reused evaluated inputs."""

    raise AssertionError("knowledge fixture unexpectedly invoked extraction")


@dataclass(frozen=True)
class PageFixture:
    page_kind: str
    page_id: str
    canonical_path: str
    role: str
    content: str


@dataclass(frozen=True)
class EvaluatedKnowledgeFixture:
    """One already-evaluated source/wiki input set."""

    name: str
    source_files: Mapping[str, str]
    assets: Mapping[str, bytes]
    inventory: Mapping[str, Any]
    pages: tuple[PageFixture, ...]
    module_page_map: Mapping[str, str]
    entity_occurrence_page_map: Mapping[tuple[str, str, int], str]
    surface_payload: Mapping[str, Any]
    surface_bytes: bytes
    knowledge_payload: Mapping[str, Any]
    knowledge_bytes: bytes
    extraction_runs: int = 1

    def inputs_for(self, consumer: str) -> dict[str, Any]:
        """Return an isolated copy without invoking source discovery/extraction."""

        if consumer not in FIXTURE_CONSUMERS:
            raise ValueError(f"unsupported fixture consumer: {consumer!r}")
        return {
            "consumer": consumer,
            "source_files": deepcopy(dict(self.source_files)),
            "assets": deepcopy(dict(self.assets)),
            "inventory": deepcopy(dict(self.inventory)),
            "pages": deepcopy(self.pages),
            "module_page_map": deepcopy(dict(self.module_page_map)),
            "entity_occurrence_page_map": deepcopy(
                dict(self.entity_occurrence_page_map)
            ),
            "surface_payload": deepcopy(dict(self.surface_payload)),
            "surface_bytes": self.surface_bytes,
            "knowledge_payload": deepcopy(dict(self.knowledge_payload)),
            "knowledge_bytes": self.knowledge_bytes,
            "extractor_guard": fail_if_extraction_runs,
            "extraction_runs": self.extraction_runs,
        }


@dataclass(frozen=True)
class FreshnessFixture:
    name: str
    expected: ComputedFreshness
    live_evaluated: bool
    source_present: Optional[bool]
    recorded_source_hash: Optional[str]
    recorded_observation_hash: Optional[str]
    recorded_basis_hash: Optional[str]
    live_source_hash: Optional[str]
    live_observation_hash: Optional[str]
    live_basis_hash: Optional[str]
    reason: str
    sibling_locator: Optional[str] = None
    recorded_sibling_observation_hash: Optional[str] = None
    live_sibling_observation_hash: Optional[str] = None
    source_path: str = FIXTURE_SOURCE_PATH
    recorded_source: Optional[str] = None
    live_source: Optional[str] = None
    recorded_inventory: Optional[Mapping[str, Any]] = None
    live_inventory: Optional[Mapping[str, Any]] = None


@dataclass(frozen=True)
class LinkOutcomeFixture:
    name: str
    markdown: str
    target: Mapping[str, Any]
    resolution: str

    def relationship(
        self,
        source_locator: str = "llm-wiki://modules/accounts",
        *,
        source_page: Optional[str] = None,
    ) -> dict[str, Any]:
        target = deepcopy(dict(self.target))
        if source_page is not None:
            snippet_start = source_page.index(self.markdown)
            location = target["location"]
            target["location"] = {
                "start": snippet_start + location["start"],
                "end": snippet_start + location["end"],
            }
        return {
            "kind": "links_to",
            "from": source_locator,
            "target": target,
            "origin": "markdown",
            "evidence": {
                "state": "present",
                "page_hash": (
                    _projection_hash(source_page.encode("utf-8"))
                    if source_page is not None
                    else fixture_hash("page:modules/accounts")
                ),
            },
            "resolution": self.resolution,
        }


@dataclass(frozen=True)
class BundleEnvelopeFixture:
    name: str
    bundle: Mapping[str, Any]


@dataclass(frozen=True)
class RepositoryIdentityPolicyFixture:
    """One future envelope-builder input and its normative identity result."""

    name: str
    configured_public_identity: Optional[str]
    vcs_remotes: Mapping[str, str]
    upstream_remote: Optional[str]
    expected_identity: str
    expected_source: RepositoryIdentitySource
    reason: str

    def expected_repository(self) -> dict[str, Any]:
        repository: dict[str, Any] = {
            "identity": self.expected_identity,
            "evaluated_revision": "unknown",
            "working_tree": "unknown",
        }
        if self.expected_source is not RepositoryIdentitySource.UNKNOWN:
            repository["extensions"] = {
                REPOSITORY_IDENTITY_SOURCE_EXTENSION: self.expected_source.value
            }
        return repository


@dataclass(frozen=True)
class RedactionPolicyFixture:
    """Machine-readable cases for the later allowlist projection boundary."""

    profile: KnowledgeProjectionProfile
    retained_identity_sources: frozenset[RepositoryIdentitySource]
    retained_evaluated_revision: bool
    retained_working_tree_state: bool
    retained_actor_identity: bool
    retained_unreviewed_extensions: bool
    prohibited_value_classes: frozenset[str]


@dataclass(frozen=True)
class ProjectionFixture:
    """Neutral projection/commit fixture; it does not preempt manifest v5 fields."""

    name: str
    surface_bytes: Optional[bytes]
    knowledge_bytes: Optional[bytes]
    committed_surface_hash: Optional[str]
    committed_knowledge_hash: Optional[str]
    expected_state: KnowledgeLoadState
    reason: str
    fallback_selected: bool = False
    underlying_state: Optional[KnowledgeLoadState] = None


def _repository(
    *,
    identity: str = FIXTURE_REPOSITORY_IDENTITY,
    identity_source: RepositoryIdentitySource = (
        RepositoryIdentitySource.CONFIGURED_PUBLIC
    ),
    revision: str = FIXTURE_GIT_REVISION,
    working_tree: str = "clean",
) -> dict[str, Any]:
    repository: dict[str, Any] = {
        "identity": identity,
        "evaluated_revision": revision,
        "working_tree": working_tree,
    }
    if identity_source is not RepositoryIdentitySource.UNKNOWN:
        repository["extensions"] = {
            REPOSITORY_IDENTITY_SOURCE_EXTENSION: identity_source.value
        }
    return repository


def _bundle(
    repository: Optional[Mapping[str, Any]] = None,
    *,
    snapshot: Optional[Mapping[str, str]] = None,
) -> dict[str, Any]:
    snapshot_payload = {
        "source_snapshot_hash": fixture_hash("snapshot:source:v1"),
        "markdown_snapshot_hash": fixture_hash("snapshot:markdown:v1"),
        "surface_index_hash": fixture_hash("snapshot:surface:v1"),
        "generation_options_hash": fixture_hash("snapshot:options:v1"),
    }
    snapshot_payload.update(snapshot or {})
    return {
        "repository": deepcopy(dict(repository or _repository())),
        "snapshot": snapshot_payload,
        "producer": {
            "tool": {
                "id": "agent-wiki-cli",
                "version": "1.4.0",
            },
            "extractors": [
                {
                    "id": "python-ast",
                    "version": "stdlib",
                    "configuration_hash": fixture_hash("extractor:python:v1"),
                    "limitations": ["syntax-only"],
                }
            ],
            "plugins": [],
        },
    }


def page_role_fixtures() -> tuple[PageFixture, ...]:
    """Return one generated, semantic, and mixed canonical page."""

    return (
        PageFixture(
            page_kind="log",
            page_id="log",
            canonical_path="log.md",
            role="generated",
            content="# Architectural Log\n\nFixture history.\n",
        ),
        PageFixture(
            page_kind="modules",
            page_id="accounts",
            canonical_path="modules/accounts.md",
            role="semantic",
            content="# accounts Module\n\nAccount-domain structure and semantics.\n",
        ),
        PageFixture(
            page_kind="workflows",
            page_id="onboarding",
            canonical_path="workflows/onboarding.md",
            role="mixed",
            content="# onboarding\n\nGenerated flow with maintained semantic notes.\n",
        ),
    )


def _base_pages(
    entity_page_ids: tuple[str, ...],
    module_page_id: str = "accounts",
    *,
    link_observations: tuple[LinkOutcomeFixture, ...] = (),
) -> tuple[PageFixture, ...]:
    pages = [page for page in page_role_fixtures() if page.page_kind != "modules"]
    module_content = f"# {module_page_id} Module\n\nFixture module documentation.\n"
    if link_observations:
        module_content += "\n## Usage\n\nAnchor target for the link matrix.\n"
        module_content += "\n## Link observations\n\n"
        module_content += "\n".join(link.markdown for link in link_observations)
        module_content += "\n"
    pages.append(
        PageFixture(
            page_kind="modules",
            page_id=module_page_id,
            canonical_path=f"modules/{module_page_id}.md",
            role="semantic",
            content=module_content,
        )
    )
    pages.append(
        PageFixture(
            page_kind="index",
            page_id="index",
            canonical_path="index.md",
            role="mixed",
            content="# LLM Wiki Index\n\nDeterministic fixture navigation.\n",
        )
    )
    pages.extend(
        PageFixture(
            page_kind="entities",
            page_id=page_id,
            canonical_path=f"entities/{page_id}.md",
            role="semantic",
            content=f"# {page_id}\n\nOccurrence-specific entity documentation.\n",
        )
        for page_id in entity_page_ids
    )
    return tuple(pages)


def _semantic_concept(
    *,
    page_kind: str,
    page_id: str,
    concept_kind: str,
    title: str,
    scope: str,
    source_path: str,
    source_content_hash: str,
    page_hash: str,
) -> dict[str, Any]:
    return {
        "locator": f"llm-wiki://{page_kind}/{page_id}",
        "concept_kind": concept_kind,
        "title": title,
        "document": {
            "page_kind": page_kind,
            "page_id": page_id,
            "canonical_path": f"{page_kind}/{page_id}.md",
            "role": "semantic",
        },
        "facets": {
            "structure": {
                "origin": "extracted",
                "evidence": "present",
                "basis": {
                    "scope": scope,
                    "source_path": source_path,
                    "extractor_ref": "python-ast",
                    "source_content_hash": source_content_hash,
                    "concept_observation_hash": fixture_hash(
                        f"observation:{page_kind}:{page_id}:v1"
                    ),
                },
            },
            "semantics": {
                "ownership": "semantic",
                "page_hash": page_hash,
                "authorship": {"kind": "unknown"},
                "verification": "untracked",
            },
        },
        "lifecycle": "unknown",
    }


def _role_concept(page: PageFixture) -> dict[str, Any]:
    concept_kind = {
        "index": "navigation-document",
        "log": "change-log-document",
        "workflows": "workflow",
    }[page.page_kind]
    return {
        "locator": (
            f"llm-wiki://{page.page_kind}/{page.page_id}"
            if page.page_kind == "workflows"
            else f"llm-wiki://{page.page_kind}"
        ),
        "concept_kind": concept_kind,
        "title": page.page_id,
        "document": {
            "page_kind": page.page_kind,
            "page_id": page.page_id,
            "canonical_path": page.canonical_path,
            "role": page.role,
        },
        "facets": {
            "structure": {
                "origin": "unknown",
                "evidence": (
                    "not-applicable"
                    if concept_kind.endswith("-document")
                    else "unknown"
                ),
            },
            "semantics": {
                "ownership": page.role,
                "page_hash": _projection_hash(page.content.encode("utf-8")),
                "authorship": {"kind": "unknown"},
                "verification": "untracked",
            },
        },
        "lifecycle": "unknown",
    }


def _derived_relationship(
    locator: str, source_path: str, observation_hash: str
) -> dict[str, Any]:
    return {
        "kind": "derived_from",
        "from": locator,
        "target": {
            "target_class": "source",
            "source_path": source_path,
        },
        "origin": "extracted",
        "evidence": {
            "state": "present",
            "concept_observation_hash": observation_hash,
        },
        "resolution": "resolved",
    }


def _knowledge_payload(
    *,
    source_path: str,
    source_content: str,
    module_page_id: str,
    entities: tuple[tuple[str, str], ...],
    pages: tuple[PageFixture, ...],
    surface_index_hash: str,
    links: tuple[LinkOutcomeFixture, ...] = (),
    repository: Optional[Mapping[str, str]] = None,
) -> dict[str, Any]:
    source_content_hash = _projection_hash(source_content.encode("utf-8"))
    pages_by_path = {page.canonical_path: page for page in pages}
    module_page = pages_by_path[f"modules/{module_page_id}.md"]
    concepts = [
        _semantic_concept(
            page_kind="modules",
            page_id=module_page_id,
            concept_kind="source-module",
            title=module_page_id,
            scope="module",
            source_path=source_path,
            source_content_hash=source_content_hash,
            page_hash=_projection_hash(module_page.content.encode("utf-8")),
        )
    ]
    concepts.extend(
        _semantic_concept(
            page_kind="entities",
            page_id=page_id,
            concept_kind="code-entity",
            title=title,
            scope="entity",
            source_path=source_path,
            source_content_hash=source_content_hash,
            page_hash=_projection_hash(
                pages_by_path[f"entities/{page_id}.md"].content.encode("utf-8")
            ),
        )
        for title, page_id in entities
    )
    concepts.extend(
        _role_concept(page)
        for page in pages
        if page.page_kind in {"index", "log", "workflows"}
    )
    source_concepts = [
        concept
        for concept in concepts
        if concept["concept_kind"] in {"source-module", "code-entity"}
    ]
    relationships = [
        _derived_relationship(
            concept["locator"],
            source_path,
            concept["facets"]["structure"]["basis"]["concept_observation_hash"],
        )
        for concept in source_concepts
    ]
    relationships.extend(
        link.relationship(
            f"llm-wiki://modules/{module_page_id}",
            source_page=module_page.content,
        )
        for link in links
    )
    return {
        "schema_version": KNOWLEDGE_SCHEMA_VERSION,
        "bundle": _bundle(
            repository,
            snapshot={
                "source_snapshot_hash": _tree_snapshot_hash(
                    {source_path: source_content}
                ),
                "markdown_snapshot_hash": _tree_snapshot_hash(
                    {page.canonical_path: page.content for page in pages}
                ),
                "surface_index_hash": surface_index_hash,
                "generation_options_hash": _projection_hash(b"{}\n"),
            },
        ),
        "concepts": concepts,
        "relationships": relationships,
        "extensions": {
            "example.invalid/fixture": {
                "name": "knowledge-contract-matrix",
                "extraction_runs": 1,
            }
        },
    }


def link_outcome_fixtures() -> tuple[LinkOutcomeFixture, ...]:
    """Return the required resolved/external/anchor/malformed/unresolved matrix."""

    def build(
        *,
        name: str,
        label: str,
        raw_target: str,
        target_class: str,
        resolution: str,
        endpoint: Optional[tuple[str, str]] = None,
    ) -> LinkOutcomeFixture:
        markdown = f"See [{label}]({raw_target})."
        start = markdown.index("[")
        end = markdown.index(")", start) + 1
        target: dict[str, Any] = {
            "target_class": target_class,
            "raw_target": raw_target,
            "normalized_target": normalize_markdown_link_target(raw_target),
            "label": label,
            "location": {"start": start, "end": end},
        }
        if endpoint is not None:
            target[endpoint[0]] = endpoint[1]
        return LinkOutcomeFixture(
            name=name,
            markdown=markdown,
            target=target,
            resolution=resolution,
        )

    return (
        build(
            name="resolved",
            label="User",
            raw_target="../entities/User.md",
            target_class="concept",
            resolution="resolved",
            endpoint=("canonical_path", "entities/User.md"),
        ),
        build(
            name="external",
            label="reference",
            raw_target="https://example.invalid/reference",
            target_class="external",
            resolution="external",
            endpoint=("external_uri", "https://example.invalid/reference"),
        ),
        build(
            name="mail",
            label="support",
            raw_target="mailto:support@example.invalid",
            target_class="mail",
            resolution="external",
            endpoint=("external_uri", "mailto:support@example.invalid"),
        ),
        build(
            name="anchor-only",
            label="usage",
            raw_target="#usage",
            target_class="anchor",
            resolution="resolved",
        ),
        build(
            name="asset",
            label="diagram",
            raw_target="../assets/account-flow.svg",
            target_class="asset",
            resolution="resolved",
        ),
        build(
            name="malformed",
            label="broken",
            raw_target="",
            target_class="malformed",
            resolution="unresolved",
        ),
        build(
            name="unresolved",
            label="Missing",
            raw_target=r"..\entities\Missing.md",
            target_class="concept",
            resolution="unresolved",
        ),
        build(
            name="ambiguous",
            label="Parser",
            raw_target="../entities/Parser.md",
            target_class="concept",
            resolution="ambiguous",
        ),
    )


def _write_precomputed_tree(
    *,
    root: Path,
    source_files: Mapping[str, str],
    assets: Mapping[str, bytes],
    pages: tuple[PageFixture, ...],
) -> tuple[Path, dict[str, Path], dict[str, Path], dict[str, Path]]:
    wiki_root = root / FIXTURE_WIKI_DIR
    source_paths: dict[str, Path] = {}
    asset_paths: dict[str, Path] = {}
    page_paths: dict[str, Path] = {}
    for relative, content in source_files.items():
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content.encode("utf-8"))
        source_paths[relative] = path
    for relative, content in assets.items():
        path = wiki_root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        asset_paths[relative] = path
    for page in pages:
        path = wiki_root / page.canonical_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(page.content.encode("utf-8"))
        page_paths[page.canonical_path] = path
    return wiki_root, source_paths, asset_paths, page_paths


def _build_surface_projection(
    *,
    source_files: Mapping[str, str],
    assets: Mapping[str, bytes],
    inventory: Mapping[str, Any],
    pages: tuple[PageFixture, ...],
    module_page_map: Mapping[str, str],
    entity_occurrence_page_map: Mapping[tuple[str, str, int], str],
) -> tuple[dict[str, Any], bytes]:
    """Build exact production surface-v1 bytes without invoking extraction."""

    with tempfile.TemporaryDirectory(prefix="llm-wiki-knowledge-fixture-") as tmp:
        root = Path(tmp)
        wiki_root, _sources, _assets, _pages = _write_precomputed_tree(
            root=root,
            source_files=source_files,
            assets=assets,
            pages=pages,
        )
        payload = build_surface_index(
            wiki_root,
            inventory,
            src_dir=root,
            entity_occurrence_page_cache=entity_occurrence_page_map,
            module_page_map=module_page_map,
        )
    return payload, _canonical_json_bytes(payload)


def _evaluated_fixture(
    *,
    name: str,
    source_files: Mapping[str, str],
    assets: Mapping[str, bytes],
    inventory: Mapping[str, Any],
    pages: tuple[PageFixture, ...],
    module_page_map: Mapping[str, str],
    entity_occurrence_page_map: Mapping[tuple[str, str, int], str],
    module_page_id: str,
    entities: tuple[tuple[str, str], ...],
    links: tuple[LinkOutcomeFixture, ...] = (),
) -> EvaluatedKnowledgeFixture:
    surface_payload, surface_bytes = _build_surface_projection(
        source_files=source_files,
        assets=assets,
        inventory=inventory,
        pages=pages,
        module_page_map=module_page_map,
        entity_occurrence_page_map=entity_occurrence_page_map,
    )
    source_path, source_content = next(iter(source_files.items()))
    knowledge_payload = _knowledge_payload(
        source_path=source_path,
        source_content=source_content,
        module_page_id=module_page_id,
        entities=entities,
        pages=pages,
        surface_index_hash=_projection_hash(surface_bytes),
        links=links,
    )
    model = parse_knowledge_index(knowledge_payload)
    knowledge_bytes = serialize_knowledge_index(model).encode("utf-8")
    return EvaluatedKnowledgeFixture(
        name=name,
        source_files=deepcopy(dict(source_files)),
        assets=deepcopy(dict(assets)),
        inventory=deepcopy(dict(inventory)),
        pages=deepcopy(pages),
        module_page_map=deepcopy(dict(module_page_map)),
        entity_occurrence_page_map=deepcopy(dict(entity_occurrence_page_map)),
        surface_payload=surface_payload,
        surface_bytes=surface_bytes,
        knowledge_payload=knowledge_payload,
        knowledge_bytes=knowledge_bytes,
    )


def one_module_two_entities_fixture() -> EvaluatedKnowledgeFixture:
    """Return one extraction result with a module and two entity observations."""

    source = '''"""Account-domain fixture."""

class User:
    """A persisted account."""

class AccountService:
    """Coordinates account operations."""
'''
    inventory = {
        FIXTURE_SOURCE_PATH: {
            "language": "python",
            "module_docstring": "Account-domain fixture.",
            "classes": [
                {
                    "name": "User",
                    "kind": "class",
                    "line": 3,
                    "docstring": "A persisted account.",
                    "bases": [],
                    "decorators": [],
                    "attributes": [],
                    "methods": [],
                },
                {
                    "name": "AccountService",
                    "kind": "class",
                    "line": 6,
                    "docstring": "Coordinates account operations.",
                    "bases": [],
                    "decorators": [],
                    "attributes": [],
                    "methods": [],
                },
            ],
            "functions": [],
            "imports": [],
        }
    }
    links = tuple(case for case in link_outcome_fixtures() if case.name != "ambiguous")
    pages = _base_pages(("User", "AccountService"), link_observations=links)
    return _evaluated_fixture(
        name="one-module-two-entities",
        source_files={FIXTURE_SOURCE_PATH: source},
        assets=FIXTURE_ASSETS,
        inventory=inventory,
        pages=pages,
        module_page_map={FIXTURE_SOURCE_PATH: "accounts"},
        entity_occurrence_page_map={
            ("User", FIXTURE_SOURCE_PATH, 1): "User",
            ("AccountService", FIXTURE_SOURCE_PATH, 1): "AccountService",
        },
        module_page_id="accounts",
        entities=(("User", "User"), ("AccountService", "AccountService")),
        links=links,
    )


def duplicate_entity_occurrences_fixture() -> EvaluatedKnowledgeFixture:
    """Return two same-name entities with occurrence-specific pages."""

    source_path = "tests/test_parser.py"
    source = '''class Parser:
    """First parser."""

class Parser:
    """Second parser."""
'''
    inventory = {
        source_path: {
            "language": "python",
            "module_docstring": "",
            "classes": [
                {
                    "name": "Parser",
                    "kind": "class",
                    "line": 1,
                    "docstring": "First parser.",
                    "bases": [],
                    "decorators": [],
                    "attributes": [],
                    "methods": [],
                },
                {
                    "name": "Parser",
                    "kind": "class",
                    "line": 4,
                    "docstring": "Second parser.",
                    "bases": [],
                    "decorators": [],
                    "attributes": [],
                    "methods": [],
                },
            ],
            "functions": [],
            "imports": [],
        }
    }
    pages = _base_pages(("Parser", "Parser_2"), module_page_id="test_parser")
    return _evaluated_fixture(
        name="duplicate-entity-occurrences",
        source_files={source_path: source},
        assets={},
        inventory=inventory,
        pages=pages,
        module_page_map={source_path: "test_parser"},
        entity_occurrence_page_map={
            ("Parser", source_path, 1): "Parser",
            ("Parser", source_path, 2): "Parser_2",
        },
        module_page_id="test_parser",
        entities=(("Parser", "Parser"), ("Parser", "Parser_2")),
    )


def freshness_fixtures() -> tuple[FreshnessFixture, ...]:
    """Return one scenario for every consumer-computed freshness state."""

    recorded_source = (
        "class User:\n    active = True\n\nclass AccountService:\n    enabled = True\n"
    )
    byte_only_source = recorded_source + "\n# formatting-only fixture change\n"
    concept_changed_source = (
        "class User:\n    active = False\n\nclass AccountService:\n    enabled = True\n"
    )
    recorded_inventory = {
        "classes": [
            {"name": "User", "attributes": ["active=True"], "methods": []},
            {
                "name": "AccountService",
                "attributes": ["enabled=True"],
                "methods": [],
            },
        ]
    }
    byte_only_inventory = deepcopy(recorded_inventory)
    concept_changed_inventory = deepcopy(recorded_inventory)
    concept_changed_inventory["classes"][0]["attributes"] = ["active=False"]
    source_v1 = "sha256:" + hashlib.sha256(recorded_source.encode()).hexdigest()
    source_v2 = "sha256:" + hashlib.sha256(byte_only_source.encode()).hexdigest()
    source_v3 = "sha256:" + hashlib.sha256(concept_changed_source.encode()).hexdigest()
    observation_v1 = fixture_hash("freshness:observation:v1")
    observation_v2 = fixture_hash("freshness:observation:v2")
    sibling_observation = fixture_hash("freshness:sibling-observation:v1")
    basis_v1 = fixture_hash("freshness:basis:v1")
    basis_v2 = fixture_hash("freshness:basis:extractor-v2")
    basis_v3 = fixture_hash("freshness:basis:config-v2")
    return (
        FreshnessFixture(
            name="unknown-no-live-evaluation",
            expected=ComputedFreshness.UNKNOWN,
            live_evaluated=False,
            source_present=None,
            recorded_source_hash=source_v1,
            recorded_observation_hash=observation_v1,
            recorded_basis_hash=basis_v1,
            live_source_hash=None,
            live_observation_hash=None,
            live_basis_hash=None,
            reason="live-evaluation-not-performed",
            sibling_locator="llm-wiki://entities/AccountService",
            recorded_sibling_observation_hash=sibling_observation,
            live_sibling_observation_hash=None,
            recorded_source=recorded_source,
            live_source=None,
            recorded_inventory=deepcopy(recorded_inventory),
            live_inventory=None,
        ),
        FreshnessFixture(
            name="current",
            expected=ComputedFreshness.CURRENT,
            live_evaluated=True,
            source_present=True,
            recorded_source_hash=source_v1,
            recorded_observation_hash=observation_v1,
            recorded_basis_hash=basis_v1,
            live_source_hash=source_v1,
            live_observation_hash=observation_v1,
            live_basis_hash=basis_v1,
            reason="recorded-basis-matches-live-evaluation",
            sibling_locator="llm-wiki://entities/AccountService",
            recorded_sibling_observation_hash=sibling_observation,
            live_sibling_observation_hash=sibling_observation,
            recorded_source=recorded_source,
            live_source=recorded_source,
            recorded_inventory=deepcopy(recorded_inventory),
            live_inventory=deepcopy(recorded_inventory),
        ),
        FreshnessFixture(
            name="byte-only-source-change",
            expected=ComputedFreshness.NONSEMANTIC_SOURCE_CHANGE,
            live_evaluated=True,
            source_present=True,
            recorded_source_hash=source_v1,
            recorded_observation_hash=observation_v1,
            recorded_basis_hash=basis_v1,
            live_source_hash=source_v2,
            live_observation_hash=observation_v1,
            live_basis_hash=basis_v1,
            reason="source-bytes-changed-concept-observation-unchanged",
            sibling_locator="llm-wiki://entities/AccountService",
            recorded_sibling_observation_hash=sibling_observation,
            live_sibling_observation_hash=sibling_observation,
            recorded_source=recorded_source,
            live_source=byte_only_source,
            recorded_inventory=deepcopy(recorded_inventory),
            live_inventory=deepcopy(byte_only_inventory),
        ),
        FreshnessFixture(
            name="concept-relevant-source-change",
            expected=ComputedFreshness.SOURCE_CHANGED,
            live_evaluated=True,
            source_present=True,
            recorded_source_hash=source_v1,
            recorded_observation_hash=observation_v1,
            recorded_basis_hash=basis_v1,
            live_source_hash=source_v3,
            live_observation_hash=observation_v2,
            live_basis_hash=basis_v1,
            reason="concept-observation-changed",
            sibling_locator="llm-wiki://entities/AccountService",
            recorded_sibling_observation_hash=sibling_observation,
            live_sibling_observation_hash=sibling_observation,
            recorded_source=recorded_source,
            live_source=concept_changed_source,
            recorded_inventory=deepcopy(recorded_inventory),
            live_inventory=deepcopy(concept_changed_inventory),
        ),
        FreshnessFixture(
            name="changed-extractor-version-basis",
            expected=ComputedFreshness.BASIS_INCOMPATIBLE,
            live_evaluated=True,
            source_present=True,
            recorded_source_hash=source_v1,
            recorded_observation_hash=observation_v1,
            recorded_basis_hash=basis_v1,
            live_source_hash=source_v1,
            live_observation_hash=observation_v1,
            live_basis_hash=basis_v2,
            reason="extractor-version-changed",
            sibling_locator="llm-wiki://entities/AccountService",
            recorded_sibling_observation_hash=sibling_observation,
            live_sibling_observation_hash=sibling_observation,
            recorded_source=recorded_source,
            live_source=recorded_source,
            recorded_inventory=deepcopy(recorded_inventory),
            live_inventory=deepcopy(recorded_inventory),
        ),
        FreshnessFixture(
            name="changed-extractor-config-basis",
            expected=ComputedFreshness.BASIS_INCOMPATIBLE,
            live_evaluated=True,
            source_present=True,
            recorded_source_hash=source_v1,
            recorded_observation_hash=observation_v1,
            recorded_basis_hash=basis_v1,
            live_source_hash=source_v1,
            live_observation_hash=observation_v1,
            live_basis_hash=basis_v3,
            reason="extractor-configuration-changed",
            sibling_locator="llm-wiki://entities/AccountService",
            recorded_sibling_observation_hash=sibling_observation,
            live_sibling_observation_hash=sibling_observation,
            recorded_source=recorded_source,
            live_source=recorded_source,
            recorded_inventory=deepcopy(recorded_inventory),
            live_inventory=deepcopy(recorded_inventory),
        ),
        FreshnessFixture(
            name="removed-source-with-prior-evidence",
            expected=ComputedFreshness.SOURCE_MISSING,
            live_evaluated=True,
            source_present=False,
            recorded_source_hash=source_v1,
            recorded_observation_hash=observation_v1,
            recorded_basis_hash=basis_v1,
            live_source_hash=None,
            live_observation_hash=None,
            live_basis_hash=basis_v1,
            reason="reliably-mapped-source-missing",
            sibling_locator="llm-wiki://entities/AccountService",
            recorded_sibling_observation_hash=sibling_observation,
            live_sibling_observation_hash=None,
            recorded_source=recorded_source,
            live_source=None,
            recorded_inventory=deepcopy(recorded_inventory),
            live_inventory=None,
        ),
    )


def source_change_fixtures() -> tuple[FreshnessFixture, ...]:
    names = {
        "byte-only-source-change",
        "concept-relevant-source-change",
        "changed-extractor-version-basis",
        "changed-extractor-config-basis",
    }
    return tuple(case for case in freshness_fixtures() if case.name in names)


def removed_source_fixtures() -> tuple[FreshnessFixture, ...]:
    """Return removed-source cases with and without recoverable prior evidence."""

    with_prior = next(
        case
        for case in freshness_fixtures()
        if case.name == "removed-source-with-prior-evidence"
    )
    without_prior = FreshnessFixture(
        name="removed-source-without-recoverable-evidence",
        expected=ComputedFreshness.UNKNOWN,
        live_evaluated=True,
        source_present=False,
        recorded_source_hash=None,
        recorded_observation_hash=None,
        recorded_basis_hash=None,
        live_source_hash=None,
        live_observation_hash=None,
        live_basis_hash=None,
        reason="missing-source-has-no-reliable-recorded-basis",
    )
    return with_prior, without_prior


def bundle_envelope_fixtures() -> tuple[BundleEnvelopeFixture, ...]:
    return (
        BundleEnvelopeFixture(name="clean", bundle=_bundle(_repository())),
        BundleEnvelopeFixture(
            name="dirty",
            bundle=_bundle(_repository(working_tree="dirty")),
        ),
        BundleEnvelopeFixture(
            name="non-git",
            bundle=_bundle(
                _repository(
                    identity="unknown",
                    identity_source=RepositoryIdentitySource.UNKNOWN,
                    revision="unknown",
                    working_tree="unknown",
                )
            ),
        ),
    )


def repository_identity_fixtures() -> tuple[RepositoryIdentityPolicyFixture, ...]:
    """Return precedence/normalization cases for the future envelope builder."""

    return (
        RepositoryIdentityPolicyFixture(
            name="configured-public-wins",
            configured_public_identity="docs.example/acme/accounts",
            vcs_remotes={
                "origin": (
                    "https://user:token@private.example/acme/accounts.git"
                    "?access_token=secret"
                )
            },
            upstream_remote=None,
            expected_identity="docs.example/acme/accounts",
            expected_source=RepositoryIdentitySource.CONFIGURED_PUBLIC,
            reason="explicit-public-identity-has-highest-precedence",
        ),
        RepositoryIdentityPolicyFixture(
            name="upstream-remote-before-origin",
            configured_public_identity=None,
            vcs_remotes={
                "origin": "https://mirror.example/acme/accounts.git",
                "upstream": "ssh://git@GitHub.com/Acme/Accounts.git",
            },
            upstream_remote="upstream",
            expected_identity="github.com/Acme/Accounts",
            expected_source=RepositoryIdentitySource.NORMALIZED_VCS,
            reason="branch-upstream-remote-is-the-vcs-identity-candidate",
        ),
        RepositoryIdentityPolicyFixture(
            name="origin-fallback",
            configured_public_identity=None,
            vcs_remotes={
                "origin": "https://GitLab.example/Acme/Accounts.git",
                "backup": "https://backup.example/Acme/Accounts.git",
            },
            upstream_remote=None,
            expected_identity="gitlab.example/Acme/Accounts",
            expected_source=RepositoryIdentitySource.NORMALIZED_VCS,
            reason="origin-is-used-when-no-upstream-remote-is-selected",
        ),
        RepositoryIdentityPolicyFixture(
            name="credentialed-origin-sanitized",
            configured_public_identity=None,
            vcs_remotes={
                "origin": (
                    "https://alice:token@Private.example/Acme/Accounts.git"
                    "?access_token=secret#private"
                )
            },
            upstream_remote=None,
            expected_identity="private.example/Acme/Accounts",
            expected_source=RepositoryIdentitySource.NORMALIZED_VCS,
            reason="credentials-query-and-fragment-never-enter-identity",
        ),
        RepositoryIdentityPolicyFixture(
            name="sole-scp-remote",
            configured_public_identity=None,
            vcs_remotes={"source": "git@Code.example:Acme/Accounts.git"},
            upstream_remote=None,
            expected_identity="code.example/Acme/Accounts",
            expected_source=RepositoryIdentitySource.NORMALIZED_VCS,
            reason="a-sole-remote-is-unambiguous",
        ),
        RepositoryIdentityPolicyFixture(
            name="ambiguous-remotes",
            configured_public_identity=None,
            vcs_remotes={
                "one": "https://one.example/acme/accounts.git",
                "two": "https://two.example/acme/accounts.git",
            },
            upstream_remote=None,
            expected_identity="unknown",
            expected_source=RepositoryIdentitySource.UNKNOWN,
            reason="multiple-unselected-remotes-do-not-establish-identity",
        ),
        RepositoryIdentityPolicyFixture(
            name="local-file-remote",
            configured_public_identity=None,
            vcs_remotes={"origin": "file:///Users/alice/private/accounts.git"},
            upstream_remote=None,
            expected_identity="unknown",
            expected_source=RepositoryIdentitySource.UNKNOWN,
            reason="local-remotes-never-become-bundle-identity",
        ),
        RepositoryIdentityPolicyFixture(
            name="windows-local-remote",
            configured_public_identity=None,
            vcs_remotes={"origin": r"C:\Users\alice\private\accounts"},
            upstream_remote=None,
            expected_identity="unknown",
            expected_source=RepositoryIdentitySource.UNKNOWN,
            reason="windows-checkout-paths-never-become-bundle-identity",
        ),
        RepositoryIdentityPolicyFixture(
            name="unc-local-remote",
            configured_public_identity=None,
            vcs_remotes={"origin": r"\\server\share\private\accounts"},
            upstream_remote=None,
            expected_identity="unknown",
            expected_source=RepositoryIdentitySource.UNKNOWN,
            reason="unc-paths-never-become-bundle-identity",
        ),
        RepositoryIdentityPolicyFixture(
            name="no-vcs",
            configured_public_identity=None,
            vcs_remotes={},
            upstream_remote=None,
            expected_identity="unknown",
            expected_source=RepositoryIdentitySource.UNKNOWN,
            reason="missing-identity-evidence-uses-the-nonidentity-sentinel",
        ),
    )


def redaction_policy_fixtures() -> tuple[RedactionPolicyFixture, ...]:
    """Define profile decisions without implementing the future exporter."""

    always_prohibited = frozenset(
        {
            "absolute-path",
            "credential",
            "environment-dump",
            "raw-plugin-settings",
            "raw-vcs-remote",
        }
    )
    return (
        RedactionPolicyFixture(
            profile=KnowledgeProjectionProfile.INTERNAL,
            retained_identity_sources=frozenset(
                {
                    RepositoryIdentitySource.CONFIGURED_PUBLIC,
                    RepositoryIdentitySource.NORMALIZED_VCS,
                }
            ),
            retained_evaluated_revision=True,
            retained_working_tree_state=True,
            retained_actor_identity=True,
            retained_unreviewed_extensions=True,
            prohibited_value_classes=always_prohibited,
        ),
        RedactionPolicyFixture(
            profile=KnowledgeProjectionProfile.PUBLIC_PORTABLE,
            retained_identity_sources=frozenset(
                {RepositoryIdentitySource.CONFIGURED_PUBLIC}
            ),
            retained_evaluated_revision=False,
            retained_working_tree_state=False,
            retained_actor_identity=False,
            retained_unreviewed_extensions=False,
            prohibited_value_classes=always_prohibited
            | {
                "credentialed-link-observation",
                "local-actor-identity",
                "normalized-vcs-identity",
                "private-plugin-record",
                "unreviewed-extension",
            },
        ),
    )


def producer_basis_fixtures() -> tuple[BundleEnvelopeFixture, ...]:
    """Return stable source inputs with changed producer evidence."""

    baseline = _bundle(_repository())
    baseline["producer"]["plugins"] = [
        {
            "id": "documentation-hooks/knowledge",
            "version": "1.0.0",
            "configuration_hash": fixture_hash("plugin:knowledge:config-v1"),
            "limitations": ["metadata-only"],
        }
    ]
    extractor_version = deepcopy(baseline)
    extractor_version["producer"]["extractors"][0]["version"] = "stdlib-v2"
    extractor_config = deepcopy(baseline)
    extractor_config["producer"]["extractors"][0]["configuration_hash"] = fixture_hash(
        "extractor:python:config-v2"
    )
    plugin_version = deepcopy(baseline)
    plugin_version["producer"]["plugins"][0]["version"] = "1.1.0"
    plugin_config = deepcopy(baseline)
    plugin_config["producer"]["plugins"][0]["configuration_hash"] = fixture_hash(
        "plugin:knowledge:config-v2"
    )
    plugin_limitations = deepcopy(baseline)
    plugin_limitations["producer"]["plugins"][0]["limitations"] = [
        "metadata-only",
        "partial-symbol-resolution",
    ]
    unknown_plugin_configuration = deepcopy(baseline)
    unknown_plugin_configuration["producer"]["plugins"][0].pop("configuration_hash")
    unknown_plugin_configuration["producer"]["plugins"][0]["limitations"] = [
        "configuration-basis-unknown",
        "metadata-only",
    ]
    return (
        BundleEnvelopeFixture(name="producer-baseline", bundle=baseline),
        BundleEnvelopeFixture(
            name="changed-extractor-version", bundle=extractor_version
        ),
        BundleEnvelopeFixture(name="changed-extractor-config", bundle=extractor_config),
        BundleEnvelopeFixture(name="changed-plugin-version", bundle=plugin_version),
        BundleEnvelopeFixture(name="changed-plugin-config", bundle=plugin_config),
        BundleEnvelopeFixture(
            name="changed-plugin-limitations",
            bundle=plugin_limitations,
        ),
        BundleEnvelopeFixture(
            name="unknown-plugin-configuration-basis",
            bundle=unknown_plugin_configuration,
        ),
    )


def inert_metadata_fixture() -> dict[str, Any]:
    """Return valid but hostile-looking metadata that must remain passive."""

    payload = build_complete_knowledge_payload()
    payload["bundle"]["producer"]["plugins"] = [
        {
            "id": "example.invalid/passive-plugin",
            "version": "$(touch should-not-exist)",
            "configuration_hash": fixture_hash("passive-plugin-config"),
            "limitations": ["run-helper-should-not-exist"],
            "extensions": {
                "example.invalid/dispatch": {
                    "command": ["python", "-c", "raise SystemExit(99)"],
                    "entry_point": "malicious.module:activate",
                    "model": "remote-model",
                    "url": "https://private.example/activate",
                }
            },
        }
    ]
    payload["extensions"]["example.invalid/access-control"] = {
        "allow": True,
        "roles": ["administrator"],
        "projection_profile": "internal",
    }
    semantic = payload["concepts"][0]["facets"]["semantics"]
    semantic["authorship"] = {
        "kind": "agent",
        "id": "local-user@example.invalid",
        "model": "exec://private-model",
    }
    return payload


def _projection_bytes() -> tuple[bytes, bytes]:
    fixture = one_module_two_entities_fixture()
    return fixture.surface_bytes, fixture.knowledge_bytes


def projection_integrity_fixtures() -> tuple[ProjectionFixture, ...]:
    """Return interrupted/mismatched projection commitments."""

    surface, knowledge = _projection_bytes()
    old_surface = surface.replace(b"User.md", b"Legacy.md")
    old_knowledge = knowledge.replace(
        b"knowledge-contract-matrix", b"knowledge-contract-legacy"
    )
    return (
        ProjectionFixture(
            name="interrupted-before-manifest-commit",
            surface_bytes=surface,
            knowledge_bytes=knowledge,
            committed_surface_hash=_projection_hash(old_surface),
            committed_knowledge_hash=_projection_hash(old_knowledge),
            expected_state=KnowledgeLoadState.MIXED_SNAPSHOT,
            reason="manifest-marker-still-commits-prior-projections",
        ),
        ProjectionFixture(
            name="surface-projection-hash-mismatch",
            surface_bytes=surface,
            knowledge_bytes=knowledge,
            committed_surface_hash=fixture_hash("projection:wrong-surface"),
            committed_knowledge_hash=_projection_hash(knowledge),
            expected_state=KnowledgeLoadState.MIXED_SNAPSHOT,
            reason="surface-projection-hash-mismatch",
        ),
        ProjectionFixture(
            name="knowledge-projection-hash-mismatch",
            surface_bytes=surface,
            knowledge_bytes=knowledge,
            committed_surface_hash=_projection_hash(surface),
            committed_knowledge_hash=fixture_hash("projection:wrong-knowledge"),
            expected_state=KnowledgeLoadState.MIXED_SNAPSHOT,
            reason="knowledge-projection-hash-mismatch",
        ),
    )


def load_state_fixtures() -> tuple[ProjectionFixture, ...]:
    """Return one neutral artifact fixture for every load-state enum value."""

    surface, knowledge = _projection_bytes()
    mixed = projection_integrity_fixtures()[0]
    malformed = b"{not-json}\n"
    unsupported = knowledge.replace(
        b'"llm-wiki-knowledge/v1"', b'"llm-wiki-knowledge/v2"', 1
    )
    return (
        ProjectionFixture(
            name="valid",
            surface_bytes=surface,
            knowledge_bytes=knowledge,
            committed_surface_hash=_projection_hash(surface),
            committed_knowledge_hash=_projection_hash(knowledge),
            expected_state=KnowledgeLoadState.VALID,
            reason="all-projection-commitments-match",
        ),
        ProjectionFixture(
            name="absent",
            surface_bytes=surface,
            knowledge_bytes=None,
            committed_surface_hash=_projection_hash(surface),
            committed_knowledge_hash=None,
            expected_state=KnowledgeLoadState.ABSENT,
            reason="knowledge-projection-not-present",
        ),
        ProjectionFixture(
            name="absent-declared-artifact-missing",
            surface_bytes=surface,
            knowledge_bytes=None,
            committed_surface_hash=_projection_hash(surface),
            committed_knowledge_hash=fixture_hash("projection:declared-knowledge"),
            expected_state=KnowledgeLoadState.ABSENT,
            reason="declared-artifact-missing",
        ),
        ProjectionFixture(
            name="invalid-malformed",
            surface_bytes=surface,
            knowledge_bytes=malformed,
            committed_surface_hash=_projection_hash(surface),
            committed_knowledge_hash=_projection_hash(malformed),
            expected_state=KnowledgeLoadState.INVALID,
            reason="knowledge-projection-malformed",
        ),
        ProjectionFixture(
            name="invalid-unsupported-version",
            surface_bytes=surface,
            knowledge_bytes=unsupported,
            committed_surface_hash=_projection_hash(surface),
            committed_knowledge_hash=_projection_hash(unsupported),
            expected_state=KnowledgeLoadState.INVALID,
            reason="knowledge-schema-version-unsupported",
        ),
        ProjectionFixture(
            name="invalid-orphan-without-capable-marker",
            surface_bytes=surface,
            knowledge_bytes=knowledge,
            committed_surface_hash=_projection_hash(surface),
            committed_knowledge_hash=None,
            expected_state=KnowledgeLoadState.INVALID,
            reason="knowledge-projection-has-no-commit-marker",
        ),
        mixed,
        ProjectionFixture(
            name="degraded-from-mixed-snapshot",
            surface_bytes=mixed.surface_bytes,
            knowledge_bytes=mixed.knowledge_bytes,
            committed_surface_hash=mixed.committed_surface_hash,
            committed_knowledge_hash=mixed.committed_knowledge_hash,
            expected_state=KnowledgeLoadState.DEGRADED,
            reason="policy-selected-surface-only-fallback-after-mixed-snapshot",
            fallback_selected=True,
            underlying_state=KnowledgeLoadState.MIXED_SNAPSHOT,
        ),
        ProjectionFixture(
            name="degraded-from-invalid",
            surface_bytes=surface,
            knowledge_bytes=malformed,
            committed_surface_hash=_projection_hash(surface),
            committed_knowledge_hash=_projection_hash(malformed),
            expected_state=KnowledgeLoadState.DEGRADED,
            reason="policy-selected-surface-only-fallback-after-invalid",
            fallback_selected=True,
            underlying_state=KnowledgeLoadState.INVALID,
        ),
    )


def normalize_temporary_roots(value: Any, roots: Mapping[Path | str, str]) -> Any:
    """Replace only explicitly supplied roots, recursively and portably."""

    replacements: list[tuple[str, str]] = []
    for root, token in roots.items():
        raw_path = Path(root)
        native_spellings = {
            str(raw_path),
            str(raw_path.absolute()),
            str(raw_path.resolve()),
        }
        spellings = native_spellings | {
            spelling.replace("\\", "/") for spelling in native_spellings
        }
        spellings |= {spelling.replace("/", "\\") for spelling in native_spellings}
        cleaned_spellings = {spelling.rstrip("/\\") for spelling in spellings}
        if not all(cleaned_spellings):
            raise ValueError("temporary fixture roots must be narrower than a root")
        replacements.extend((spelling, token) for spelling in cleaned_spellings)
    replacements.sort(key=lambda item: len(item[0]), reverse=True)

    def normalize(item: Any) -> Any:
        if is_dataclass(item) and not isinstance(item, type):
            return normalize(asdict(item))
        if isinstance(item, Path):
            item = str(item)
        if isinstance(item, str):
            replaced_root = False
            for spelling, token in replacements:
                pattern = re.compile(re.escape(spelling) + r"(?=$|[/\\])")
                if pattern.search(item):
                    replaced_root = True
                item = pattern.sub(
                    lambda _match, replacement=token: replacement,
                    item,
                )
            return item.replace("\\", "/") if replaced_root else item
        if isinstance(item, Mapping):
            return {normalize(key): normalize(child) for key, child in item.items()}
        if isinstance(item, list):
            return [normalize(child) for child in item]
        if isinstance(item, tuple):
            return tuple(normalize(child) for child in item)
        return item

    return normalize(value)


def assert_no_temporary_roots(value: Any, roots: Mapping[Path | str, str]) -> None:
    """Fail when a value still contains a supplied absolute temporary root."""

    root_spellings = {
        spelling.rstrip("/\\")
        for root in roots
        for native in (
            str(Path(root)),
            str(Path(root).absolute()),
            str(Path(root).resolve()),
        )
        for spelling in (native, native.replace("\\", "/"), native.replace("/", "\\"))
    }
    if not all(root_spellings):
        raise ValueError("temporary fixture roots must be narrower than a root")

    def visit(item: Any) -> None:
        if is_dataclass(item) and not isinstance(item, type):
            visit(asdict(item))
            return
        if isinstance(item, Path):
            item = str(item)
        if isinstance(item, str):
            if any(
                re.search(re.escape(spelling) + r"(?=$|[/\\])", item)
                for spelling in root_spellings
            ):
                raise AssertionError(f"temporary root leaked into fixture: {item!r}")
        elif isinstance(item, Mapping):
            for key, child in item.items():
                visit(key)
                visit(child)
        elif isinstance(item, (list, tuple)):
            for child in item:
                visit(child)

    visit(value)


def materialize_fixture_tree(
    fixture: EvaluatedKnowledgeFixture,
    root: Path,
    *,
    consumer: str = "bootstrap",
) -> dict[str, Any]:
    """Write fixture bytes for adapter tests without extracting them again."""

    root = root.resolve()
    wiki_root, source_paths, asset_paths, page_paths = _write_precomputed_tree(
        root=root,
        source_files=fixture.source_files,
        assets=fixture.assets,
        pages=fixture.pages,
    )
    surface_path = wiki_root / SURFACE_INDEX_FILENAME
    knowledge_path = wiki_root / FIXTURE_KNOWLEDGE_FILENAME
    surface_path.write_bytes(fixture.surface_bytes)
    knowledge_path.write_bytes(fixture.knowledge_bytes)
    return {
        "root": root,
        "wiki_root": wiki_root,
        "source_paths": source_paths,
        "asset_paths": asset_paths,
        "page_paths": page_paths,
        "surface_path": surface_path,
        "knowledge_path": knowledge_path,
        "evaluated_inputs": fixture.inputs_for(consumer),
    }


def build_complete_knowledge_payload() -> dict[str, Any]:
    return deepcopy(dict(one_module_two_entities_fixture().knowledge_payload))


def render_knowledge_goldens() -> dict[str, bytes]:
    """Render every committed golden through the production serializer."""

    return {"complete-v1.json": one_module_two_entities_fixture().knowledge_bytes}


__all__ = [
    "FIXTURE_ASSETS",
    "FIXTURE_CONSUMERS",
    "FIXTURE_GIT_REVISION",
    "FIXTURE_KNOWLEDGE_FILENAME",
    "FIXTURE_REPOSITORY_IDENTITY",
    "FIXTURE_SOURCE_PATH",
    "FIXTURE_WIKI_DIR",
    "BundleEnvelopeFixture",
    "EvaluatedKnowledgeFixture",
    "FreshnessFixture",
    "LinkOutcomeFixture",
    "PageFixture",
    "ProjectionFixture",
    "RedactionPolicyFixture",
    "RepositoryIdentityPolicyFixture",
    "assert_no_temporary_roots",
    "build_complete_knowledge_payload",
    "bundle_envelope_fixtures",
    "duplicate_entity_occurrences_fixture",
    "fail_if_extraction_runs",
    "fixture_hash",
    "freshness_fixtures",
    "inert_metadata_fixture",
    "link_outcome_fixtures",
    "load_state_fixtures",
    "materialize_fixture_tree",
    "normalize_temporary_roots",
    "one_module_two_entities_fixture",
    "page_role_fixtures",
    "producer_basis_fixtures",
    "projection_integrity_fixtures",
    "redaction_policy_fixtures",
    "removed_source_fixtures",
    "render_knowledge_goldens",
    "repository_identity_fixtures",
    "source_change_fixtures",
]
