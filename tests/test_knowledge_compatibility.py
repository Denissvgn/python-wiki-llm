"""Cross-consumer compatibility matrix for native knowledge reads."""

from __future__ import annotations

import json
from dataclasses import dataclass, replace
from pathlib import Path

import pytest

from llm_wiki_cli.services.documentation_queries import (
    DocumentationGraphQueryService,
)
from llm_wiki_cli.services.knowledge_artifacts import (
    KNOWLEDGE_INDEX_FILENAME,
    CommitStage,
    build_knowledge_commit_plan,
    commit_knowledge_artifacts,
)
from llm_wiki_cli.services.knowledge_consumption import (
    KnowledgeAvailability,
    KnowledgeReadReason,
    build_knowledge_read_view,
)
from llm_wiki_cli.services.knowledge_evidence import formatted_json_bytes
from llm_wiki_cli.services.knowledge_loader import (
    KnowledgeMismatchPolicy,
    load_knowledge_state,
)
from llm_wiki_cli.services.knowledge_model import (
    KnowledgeLoadState,
    parse_knowledge_index,
    serialize_knowledge_index,
)
from llm_wiki_cli.services.sync_manifest import MANIFEST_FILENAME
from llm_wiki_cli.services.wiki_surface_index import (
    SURFACE_INDEX_FILENAME,
    WIKI_SURFACE_INDEX_SCHEMA_VERSION,
)
from tests.knowledge_fixtures import (
    ProjectionFixture,
    bundle_envelope_fixtures,
    fixture_hash,
    load_state_fixtures,
    one_module_two_entities_fixture,
    projection_integrity_fixtures,
)
from tests.test_knowledge_artifacts import _plan, _surface_variant
from tests.test_knowledge_loader import _write_fixture_pages

USER_LOCATOR = "llm-wiki://entities/User"


@dataclass(frozen=True)
class CompatibilityCase:
    """One materialized variant in the eight-state compatibility matrix."""

    category: str
    variant: str
    expected_load_state: KnowledgeLoadState
    expected_underlying_state: KnowledgeLoadState | None
    expected_availability: KnowledgeAvailability
    expected_reason: KnowledgeReadReason
    expected_issue_codes: frozenset[str]
    serves_knowledge: bool
    projection_fixture: str | None

    @property
    def id(self) -> str:
        if self.category == self.variant:
            return self.category
        return f"{self.category}-{self.variant}"


