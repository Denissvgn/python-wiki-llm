"""Validated loader and explicit degraded-fallback tests."""

from __future__ import annotations

import json
from dataclasses import replace

import pytest

from llm_wiki_cli.services.io import write_bytes_atomic
from llm_wiki_cli.services.knowledge_artifacts import (
    KNOWLEDGE_INDEX_FILENAME,
    CommitStage,
    build_knowledge_commit_plan,
    commit_knowledge_artifacts,
)
from llm_wiki_cli.services.knowledge_evidence import (
    canonical_json_text,
    formatted_json_bytes,
    sha256_bytes,
)
from llm_wiki_cli.services.knowledge_loader import (
    KnowledgeMismatchPolicy,
    KnowledgeStateLoadError,
    load_knowledge_state,
)
from llm_wiki_cli.services.knowledge_model import KnowledgeLoadState
from llm_wiki_cli.services.contracts import (
    SECTION_OWNERSHIP_EXTENSION_KEY,
    TYPED_GRAPH_EXTENSION_KEY,
)
from llm_wiki_cli.services.sync_manifest import (
    MANIFEST_FILENAME,
    ManifestEvidenceBaseline,
)
from llm_wiki_cli.services.wiki_surface_index import SURFACE_INDEX_FILENAME
from tests.knowledge_fixtures import one_module_two_entities_fixture
from tests.test_knowledge_artifacts import _plan, _surface_variant
from tests.test_knowledge_generation import _planner_inputs
from llm_wiki_cli.services.knowledge_generation import (
    build_knowledge_generation_plan,
)
from llm_wiki_cli.services.knowledge_graph import relationship_edge_key
from llm_wiki_cli.services.knowledge_model import parse_knowledge_index


def _write_fixture_pages(root, fixture, *, crlf: bool = False):
    for page in fixture.pages:
        path = root / page.canonical_path
        path.parent.mkdir(parents=True, exist_ok=True)
        content = page.content.replace("\n", "\r\n") if crlf else page.content
        path.write_text(content, encoding="utf-8", newline="")


def _committed_state(root):
    fixture = one_module_two_entities_fixture()
    _write_fixture_pages(root, fixture)
    plan = _plan(root, fixture)
    result = commit_knowledge_artifacts(plan)
    return fixture, plan, result


def _committed_m3_state(root):
    inputs = _planner_inputs(root)
    _write_fixture_pages(root, one_module_two_entities_fixture())
    plan = build_knowledge_generation_plan(inputs)
    result = commit_knowledge_artifacts(plan)
    return plan, result


def test_valid_state_returns_all_validated_components(tmp_path):
    _fixture, plan, result = _committed_state(tmp_path)

    loaded = load_knowledge_state(tmp_path)

    assert loaded.status is KnowledgeLoadState.VALID
    assert loaded.knowledge is not None
    assert loaded.surface is not None
    assert loaded.manifest_basis == result.committed_manifest
    assert loaded.issues == ()
    assert loaded.knowledge.bundle.snapshot.surface_index_hash == (
        plan.surface_index.content_hash
    )


def test_absent_knowledge_returns_surface_only_without_fabricated_fields(tmp_path):
    fixture = one_module_two_entities_fixture()
    _write_fixture_pages(tmp_path, fixture)
    plan = _plan(tmp_path, fixture)
    write_bytes_atomic(tmp_path / SURFACE_INDEX_FILENAME, plan.surface_index.content)

    loaded = load_knowledge_state(tmp_path)

    assert loaded.status is KnowledgeLoadState.ABSENT
    assert loaded.surface is not None
    assert loaded.knowledge is None
    assert loaded.manifest_basis is None
    assert {issue.code for issue in loaded.issues} == {"manifest-absent"}


def test_declared_but_missing_knowledge_is_invalid_and_can_degrade(tmp_path):
    _committed_state(tmp_path)
    (tmp_path / KNOWLEDGE_INDEX_FILENAME).unlink()

    with pytest.raises(KnowledgeStateLoadError) as exc_info:
        load_knowledge_state(tmp_path)

    assert exc_info.value.status is KnowledgeLoadState.INVALID
    assert any(
        issue.code == "declared-artifact-missing" for issue in exc_info.value.issues
    )

    degraded = load_knowledge_state(
        tmp_path,
        policy=KnowledgeMismatchPolicy.DEGRADED,
    )
    assert degraded.status is KnowledgeLoadState.DEGRADED
    assert degraded.underlying_status is KnowledgeLoadState.INVALID
    assert degraded.surface is not None
    assert degraded.knowledge is None