COMPATIBILITY_CASES = (
    CompatibilityCase(
        category="legacy-manifest-surface-no-knowledge",
        variant="legacy-manifest-surface-no-knowledge",
        expected_load_state=KnowledgeLoadState.ABSENT,
        expected_underlying_state=None,
        expected_availability=KnowledgeAvailability.ABSENT,
        expected_reason=KnowledgeReadReason.ABSENT,
        expected_issue_codes=frozenset(),
        serves_knowledge=False,
        projection_fixture="absent",
    ),
    CompatibilityCase(
        category="valid-committed-knowledge",
        variant="valid-committed-knowledge",
        expected_load_state=KnowledgeLoadState.VALID,
        expected_underlying_state=None,
        expected_availability=KnowledgeAvailability.READY,
        expected_reason=KnowledgeReadReason.READY,
        expected_issue_codes=frozenset(),
        serves_knowledge=True,
        projection_fixture="valid",
    ),
    CompatibilityCase(
        category="manifest-declared-missing-knowledge",
        variant="manifest-declared-missing-knowledge",
        expected_load_state=KnowledgeLoadState.DEGRADED,
        expected_underlying_state=KnowledgeLoadState.INVALID,
        expected_availability=KnowledgeAvailability.DEGRADED,
        expected_reason=KnowledgeReadReason.DEGRADED_INVALID,
        expected_issue_codes=frozenset({"declared-artifact-missing"}),
        serves_knowledge=False,
        projection_fixture="absent-declared-artifact-missing",
    ),
    CompatibilityCase(
        category="malformed-or-schema-invalid-knowledge",
        variant="malformed",
        expected_load_state=KnowledgeLoadState.DEGRADED,
        expected_underlying_state=KnowledgeLoadState.INVALID,
        expected_availability=KnowledgeAvailability.DEGRADED,
        expected_reason=KnowledgeReadReason.DEGRADED_INVALID,
        expected_issue_codes=frozenset({"knowledge-invalid"}),
        serves_knowledge=False,
        projection_fixture="invalid-malformed",
    ),
    CompatibilityCase(
        category="malformed-or-schema-invalid-knowledge",
        variant="schema-invalid",
        expected_load_state=KnowledgeLoadState.DEGRADED,
        expected_underlying_state=KnowledgeLoadState.INVALID,
        expected_availability=KnowledgeAvailability.DEGRADED,
        expected_reason=KnowledgeReadReason.DEGRADED_INVALID,
        expected_issue_codes=frozenset({"knowledge-invalid"}),
        serves_knowledge=False,
        projection_fixture="invalid-schema",
    ),
    CompatibilityCase(
        category="projection-hash-mismatch",
        variant="surface",
        expected_load_state=KnowledgeLoadState.DEGRADED,
        expected_underlying_state=KnowledgeLoadState.MIXED_SNAPSHOT,
        expected_availability=KnowledgeAvailability.DEGRADED,
        expected_reason=KnowledgeReadReason.DEGRADED_MIXED_SNAPSHOT,
        expected_issue_codes=frozenset({"surface-hash-mismatch"}),
        serves_knowledge=False,
        projection_fixture="surface-projection-hash-mismatch",
    ),
    CompatibilityCase(
        category="projection-hash-mismatch",
        variant="knowledge",
        expected_load_state=KnowledgeLoadState.DEGRADED,
        expected_underlying_state=KnowledgeLoadState.MIXED_SNAPSHOT,
        expected_availability=KnowledgeAvailability.DEGRADED,
        expected_reason=KnowledgeReadReason.DEGRADED_MIXED_SNAPSHOT,
        expected_issue_codes=frozenset({"knowledge-hash-mismatch"}),
        serves_knowledge=False,
        projection_fixture="knowledge-projection-hash-mismatch",
    ),
    CompatibilityCase(
        category="projection-hash-mismatch",
        variant="manifest-envelope",
        expected_load_state=KnowledgeLoadState.DEGRADED,
        expected_underlying_state=KnowledgeLoadState.MIXED_SNAPSHOT,
        expected_availability=KnowledgeAvailability.DEGRADED,
        expected_reason=KnowledgeReadReason.DEGRADED_MIXED_SNAPSHOT,
        expected_issue_codes=frozenset({"envelope-hash-mismatch"}),
        serves_knowledge=False,
        projection_fixture="envelope-projection-hash-mismatch",
    ),
    CompatibilityCase(
        category="unsupported-future-schema",
        variant="unsupported-future-schema",
        expected_load_state=KnowledgeLoadState.DEGRADED,
        expected_underlying_state=KnowledgeLoadState.INVALID,
        expected_availability=KnowledgeAvailability.UNSUPPORTED,
        expected_reason=KnowledgeReadReason.UNSUPPORTED_SCHEMA,
        expected_issue_codes=frozenset({"knowledge-schema-version-unsupported"}),
        serves_knowledge=False,
        projection_fixture="invalid-unsupported-version",
    ),
    CompatibilityCase(
        category="interrupted-mixed-projections",
        variant="interrupted-mixed-projections",
        expected_load_state=KnowledgeLoadState.DEGRADED,
        expected_underlying_state=KnowledgeLoadState.MIXED_SNAPSHOT,
        expected_availability=KnowledgeAvailability.DEGRADED,
        expected_reason=KnowledgeReadReason.DEGRADED_MIXED_SNAPSHOT,
        expected_issue_codes=frozenset(
            {
                "surface-hash-mismatch",
                "knowledge-hash-mismatch",
                "envelope-hash-mismatch",
            }
        ),
        serves_knowledge=False,
        projection_fixture="interrupted-before-manifest-commit",
    ),
    CompatibilityCase(
        category="dirty-non-git-unknown-revision",
        variant="dirty",
        expected_load_state=KnowledgeLoadState.VALID,
        expected_underlying_state=None,
        expected_availability=KnowledgeAvailability.READY,
        expected_reason=KnowledgeReadReason.READY,
        expected_issue_codes=frozenset(),
        serves_knowledge=True,
        projection_fixture="valid",
    ),
    CompatibilityCase(
        category="dirty-non-git-unknown-revision",
        variant="non-git",
        expected_load_state=KnowledgeLoadState.VALID,
        expected_underlying_state=None,
        expected_availability=KnowledgeAvailability.READY,
        expected_reason=KnowledgeReadReason.READY,
        expected_issue_codes=frozenset(),
        serves_knowledge=True,
        projection_fixture="valid",
    ),
)