def test_deleting_knowledge_then_manifest_transitions_invalid_to_absent(
    tmp_path,
):
    _committed_state(tmp_path)
    (tmp_path / KNOWLEDGE_INDEX_FILENAME).unlink()

    with pytest.raises(KnowledgeStateLoadError) as exc_info:
        load_knowledge_state(tmp_path)

    assert exc_info.value.status is KnowledgeLoadState.INVALID
    assert any(
        issue.code == "declared-artifact-missing" for issue in exc_info.value.issues
    )

    (tmp_path / MANIFEST_FILENAME).unlink()
    loaded = load_knowledge_state(tmp_path)

    assert loaded.status is KnowledgeLoadState.ABSENT
    assert loaded.surface is not None
    assert loaded.knowledge is None
    assert loaded.manifest_basis is None
    assert {issue.code for issue in loaded.issues} == {"manifest-absent"}


@pytest.mark.parametrize(
    "invalid_bytes",
    [
        b"{not-json\n",
        b'{"schema_version":"future","schema_version":"other"}\n',
    ],
)
def test_malformed_or_duplicate_key_knowledge_never_loads(
    tmp_path,
    invalid_bytes,
):
    _committed_state(tmp_path)
    (tmp_path / KNOWLEDGE_INDEX_FILENAME).write_bytes(invalid_bytes)

    with pytest.raises(KnowledgeStateLoadError) as exc_info:
        load_knowledge_state(tmp_path)

    assert exc_info.value.status is KnowledgeLoadState.INVALID
    assert any(issue.code == "knowledge-invalid" for issue in exc_info.value.issues)


def test_unsupported_knowledge_version_is_invalid(tmp_path):
    _fixture, plan, _result = _committed_state(tmp_path)
    payload = json.loads(plan.knowledge_index.content)
    payload["schema_version"] = "llm-wiki-knowledge/v999"
    (tmp_path / KNOWLEDGE_INDEX_FILENAME).write_bytes(formatted_json_bytes(payload))

    with pytest.raises(KnowledgeStateLoadError) as exc_info:
        load_knowledge_state(tmp_path)

    assert exc_info.value.status is KnowledgeLoadState.INVALID
    assert any(
        issue.code == "knowledge-schema-version-unsupported"
        and issue.field == "knowledge_index_bytes.schema_version"
        for issue in exc_info.value.issues
    )


@pytest.mark.parametrize(
    "schema_version",
    [
        999,
        "not-a-version",
        "llm-wiki-knowledge/v0",
    ],
)
def test_malformed_schema_version_is_invalid_but_not_unsupported(
    tmp_path,
    schema_version,
):
    _fixture, plan, _result = _committed_state(tmp_path)
    payload = json.loads(plan.knowledge_index.content)
    payload["schema_version"] = schema_version
    (tmp_path / KNOWLEDGE_INDEX_FILENAME).write_bytes(formatted_json_bytes(payload))

    with pytest.raises(KnowledgeStateLoadError) as exc_info:
        load_knowledge_state(tmp_path)

    assert exc_info.value.status is KnowledgeLoadState.INVALID
    assert any(
        issue.code == "knowledge-invalid"
        and issue.field == "knowledge_index_bytes.schema_version"
        for issue in exc_info.value.issues
    )


@pytest.mark.parametrize("manifest_mode", ["missing", "markerless"])
def test_present_knowledge_requires_a_capable_manifest(tmp_path, manifest_mode):
    _fixture, _plan_value, result = _committed_state(tmp_path)
    if manifest_mode == "missing":
        (tmp_path / MANIFEST_FILENAME).unlink()
    else:
        result.committed_manifest.without_artifact_hashes().save(tmp_path)

    with pytest.raises(KnowledgeStateLoadError) as exc_info:
        load_knowledge_state(tmp_path)

    assert exc_info.value.status is KnowledgeLoadState.INVALID
    assert any(
        issue.code in {"manifest-absent", "manifest-marker-missing"}
        for issue in exc_info.value.issues
    )


@pytest.mark.parametrize("knowledge_present", [True, False])
def test_future_manifest_version_is_unsupported_and_never_absent(
    tmp_path,
    knowledge_present,
):
    _fixture, _plan_value, _result = _committed_state(tmp_path)
    manifest_path = tmp_path / MANIFEST_FILENAME
    payload = json.loads(manifest_path.read_bytes())
    payload["version"] = 999
    manifest_path.write_bytes(formatted_json_bytes(payload))
    if not knowledge_present:
        (tmp_path / KNOWLEDGE_INDEX_FILENAME).unlink()

    with pytest.raises(KnowledgeStateLoadError) as exc_info:
        load_knowledge_state(tmp_path)

    assert exc_info.value.status is KnowledgeLoadState.INVALID
    assert exc_info.value.status is not KnowledgeLoadState.ABSENT
    assert any(
        issue.code == "manifest-version-unsupported"
        and issue.artifact_path == MANIFEST_FILENAME
        and issue.field == "version"
        for issue in exc_info.value.issues
    )


@pytest.mark.parametrize("manifest_case", ["malformed-json", "noninteger-version"])
def test_invalid_manifest_without_knowledge_is_not_absent(
    tmp_path,
    manifest_case,
):
    _fixture, _plan_value, _result = _committed_state(tmp_path)
    manifest_path = tmp_path / MANIFEST_FILENAME
    if manifest_case == "malformed-json":
        manifest_path.write_bytes(b"{not-json\n")
    else:
        payload = json.loads(manifest_path.read_bytes())
        payload["version"] = "5"
        manifest_path.write_bytes(formatted_json_bytes(payload))
    (tmp_path / KNOWLEDGE_INDEX_FILENAME).unlink()

    with pytest.raises(KnowledgeStateLoadError) as exc_info:
        load_knowledge_state(tmp_path)

    assert exc_info.value.status is KnowledgeLoadState.INVALID
    assert exc_info.value.status is not KnowledgeLoadState.ABSENT
    assert any(
        issue.code == "manifest-invalid"
        and issue.artifact_path == MANIFEST_FILENAME
        for issue in exc_info.value.issues
    )
    assert all(
        issue.code != "manifest-version-unsupported"
        for issue in exc_info.value.issues
    )


@pytest.mark.parametrize(
    "invalid_manifest",
    [
        b'{"version":5,"version":5}\n',
        b'{"version":NaN}\n',
    ],
)
def test_loader_rejects_non_strict_manifest_json(tmp_path, invalid_manifest):
    _committed_state(tmp_path)
    (tmp_path / MANIFEST_FILENAME).write_bytes(invalid_manifest)

    with pytest.raises(KnowledgeStateLoadError) as exc_info:
        load_knowledge_state(tmp_path)

    assert exc_info.value.status is KnowledgeLoadState.INVALID
    assert any(
        issue.code == "manifest-invalid" and issue.artifact_path == MANIFEST_FILENAME
        for issue in exc_info.value.issues
    )


@pytest.mark.parametrize(
    ("field", "issue_code"),
    [
        ("surface_index_hash", "surface-hash-mismatch"),
        ("knowledge_index_hash", "knowledge-hash-mismatch"),
        ("evaluated_envelope_hash", "envelope-hash-mismatch"),
    ],
)
def test_manifest_marker_mismatches_are_mixed_snapshots(
    tmp_path,
    field,
    issue_code,
):
    _fixture, _plan_value, result = _committed_state(tmp_path)
    marker = result.committed_manifest.artifact_hashes
    assert marker is not None
    changed = replace(marker, **{field: "sha256:" + "f" * 64})
    replace(result.committed_manifest, artifact_hashes=changed).save(tmp_path)

    with pytest.raises(KnowledgeStateLoadError) as exc_info:
        load_knowledge_state(tmp_path)

    assert exc_info.value.status is KnowledgeLoadState.MIXED_SNAPSHOT
    assert any(issue.code == issue_code for issue in exc_info.value.issues)