_PROJECTION_FIXTURES = {
    fixture.name: fixture
    for fixture in (
        *load_state_fixtures(),
        *projection_integrity_fixtures(),
    )
}


def _base_plan(root: Path):
    fixture = one_module_two_entities_fixture()
    _write_fixture_pages(root, fixture)
    return fixture, _plan(root, fixture)


def _commit_current(root: Path):
    fixture, plan = _base_plan(root)
    return fixture, plan, commit_knowledge_artifacts(plan)


def _projection_fixture(case: CompatibilityCase) -> ProjectionFixture:
    assert case.projection_fixture is not None
    return _PROJECTION_FIXTURES[case.projection_fixture]


def _materialize_case(root: Path, case: CompatibilityCase):
    projection = _projection_fixture(case)
    if case.category == "legacy-manifest-surface-no-knowledge":
        fixture, plan = _base_plan(root)
        assert projection.surface_bytes == plan.surface_index.content
        assert projection.knowledge_bytes is None
        (root / SURFACE_INDEX_FILENAME).write_bytes(projection.surface_bytes)
        (root / MANIFEST_FILENAME).write_bytes(
            formatted_json_bytes({"version": 4, "sources": {}})
        )
        return fixture

    fixture, plan, committed = _commit_current(root)
    knowledge_path = root / KNOWLEDGE_INDEX_FILENAME

    if case.category == "valid-committed-knowledge":
        assert projection.surface_bytes == plan.surface_index.content
        assert projection.expected_state is KnowledgeLoadState.VALID
        return fixture
    if case.category == "manifest-declared-missing-knowledge":
        assert projection.knowledge_bytes is None
        assert projection.committed_knowledge_hash is not None
        knowledge_path.unlink()
        return fixture
    if case.category == "malformed-or-schema-invalid-knowledge":
        assert projection.knowledge_bytes is not None
        knowledge_path.write_bytes(projection.knowledge_bytes)
        return fixture
    if case.category == "projection-hash-mismatch":
        marker = committed.committed_manifest.artifact_hashes
        assert marker is not None
        marker_fields = {
            "surface": (
                "surface_index_hash",
                projection.committed_surface_hash,
            ),
            "knowledge": (
                "knowledge_index_hash",
                projection.committed_knowledge_hash,
            ),
            "manifest-envelope": (
                "evaluated_envelope_hash",
                projection.committed_envelope_hash,
            ),
        }
        marker_field, mismatched_hash = marker_fields[case.variant]
        assert mismatched_hash is not None
        mismatched = replace(marker, **{marker_field: mismatched_hash})
        replace(
            committed.committed_manifest,
            artifact_hashes=mismatched,
        ).save(root)
        return fixture
    if case.category == "unsupported-future-schema":
        assert projection.knowledge_bytes is not None
        knowledge_path.write_bytes(projection.knowledge_bytes)
        return fixture
    if case.category == "interrupted-mixed-projections":
        assert projection.expected_state is KnowledgeLoadState.MIXED_SNAPSHOT
        surface_bytes, knowledge_bytes = _surface_variant(
            plan,
            lambda surface: surface.__setitem__(
                "source_hash",
                fixture_hash("compatibility:replacement-surface"),
            ),
        )
        replacement = build_knowledge_commit_plan(
            root,
            surface_index_bytes=surface_bytes,
            knowledge_index_bytes=knowledge_bytes,
            manifest=committed.committed_manifest.without_artifact_hashes(),
        )

        def interrupt(stage: CommitStage) -> None:
            if stage is CommitStage.KNOWLEDGE_INDEX_WRITTEN:
                raise RuntimeError("compatibility fixture interrupted")

        with pytest.raises(RuntimeError, match="fixture interrupted"):
            commit_knowledge_artifacts(replacement, fault_injector=interrupt)
        return fixture
    if case.category == "dirty-non-git-unknown-revision":
        assert projection.expected_state is KnowledgeLoadState.VALID
        repositories = {
            item.name: item.bundle["repository"] for item in bundle_envelope_fixtures()
        }
        payload = json.loads(plan.knowledge_index.content)
        payload["bundle"]["repository"] = repositories[case.variant]
        knowledge_bytes = serialize_knowledge_index(
            parse_knowledge_index(payload)
        ).encode("utf-8")
        replacement = build_knowledge_commit_plan(
            root,
            surface_index_bytes=plan.surface_index.content,
            knowledge_index_bytes=knowledge_bytes,
            manifest=committed.committed_manifest.without_artifact_hashes(),
        )
        commit_knowledge_artifacts(replacement)
        return fixture

    raise AssertionError(f"unhandled compatibility category {case.category!r}")