def test_valid_graph_from_another_inventory_is_a_mixed_snapshot(tmp_path):
    plan, result = _committed_m3_state(tmp_path)
    payload = json.loads(plan.knowledge_index.content)
    graph = payload["extensions"][TYPED_GRAPH_EXTENSION_KEY]
    graph["input_hashes"]["inventory"] = "sha256:" + ("f" * 64)
    graph["input_hashes"]["aggregate"] = sha256_bytes(
        canonical_json_text(
            {
                key: value
                for key, value in graph["input_hashes"].items()
                if key != "aggregate"
            }
        ).encode("utf-8")
    )
    knowledge_bytes = formatted_json_bytes(payload)
    write_bytes_atomic(tmp_path / KNOWLEDGE_INDEX_FILENAME, knowledge_bytes)
    marker = result.committed_manifest.artifact_hashes
    assert marker is not None
    replace(
        result.committed_manifest,
        artifact_hashes=replace(
            marker,
            knowledge_index_hash=sha256_bytes(knowledge_bytes),
        ),
    ).save(tmp_path)

    with pytest.raises(KnowledgeStateLoadError) as exc_info:
        load_knowledge_state(tmp_path)

    assert exc_info.value.status is KnowledgeLoadState.MIXED_SNAPSHOT
    assert any(
        issue.code == "artifact-parity-mismatch"
        and TYPED_GRAPH_EXTENSION_KEY in (issue.field or "")
        for issue in exc_info.value.issues
    )


def test_valid_graph_with_foreign_concept_reference_is_a_mixed_snapshot(tmp_path):
    plan, result = _committed_m3_state(tmp_path)
    payload = json.loads(plan.knowledge_index.content)
    graph = payload["extensions"][TYPED_GRAPH_EXTENSION_KEY]
    edge = next(edge for edge in graph["edges"] if edge["kind"] == "contains")
    edge["target"] = {
        "kind": "concept",
        "locator": "llm-wiki://entities/foreign",
    }
    edge["key"] = relationship_edge_key(edge)
    graph["edges"].sort(key=lambda item: item["key"])

    # The extension remains intrinsically valid; only its references disagree
    # with the enclosing knowledge snapshot.
    parse_knowledge_index(payload)
    knowledge_bytes = formatted_json_bytes(payload)
    write_bytes_atomic(tmp_path / KNOWLEDGE_INDEX_FILENAME, knowledge_bytes)
    marker = result.committed_manifest.artifact_hashes
    assert marker is not None
    replace(
        result.committed_manifest,
        artifact_hashes=replace(
            marker,
            knowledge_index_hash=sha256_bytes(knowledge_bytes),
        ),
    ).save(tmp_path)

    with pytest.raises(KnowledgeStateLoadError) as exc_info:
        load_knowledge_state(tmp_path)

    assert exc_info.value.status is KnowledgeLoadState.MIXED_SNAPSHOT
    assert any(
        issue.code == "artifact-parity-mismatch"
        and TYPED_GRAPH_EXTENSION_KEY in (issue.field or "")
        for issue in exc_info.value.issues
    )


def test_malformed_typed_graph_is_invalid_even_with_matching_marker(tmp_path):
    plan, result = _committed_m3_state(tmp_path)
    payload = json.loads(plan.knowledge_index.content)
    graph = payload["extensions"][TYPED_GRAPH_EXTENSION_KEY]
    graph["edges"][0]["coverage"]["omitted"] = 99
    knowledge_bytes = formatted_json_bytes(payload)
    write_bytes_atomic(tmp_path / KNOWLEDGE_INDEX_FILENAME, knowledge_bytes)
    marker = result.committed_manifest.artifact_hashes
    assert marker is not None
    replace(
        result.committed_manifest,
        artifact_hashes=replace(
            marker,
            knowledge_index_hash=sha256_bytes(knowledge_bytes),
        ),
    ).save(tmp_path)

    with pytest.raises(KnowledgeStateLoadError) as exc_info:
        load_knowledge_state(tmp_path)

    assert exc_info.value.status is KnowledgeLoadState.INVALID
    assert any(
        issue.code == "knowledge-invalid"
        and TYPED_GRAPH_EXTENSION_KEY in (issue.field or "")
        for issue in exc_info.value.issues
    )


def test_valid_section_ownership_from_another_snapshot_is_mixed(tmp_path):
    plan, result = _committed_m3_state(tmp_path)
    payload = json.loads(plan.knowledge_index.content)
    sections = payload["extensions"][SECTION_OWNERSHIP_EXTENSION_KEY]
    sections["pages"][0]["source_hash"] = "sha256:" + ("f" * 64)
    knowledge_bytes = formatted_json_bytes(payload)
    write_bytes_atomic(tmp_path / KNOWLEDGE_INDEX_FILENAME, knowledge_bytes)
    marker = result.committed_manifest.artifact_hashes
    assert marker is not None
    replace(
        result.committed_manifest,
        artifact_hashes=replace(
            marker,
            knowledge_index_hash=sha256_bytes(knowledge_bytes),
        ),
    ).save(tmp_path)

    with pytest.raises(KnowledgeStateLoadError) as exc_info:
        load_knowledge_state(tmp_path)

    assert exc_info.value.status is KnowledgeLoadState.MIXED_SNAPSHOT
    assert any(
        issue.code == "artifact-parity-mismatch"
        and SECTION_OWNERSHIP_EXTENSION_KEY in (issue.field or "")
        for issue in exc_info.value.issues
    )


def test_malformed_section_ownership_is_invalid_with_matching_marker(tmp_path):
    plan, result = _committed_m3_state(tmp_path)
    payload = json.loads(plan.knowledge_index.content)
    sections = payload["extensions"][SECTION_OWNERSHIP_EXTENSION_KEY]
    sections["pages"][0]["sections"][0]["occurrence"] = 0
    knowledge_bytes = formatted_json_bytes(payload)
    write_bytes_atomic(tmp_path / KNOWLEDGE_INDEX_FILENAME, knowledge_bytes)
    marker = result.committed_manifest.artifact_hashes
    assert marker is not None
    replace(
        result.committed_manifest,
        artifact_hashes=replace(
            marker,
            knowledge_index_hash=sha256_bytes(knowledge_bytes),
        ),
    ).save(tmp_path)

    with pytest.raises(KnowledgeStateLoadError) as exc_info:
        load_knowledge_state(tmp_path)

    assert exc_info.value.status is KnowledgeLoadState.INVALID
    assert any(
        issue.code == "knowledge-invalid"
        and SECTION_OWNERSHIP_EXTENSION_KEY in (issue.field or "")
        for issue in exc_info.value.issues
    )


@pytest.mark.parametrize(
    ("failure_stage", "expected_issue_codes"),
    [
        (
            CommitStage.SURFACE_INDEX_WRITTEN,
            {"artifact-parity-mismatch"},
        ),
        (
            CommitStage.KNOWLEDGE_INDEX_WRITTEN,
            {
                "surface-hash-mismatch",
                "knowledge-hash-mismatch",
                "envelope-hash-mismatch",
            },
        ),
    ],
)
def test_loader_rejects_projection_set_left_by_interrupted_replacement(
    tmp_path,
    failure_stage,
    expected_issue_codes,
):
    _fixture, initial_plan, initial_result = _committed_state(tmp_path)
    surface_bytes, knowledge_bytes = _surface_variant(
        initial_plan,
        lambda surface: surface.__setitem__(
            "source_hash",
            "sha256:" + "f" * 64,
        ),
    )
    replacement_plan = build_knowledge_commit_plan(
        tmp_path,
        surface_index_bytes=surface_bytes,
        knowledge_index_bytes=knowledge_bytes,
        manifest=initial_result.committed_manifest.without_artifact_hashes(),
    )

    def interrupt(stage):
        if stage is failure_stage:
            raise RuntimeError(f"interrupted after {stage.value}")

    with pytest.raises(RuntimeError, match="interrupted after"):
        commit_knowledge_artifacts(
            replacement_plan,
            fault_injector=interrupt,
        )

    with pytest.raises(KnowledgeStateLoadError) as exc_info:
        load_knowledge_state(tmp_path)

    assert exc_info.value.status is KnowledgeLoadState.MIXED_SNAPSHOT
    issue_codes = {issue.code for issue in exc_info.value.issues}
    assert expected_issue_codes <= issue_codes

    degraded = load_knowledge_state(
        tmp_path,
        policy=KnowledgeMismatchPolicy.DEGRADED,
    )
    assert degraded.status is KnowledgeLoadState.DEGRADED
    assert degraded.underlying_status is KnowledgeLoadState.MIXED_SNAPSHOT
    assert degraded.surface is not None
    assert degraded.knowledge is None