def _surface_coordinates(surface):
    return tuple(
        (
            page["kind"],
            page["id"],
            page["canonical_path"],
            page["mcp_uri"],
        )
        for page in surface["pages"]
    )


def test_compatibility_matrix_defines_all_eight_contract_states():
    assert {case.category for case in COMPATIBILITY_CASES} == {
        "legacy-manifest-surface-no-knowledge",
        "valid-committed-knowledge",
        "manifest-declared-missing-knowledge",
        "malformed-or-schema-invalid-knowledge",
        "projection-hash-mismatch",
        "unsupported-future-schema",
        "interrupted-mixed-projections",
        "dirty-non-git-unknown-revision",
    }
    assert {
        case.variant
        for case in COMPATIBILITY_CASES
        if case.category == "malformed-or-schema-invalid-knowledge"
    } == {"malformed", "schema-invalid"}
    assert {
        case.variant
        for case in COMPATIBILITY_CASES
        if case.category == "projection-hash-mismatch"
    } == {"surface", "knowledge", "manifest-envelope"}
    assert {
        case.variant
        for case in COMPATIBILITY_CASES
        if case.category == "dirty-non-git-unknown-revision"
    } == {"dirty", "non-git"}


@pytest.mark.parametrize(
    "case",
    COMPATIBILITY_CASES,
    ids=lambda case: case.id,
)
def test_loader_read_view_and_query_envelope_share_compatibility_policy(
    tmp_path,
    case,
):
    fixture = _materialize_case(tmp_path, case)

    loaded = load_knowledge_state(
        tmp_path,
        policy=KnowledgeMismatchPolicy.DEGRADED,
    )
    view = build_knowledge_read_view(loaded, snapshot_only=True)
    service = DocumentationGraphQueryService({}, knowledge_view=view)

    assert loaded.status is case.expected_load_state
    assert loaded.underlying_status is case.expected_underlying_state
    assert {issue.code for issue in loaded.issues} == case.expected_issue_codes
    assert view.availability is case.expected_availability
    assert view.reason is case.expected_reason
    assert view.load_state is case.expected_load_state
    assert view.underlying_load_state is case.expected_underlying_state
    assert view.projection_findings == loaded.issues
    assert view.freshness is None

    assert loaded.surface is not None
    assert loaded.surface["schema_version"] == WIKI_SURFACE_INDEX_SCHEMA_VERSION
    assert WIKI_SURFACE_INDEX_SCHEMA_VERSION == "llm-wiki-surface-index/v1"
    assert _surface_coordinates(loaded.surface) == _surface_coordinates(
        fixture.surface_payload
    )
    for page in fixture.pages:
        assert (tmp_path / page.canonical_path).read_text(
            encoding="utf-8"
        ) == page.content

    concept = service.get_concept(USER_LOCATOR)
    related = service.related_concepts(USER_LOCATOR)
    evidence = service.explain_evidence(USER_LOCATOR)
    expected_envelope = {
        "availability": case.expected_availability.value,
        "reason": case.expected_reason.value,
        "freshness": "unevaluated (snapshot-only read)",
        "freshness_evaluated": False,
    }
    assert concept["knowledge"] == expected_envelope
    assert related["knowledge"] == expected_envelope
    assert evidence["knowledge"] == expected_envelope

    if case.serves_knowledge:
        assert loaded.knowledge is not None
        assert view.knowledge is loaded.knowledge
        assert view.counts is not None
        assert concept["found"] is True
        assert concept["concept"]["locator"] == USER_LOCATOR
        assert concept["concept"]["mcp_uri"] == USER_LOCATOR
        assert concept["concept"]["freshness"] == {
            "state": None,
            "reason": "not-evaluated",
            "live_comparison_performed": False,
        }
        assert related["found"] is True
        assert evidence["found"] is True
        assert evidence["evidence"] is not None
    else:
        assert loaded.knowledge is None
        assert view.knowledge is None
        assert view.counts is None
        assert concept["found"] is False
        assert concept["concept"] is None
        assert concept["matches"] == []
        assert related["found"] is False
        assert related["relationships"] == []
        assert related["related_concepts"] == []
        assert evidence["found"] is False
        assert evidence["evidence"] is None