def test_loader_accepts_complete_commit_when_caller_faults_after_manifest(tmp_path):
    fixture = one_module_two_entities_fixture()
    _write_fixture_pages(tmp_path, fixture)
    plan = _plan(tmp_path, fixture)

    def interrupt(stage):
        if stage is CommitStage.MANIFEST_WRITTEN:
            raise RuntimeError("interrupted after manifest")

    with pytest.raises(RuntimeError, match="after manifest"):
        commit_knowledge_artifacts(plan, fault_injector=interrupt)

    loaded = load_knowledge_state(tmp_path)
    assert loaded.status is KnowledgeLoadState.VALID
    assert loaded.knowledge is not None


def test_current_markdown_content_mismatch_is_mixed_but_surface_can_degrade(
    tmp_path,
):
    fixture, _plan_value, _result = _committed_state(tmp_path)
    changed = tmp_path / fixture.pages[0].canonical_path
    changed.write_text(changed.read_text(encoding="utf-8") + "\nchanged\n")

    degraded = load_knowledge_state(
        tmp_path,
        policy=KnowledgeMismatchPolicy.DEGRADED,
    )

    assert degraded.status is KnowledgeLoadState.DEGRADED
    assert degraded.underlying_status is KnowledgeLoadState.MIXED_SNAPSHOT
    assert degraded.knowledge is None
    assert any(issue.code == "markdown-snapshot-mismatch" for issue in degraded.issues)


def test_markdown_snapshot_normalizes_crlf(tmp_path):
    fixture = one_module_two_entities_fixture()
    _write_fixture_pages(tmp_path, fixture, crlf=True)
    commit_knowledge_artifacts(_plan(tmp_path, fixture))

    loaded = load_knowledge_state(tmp_path)

    assert loaded.status is KnowledgeLoadState.VALID


def test_page_parity_mismatch_refuses_even_degraded_surface(tmp_path):
    _committed_state(tmp_path)
    extra = tmp_path / "guides" / "extra.md"
    extra.parent.mkdir(parents=True)
    extra.write_text("# Extra\n", encoding="utf-8")

    with pytest.raises(KnowledgeStateLoadError) as exc_info:
        load_knowledge_state(
            tmp_path,
            policy=KnowledgeMismatchPolicy.DEGRADED,
        )

    assert exc_info.value.status is KnowledgeLoadState.MIXED_SNAPSHOT
    assert any(issue.code == "page-parity-mismatch" for issue in exc_info.value.issues)


def test_manifest_evidence_disagreement_is_a_mixed_snapshot(tmp_path):
    _fixture, _plan_value, result = _committed_state(tmp_path)
    manifest = result.committed_manifest
    path = min(manifest.evidence_baselines)
    baseline = manifest.evidence_baselines[path]
    assert baseline.basis is not None
    changed_basis = replace(
        baseline.basis,
        concept_observation_hash="sha256:" + "a" * 64,
    )
    changed_baselines = dict(manifest.evidence_baselines)
    changed_baselines[path] = ManifestEvidenceBaseline.from_basis(changed_basis)
    replace(manifest, evidence_baselines=changed_baselines).save(tmp_path)

    with pytest.raises(KnowledgeStateLoadError) as exc_info:
        load_knowledge_state(tmp_path)

    assert exc_info.value.status is KnowledgeLoadState.MIXED_SNAPSHOT
    assert any(
        issue.code == "artifact-parity-mismatch" for issue in exc_info.value.issues
    )


def test_invalid_surface_cannot_be_selected_as_degraded_fallback(tmp_path):
    _fixture, plan, _result = _committed_state(tmp_path)
    surface = json.loads(plan.surface_index.content)
    surface["pages"][0]["source_path"] = "/private/secret"
    (tmp_path / SURFACE_INDEX_FILENAME).write_bytes(formatted_json_bytes(surface))

    with pytest.raises(KnowledgeStateLoadError) as exc_info:
        load_knowledge_state(
            tmp_path,
            policy=KnowledgeMismatchPolicy.DEGRADED,
        )

    assert exc_info.value.status is KnowledgeLoadState.INVALID
    assert any(issue.code == "surface-invalid" for issue in exc_info.value.issues)