@pytest.mark.parametrize("repository_state", ["dirty", "non-git"])
def test_dirty_and_unknown_revision_evidence_remains_valid_but_not_optimistic(
    tmp_path,
    repository_state,
):
    case = next(
        item
        for item in COMPATIBILITY_CASES
        if item.category == "dirty-non-git-unknown-revision"
        and item.variant == repository_state
    )
    _materialize_case(tmp_path, case)

    view = build_knowledge_read_view(
        load_knowledge_state(tmp_path),
        snapshot_only=True,
    )
    assert view.knowledge is not None
    repository = view.knowledge.bundle.repository

    if repository_state == "dirty":
        assert repository.working_tree.value == "dirty"
        assert repository.evaluated_revision.startswith("git:")
    else:
        assert repository.identity == "unknown"
        assert repository.evaluated_revision == "unknown"
        assert repository.working_tree.value == "unknown"

    concept = DocumentationGraphQueryService(
        {},
        knowledge_view=view,
    ).get_concept(USER_LOCATOR)
    assert concept["knowledge"]["availability"] == "ready"
    assert concept["knowledge"]["freshness_evaluated"] is False
    assert concept["concept"]["freshness"]["state"] is None


def test_valid_deterministic_artifacts_have_no_routine_timestamp_fields(
    tmp_path,
):
    _commit_current(tmp_path)
    forbidden = {
        "created_at",
        "generated_at",
        "mtime",
        "mtime_ns",
        "timestamp",
        "updated_at",
    }

    def mapping_keys(value):
        if isinstance(value, dict):
            yield from value
            for item in value.values():
                yield from mapping_keys(item)
        elif isinstance(value, list):
            for item in value:
                yield from mapping_keys(item)

    for filename in (
        SURFACE_INDEX_FILENAME,
        KNOWLEDGE_INDEX_FILENAME,
        MANIFEST_FILENAME,
    ):
        payload = json.loads((tmp_path / filename).read_bytes())
        assert forbidden.isdisjoint(mapping_keys(payload))