def test_future_surface_schema_version_is_unsupported(tmp_path):
    _fixture, plan, _result = _committed_state(tmp_path)
    surface = json.loads(plan.surface_index.content)
    surface["schema_version"] = "llm-wiki-surface-index/v999"
    (tmp_path / SURFACE_INDEX_FILENAME).write_bytes(formatted_json_bytes(surface))

    with pytest.raises(KnowledgeStateLoadError) as exc_info:
        load_knowledge_state(tmp_path)

    assert exc_info.value.status is KnowledgeLoadState.INVALID
    assert any(
        issue.code == "surface-schema-version-unsupported"
        and issue.artifact_path == SURFACE_INDEX_FILENAME
        and issue.field == "surface_index.schema_version"
        for issue in exc_info.value.issues
    )


@pytest.mark.parametrize(
    "schema_case",
    ["nonstring", "missing", "unrecognized", "zero"],
)
def test_malformed_surface_schema_is_invalid_not_unsupported(
    tmp_path,
    schema_case,
):
    _fixture, plan, _result = _committed_state(tmp_path)
    surface = json.loads(plan.surface_index.content)
    if schema_case == "nonstring":
        surface["schema_version"] = 999
    elif schema_case == "missing":
        surface.pop("schema_version")
    elif schema_case == "unrecognized":
        surface["schema_version"] = "not-a-version"
    else:
        surface["schema_version"] = "llm-wiki-surface-index/v0"
    (tmp_path / SURFACE_INDEX_FILENAME).write_bytes(formatted_json_bytes(surface))

    with pytest.raises(KnowledgeStateLoadError) as exc_info:
        load_knowledge_state(tmp_path)

    assert exc_info.value.status is KnowledgeLoadState.INVALID
    assert any(
        issue.code == "surface-invalid"
        and issue.artifact_path == SURFACE_INDEX_FILENAME
        and issue.field == "surface_index.schema_version"
        for issue in exc_info.value.issues
    )
    assert all(
        issue.code != "surface-schema-version-unsupported"
        for issue in exc_info.value.issues
    )


def test_rebuild_policy_calls_callback_once_and_revalidates(tmp_path):
    fixture, plan, _result = _committed_state(tmp_path)
    (tmp_path / KNOWLEDGE_INDEX_FILENAME).write_bytes(b"{broken\n")
    calls = []

    def rebuild(issues):
        calls.append(issues)
        replacement = build_knowledge_commit_plan(
            tmp_path,
            surface_index_bytes=plan.surface_index.content,
            knowledge_index_bytes=plan.knowledge_index.content,
            manifest=plan.committed_manifest.without_artifact_hashes(),
        )
        commit_knowledge_artifacts(replacement)

    loaded = load_knowledge_state(
        tmp_path,
        policy=KnowledgeMismatchPolicy.REBUILD,
        rebuild_callback=rebuild,
    )

    assert loaded.status is KnowledgeLoadState.VALID
    assert loaded.rebuilt
    assert len(calls) == 1
    assert fixture.pages


def test_failed_rebuild_is_not_retried(tmp_path):
    _committed_state(tmp_path)
    (tmp_path / KNOWLEDGE_INDEX_FILENAME).write_bytes(b"{broken\n")
    calls = []

    def no_repair(issues):
        calls.append(issues)

    with pytest.raises(KnowledgeStateLoadError):
        load_knowledge_state(
            tmp_path,
            policy=KnowledgeMismatchPolicy.REBUILD,
            rebuild_callback=no_repair,
        )

    assert len(calls) == 1


def test_errors_and_issues_never_include_checkout_path(tmp_path):
    _committed_state(tmp_path)
    (tmp_path / KNOWLEDGE_INDEX_FILENAME).write_bytes(b"{broken\n")

    with pytest.raises(KnowledgeStateLoadError) as exc_info:
        load_knowledge_state(tmp_path)

    assert str(tmp_path) not in str(exc_info.value)
    assert all(
        issue.artifact_path
        in {
            SURFACE_INDEX_FILENAME,
            KNOWLEDGE_INDEX_FILENAME,
            MANIFEST_FILENAME,
        }
        for issue in exc_info.value.issues
    )


def test_deleting_knowledge_and_commit_marker_restores_surface_only_behavior(
    tmp_path,
):
    _fixture, _plan_value, result = _committed_state(tmp_path)
    (tmp_path / KNOWLEDGE_INDEX_FILENAME).unlink()
    result.committed_manifest.without_artifact_hashes().save(tmp_path)

    loaded = load_knowledge_state(tmp_path)

    assert loaded.status is KnowledgeLoadState.ABSENT
    assert loaded.surface is not None
    assert loaded.knowledge is None
