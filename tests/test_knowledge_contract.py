"""Golden-contract and reusable policy fixtures for KNOW-003 and KNOW-004."""

from __future__ import annotations

import hashlib
import json
import socket
import subprocess
import sys
import urllib.request
from copy import deepcopy
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from llm_wiki_cli.services.knowledge_model import (
    REPOSITORY_IDENTITY_SOURCE_EXTENSION,
    ComputedFreshness,
    KnowledgeLoadState,
    KnowledgeProjectionProfile,
    RepositoryIdentitySource,
    knowledge_index_to_payload,
    load_knowledge_schema,
    parse_knowledge_index,
    repository_identities_match,
)
from llm_wiki_cli.services.wiki_media import iter_markdown_link_targets
from llm_wiki_cli.services.wiki_surface import (
    PageKind,
    SurfaceRole,
    canonical_path,
    iter_page_kinds,
)
from llm_wiki_cli.services.wiki_surface_index import build_surface_index
from tests import regenerate_knowledge_goldens
from tests.knowledge_fixtures import (
    FIXTURE_CONSUMERS,
    FIXTURE_SOURCE_PATH,
    assert_no_temporary_roots,
    build_complete_knowledge_payload,
    bundle_envelope_fixtures,
    duplicate_entity_occurrences_fixture,
    fail_if_extraction_runs,
    freshness_fixtures,
    inert_metadata_fixture,
    link_outcome_fixtures,
    load_state_fixtures,
    materialize_fixture_tree,
    normalize_temporary_roots,
    one_module_two_entities_fixture,
    page_role_fixtures,
    producer_basis_fixtures,
    projection_integrity_fixtures,
    redaction_policy_fixtures,
    removed_source_fixtures,
    render_knowledge_goldens,
    repository_identity_fixtures,
    source_change_fixtures,
)
from tests.regenerate_knowledge_goldens import main as check_or_regenerate_goldens

GOLDEN_ROOT = Path(__file__).parent / "fixtures" / "knowledge"


def _sha256(value: bytes) -> str:
    return "sha256:" + hashlib.sha256(value).hexdigest()


def _tree_sha256(files: dict[str, str]) -> str:
    encoded = json.dumps(
        files,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return _sha256(encoded)


def _walk_strings(value: object) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        return [
            text
            for key, child in value.items()
            for text in _walk_strings(key) + _walk_strings(child)
        ]
    if isinstance(value, (list, tuple)):
        return [text for child in value for text in _walk_strings(child)]
    return []


def _walk_keys(value: object) -> set[str]:
    if isinstance(value, dict):
        return set(value) | {
            key for child in value.values() for key in _walk_keys(child)
        }
    if isinstance(value, (list, tuple)):
        return {key for child in value for key in _walk_keys(child)}
    return set()


def test_one_module_two_entities_is_precomputed_and_contract_valid():
    fixture = one_module_two_entities_fixture()
    model = parse_knowledge_index(deepcopy(fixture.knowledge_payload))

    classes = fixture.inventory[FIXTURE_SOURCE_PATH]["classes"]
    assert [entity["name"] for entity in classes] == ["User", "AccountService"]
    assert {entity["kind"] for entity in classes} == {"class"}
    assert fixture.module_page_map == {FIXTURE_SOURCE_PATH: "accounts"}
    assert fixture.entity_occurrence_page_map == {
        ("User", FIXTURE_SOURCE_PATH, 1): "User",
        ("AccountService", FIXTURE_SOURCE_PATH, 1): "AccountService",
    }
    assert fixture.extraction_runs == 1
    assert {
        concept.locator
        for concept in model.concepts
        if concept.locator.startswith("llm-wiki://entities/")
    } == {
        "llm-wiki://entities/User",
        "llm-wiki://entities/AccountService",
    }
    assert (
        len(
            [
                relationship
                for relationship in model.relationships
                if relationship.kind == "derived_from"
            ]
        )
        == 3
    )
    expected_source_hash = _sha256(
        fixture.source_files[FIXTURE_SOURCE_PATH].encode("utf-8")
    )
    source_concepts = [
        concept
        for concept in model.concepts
        if concept.facets.structure.basis is not None
    ]
    assert {
        concept.facets.structure.basis.source_content_hash
        for concept in source_concepts
        if concept.facets.structure.basis is not None
    } == {expected_source_hash}
    observations = {
        concept.locator: concept.facets.structure.basis.concept_observation_hash
        for concept in source_concepts
        if concept.facets.structure.basis is not None
    }
    for relationship in model.relationships:
        if relationship.kind == "derived_from":
            assert (
                relationship.evidence.concept_observation_hash
                == observations[relationship.source_locator]
            )

    pages_by_path = {page.canonical_path: page for page in fixture.pages}
    for concept in model.concepts:
        page = pages_by_path[concept.document.canonical_path]
        assert concept.facets.semantics.page_hash == _sha256(
            page.content.encode("utf-8")
        )

    snapshot = fixture.knowledge_payload["bundle"]["snapshot"]
    assert snapshot["source_snapshot_hash"] == _tree_sha256(dict(fixture.source_files))
    assert snapshot["markdown_snapshot_hash"] == _tree_sha256(
        {page.canonical_path: page.content for page in fixture.pages}
    )
    assert snapshot["surface_index_hash"] == _sha256(fixture.surface_bytes)
    assert snapshot["generation_options_hash"] == _sha256(b"{}\n")
    assert fixture.surface_payload == json.loads(fixture.surface_bytes)
    assert fixture.knowledge_payload == json.loads(fixture.knowledge_bytes)
    assert all(isinstance(page, dict) for page in fixture.surface_payload["pages"])
    assert {
        "schema_version",
        "counts",
        "dependency_pages",
        "assets",
        "flows",
        "pages",
        "source_hash",
    } == set(fixture.surface_payload)


def test_duplicate_names_have_occurrence_specific_pages_and_observations():
    fixture = duplicate_entity_occurrences_fixture()
    model = parse_knowledge_index(deepcopy(fixture.knowledge_payload))

    assert fixture.entity_occurrence_page_map == {
        ("Parser", "tests/test_parser.py", 1): "Parser",
        ("Parser", "tests/test_parser.py", 2): "Parser_2",
    }
    classes = fixture.inventory["tests/test_parser.py"]["classes"]
    assert [item["kind"] for item in classes] == ["class", "class"]
    assert [item["docstring"] for item in classes] == [
        "First parser.",
        "Second parser.",
    ]
    assert all(
        docstring in fixture.source_files["tests/test_parser.py"]
        for docstring in (
            "First parser.",
            "Second parser.",
        )
    )
    parser_concepts = [
        concept for concept in model.concepts if concept.concept_kind == "code-entity"
    ]
    assert [concept.document.page_id for concept in parser_concepts] == [
        "Parser",
        "Parser_2",
    ]
    assert (
        parser_concepts[0].facets.structure.basis is not None
        and parser_concepts[1].facets.structure.basis is not None
    )
    assert (
        parser_concepts[0].facets.structure.basis.concept_observation_hash
        != parser_concepts[1].facets.structure.basis.concept_observation_hash
    )


def test_page_role_matrix_uses_registry_derived_paths_and_roles():
    cases = page_role_fixtures()
    registry = {entry.kind.value: entry for entry in iter_page_kinds()}

    assert {case.role for case in cases} == {
        SurfaceRole.GENERATED.value,
        SurfaceRole.SEMANTIC.value,
        SurfaceRole.MIXED.value,
    }
    for case in cases:
        entry = registry[case.page_kind]
        assert case.role == entry.role.value
        assert case.canonical_path == canonical_path(
            PageKind(case.page_kind),
            case.page_id if entry.requires_page_id else None,
        )


def test_source_change_matrix_distinguishes_bytes_concepts_and_basis():
    cases = {case.name: case for case in source_change_fixtures()}

    byte_only = cases["byte-only-source-change"]
    assert byte_only.recorded_source != byte_only.live_source
    assert byte_only.recorded_inventory == byte_only.live_inventory
    assert byte_only.recorded_source_hash != byte_only.live_source_hash
    assert byte_only.recorded_source is not None
    assert byte_only.live_source is not None
    assert _sha256(byte_only.recorded_source.encode()) == (
        byte_only.recorded_source_hash
    )
    assert _sha256(byte_only.live_source.encode()) == byte_only.live_source_hash
    assert byte_only.recorded_observation_hash == byte_only.live_observation_hash
    assert byte_only.expected is ComputedFreshness.NONSEMANTIC_SOURCE_CHANGE

    relevant = cases["concept-relevant-source-change"]
    assert relevant.recorded_source != relevant.live_source
    assert relevant.recorded_inventory is not None
    assert relevant.live_inventory is not None
    assert (
        relevant.recorded_inventory["classes"][0]
        != relevant.live_inventory["classes"][0]
    )
    assert (
        relevant.recorded_inventory["classes"][1]
        == relevant.live_inventory["classes"][1]
    )
    assert relevant.recorded_observation_hash != relevant.live_observation_hash
    assert (
        relevant.recorded_sibling_observation_hash
        == relevant.live_sibling_observation_hash
    )
    assert relevant.expected is ComputedFreshness.SOURCE_CHANGED

    for name in {
        "changed-extractor-version-basis",
        "changed-extractor-config-basis",
    }:
        changed_basis = cases[name]
        assert changed_basis.recorded_source_hash == changed_basis.live_source_hash
        assert changed_basis.recorded_basis_hash != changed_basis.live_basis_hash
        assert changed_basis.expected is ComputedFreshness.BASIS_INCOMPATIBLE


def test_removed_source_matrix_never_fabricates_prior_evidence():
    with_prior, without_prior = removed_source_fixtures()

    assert with_prior.expected is ComputedFreshness.SOURCE_MISSING
    assert with_prior.source_present is False
    assert with_prior.recorded_source_hash is not None
    assert with_prior.recorded_observation_hash is not None
    assert with_prior.recorded_basis_hash is not None

    assert without_prior.expected is ComputedFreshness.UNKNOWN
    assert without_prior.source_present is False
    assert without_prior.recorded_source_hash is None
    assert without_prior.recorded_observation_hash is None
    assert without_prior.recorded_basis_hash is None


def test_freshness_matrix_covers_every_computed_enum():
    cases = freshness_fixtures()

    assert {case.expected for case in cases} == set(ComputedFreshness)
    assert all(case.reason for case in cases)


def test_link_matrix_preserves_observations_and_all_operational_outcomes():
    cases = link_outcome_fixtures()
    fixture = one_module_two_entities_fixture()
    model = parse_knowledge_index(fixture.knowledge_payload)

    assert {
        "resolved",
        "external",
        "anchor-only",
        "malformed",
        "unresolved",
    } <= {case.name for case in cases}
    assert {case.resolution for case in cases} == {
        "resolved",
        "external",
        "ambiguous",
        "unresolved",
    }
    assert {case.target["target_class"] for case in cases} >= {
        "concept",
        "external",
        "mail",
        "anchor",
        "asset",
        "malformed",
    }
    for case in cases:
        target = case.target
        location = target["location"]
        assert case.markdown[location["start"] : location["end"]] == (
            f"[{target['label']}]({target['raw_target']})"
        )
        assert {
            "raw_target",
            "normalized_target",
            "label",
            "location",
        } <= set(target)
        observed = list(iter_markdown_link_targets(case.markdown))
        assert len(observed) == 1
        assert observed[0].raw_target == target["raw_target"]
        assert observed[0].target == target["normalized_target"]
        assert observed[0].label == target["label"]
        assert (observed[0].start, observed[0].end) == (
            location["start"],
            location["end"],
        )
    embedded_names = {case.name for case in cases} - {"ambiguous"}
    embedded_by_raw_target = {
        case.target["raw_target"]: case for case in cases if case.name in embedded_names
    }
    module_page = next(
        page for page in fixture.pages if page.canonical_path == "modules/accounts.md"
    )
    link_relationships = [
        relationship
        for relationship in model.relationships
        if relationship.kind == "links_to"
    ]
    assert len(link_relationships) == len(embedded_names)
    assert len(list(iter_markdown_link_targets(module_page.content))) == len(
        embedded_names
    )
    for relationship in link_relationships:
        target = relationship.target
        assert target.raw_target is not None
        case = embedded_by_raw_target[target.raw_target]
        assert target.location is not None
        observed_text = module_page.content[target.location.start : target.location.end]
        assert observed_text == (
            f"[{case.target['label']}]({case.target['raw_target']})"
        )
        assert relationship.evidence.page_hash == _sha256(
            module_page.content.encode("utf-8")
        )
    assert "## Usage" in module_page.content
    assert "assets/account-flow.svg" in fixture.assets


def test_bundle_matrix_covers_clean_dirty_and_non_git_without_local_paths():
    cases = {case.name: case for case in bundle_envelope_fixtures()}

    assert set(cases) == {"clean", "dirty", "non-git"}
    assert cases["clean"].bundle["repository"]["working_tree"] == "clean"
    assert cases["dirty"].bundle["repository"]["working_tree"] == "dirty"
    assert cases["non-git"].bundle["repository"] == {
        "identity": "unknown",
        "evaluated_revision": "unknown",
        "working_tree": "unknown",
    }
    for case in cases.values():
        payload = build_complete_knowledge_payload()
        payload["bundle"] = deepcopy(dict(case.bundle))
        parse_knowledge_index(payload)
        assert not any(
            Path(value).is_absolute() for value in _walk_strings(case.bundle)
        )


def test_repository_identity_matrix_locks_precedence_and_safe_persisted_results():
    cases = {case.name: case for case in repository_identity_fixtures()}

    assert set(cases) == {
        "configured-public-wins",
        "upstream-remote-before-origin",
        "origin-fallback",
        "credentialed-origin-sanitized",
        "sole-scp-remote",
        "ambiguous-remotes",
        "local-file-remote",
        "windows-local-remote",
        "unc-local-remote",
        "no-vcs",
    }
    assert cases["configured-public-wins"].expected_source is (
        RepositoryIdentitySource.CONFIGURED_PUBLIC
    )
    assert cases["upstream-remote-before-origin"].expected_identity == (
        "github.com/Acme/Accounts"
    )
    assert cases["origin-fallback"].expected_identity == (
        "gitlab.example/Acme/Accounts"
    )
    assert cases["credentialed-origin-sanitized"].expected_identity == (
        "private.example/Acme/Accounts"
    )
    assert cases["sole-scp-remote"].expected_identity == ("code.example/Acme/Accounts")
    assert {
        cases[name].expected_identity
        for name in {
            "ambiguous-remotes",
            "local-file-remote",
            "windows-local-remote",
            "unc-local-remote",
            "no-vcs",
        }
    } == {"unknown"}

    for case in cases.values():
        payload = build_complete_knowledge_payload()
        payload["bundle"]["repository"] = case.expected_repository()
        model = parse_knowledge_index(payload)
        repository = model.bundle.repository
        assert repository.identity == case.expected_identity
        assert repository.identity_source is case.expected_source
        persisted = knowledge_index_to_payload(model)["bundle"]["repository"]
        persisted_text = json.dumps(persisted).lower()
        assert not any(
            needle in persisted_text
            for needle in (
                "access_token",
                "alice",
                "file://",
                "secret",
                "token",
                "users",
            )
        )
        assert case.reason


def test_equal_snapshots_do_not_collapse_distinct_or_unknown_repositories():
    left_payload = build_complete_knowledge_payload()
    right_payload = deepcopy(left_payload)
    right_payload["bundle"]["repository"].update(
        {
            "identity": "example.invalid/acme/other-repository",
            "extensions": {REPOSITORY_IDENTITY_SOURCE_EXTENSION: "configured-public"},
        }
    )
    same_payload = deepcopy(left_payload)
    unknown_payload = deepcopy(left_payload)
    unknown_payload["bundle"]["repository"] = {
        "identity": "unknown",
        "evaluated_revision": "unknown",
        "working_tree": "unknown",
    }

    left = parse_knowledge_index(left_payload)
    right = parse_knowledge_index(right_payload)
    same = parse_knowledge_index(same_payload)
    unknown_left = parse_knowledge_index(unknown_payload)
    unknown_right = parse_knowledge_index(deepcopy(unknown_payload))

    assert left.bundle.snapshot == right.bundle.snapshot
    assert not repository_identities_match(
        left.bundle.repository,
        right.bundle.repository,
    )
    assert repository_identities_match(
        left.bundle.repository,
        same.bundle.repository,
    )
    assert not repository_identities_match(
        unknown_left.bundle.repository,
        unknown_right.bundle.repository,
    )


def test_redaction_profiles_define_safe_boundaries_without_selecting_an_exporter():
    cases = {case.profile: case for case in redaction_policy_fixtures()}
    internal = cases[KnowledgeProjectionProfile.INTERNAL]
    public = cases[KnowledgeProjectionProfile.PUBLIC_PORTABLE]

    assert set(cases) == set(KnowledgeProjectionProfile)
    assert internal.retained_identity_sources == {
        RepositoryIdentitySource.CONFIGURED_PUBLIC,
        RepositoryIdentitySource.NORMALIZED_VCS,
    }
    assert public.retained_identity_sources == {
        RepositoryIdentitySource.CONFIGURED_PUBLIC
    }
    assert internal.retained_evaluated_revision
    assert not public.retained_evaluated_revision
    assert internal.retained_working_tree_state
    assert not public.retained_working_tree_state
    assert internal.retained_actor_identity
    assert not public.retained_actor_identity
    assert internal.retained_unreviewed_extensions
    assert not public.retained_unreviewed_extensions
    assert {
        "absolute-path",
        "credential",
        "environment-dump",
        "raw-plugin-settings",
        "raw-vcs-remote",
    } <= internal.prohibited_value_classes
    assert {
        "credentialed-link-observation",
        "local-actor-identity",
        "normalized-vcs-identity",
        "private-plugin-record",
        "unreviewed-extension",
    } <= public.prohibited_value_classes


def test_hostile_metadata_remains_inert_and_cannot_select_execution_or_access(
    monkeypatch,
):
    from llm_wiki_cli.services import plugins

    schema = load_knowledge_schema()
    attempted_effects: list[str] = []

    def forbidden_effect(*_args, **_kwargs):
        attempted_effects.append("called")
        raise AssertionError("knowledge metadata attempted an external effect")

    monkeypatch.setattr(plugins, "load_entry_point", forbidden_effect)
    monkeypatch.setattr(plugins.importlib, "import_module", forbidden_effect)
    monkeypatch.setattr(subprocess, "Popen", forbidden_effect)
    monkeypatch.setattr(subprocess, "run", forbidden_effect)
    monkeypatch.setattr(socket, "create_connection", forbidden_effect)
    monkeypatch.setattr(urllib.request, "urlopen", forbidden_effect)

    payload = inert_metadata_fixture()
    model = parse_knowledge_index(payload)
    normalized = knowledge_index_to_payload(model)

    assert attempted_effects == []
    assert (
        normalized["bundle"]["producer"]["plugins"][0]["extensions"][
            "example.invalid/dispatch"
        ]["entry_point"]
        == "malicious.module:activate"
    )
    assert normalized["extensions"]["example.invalid/access-control"] == {
        "allow": True,
        "projection_profile": "internal",
        "roles": ["administrator"],
    }
    assert not hasattr(model, "projection_profile")
    assert not hasattr(model, "authorized")

    component_properties = schema["$defs"]["component"]["properties"]
    assert {
        "command",
        "entry_point",
        "executable",
        "helper",
        "module",
        "permissions",
        "projection_profile",
        "url",
    }.isdisjoint(component_properties)
    assert "projection_profile" not in schema["properties"]


def test_producer_basis_matrix_changes_only_the_declared_producer_basis():
    cases = {case.name: case for case in producer_basis_fixtures()}
    baseline = cases["producer-baseline"]

    assert set(cases) == {
        "producer-baseline",
        "changed-extractor-version",
        "changed-extractor-config",
        "changed-plugin-version",
        "changed-plugin-config",
        "changed-plugin-limitations",
        "unknown-plugin-configuration-basis",
    }
    assert all(
        case.bundle["snapshot"] == baseline.bundle["snapshot"]
        for case in cases.values()
    )
    version_change = cases["changed-extractor-version"]
    config_change = cases["changed-extractor-config"]
    baseline_extractor = baseline.bundle["producer"]["extractors"][0]
    version_extractor = version_change.bundle["producer"]["extractors"][0]
    config_extractor = config_change.bundle["producer"]["extractors"][0]
    assert baseline_extractor["version"] != version_extractor["version"]
    assert (
        baseline_extractor["configuration_hash"]
        != config_extractor["configuration_hash"]
    )
    baseline_plugin = baseline.bundle["producer"]["plugins"][0]
    assert (
        baseline_plugin["version"]
        != cases["changed-plugin-version"].bundle["producer"]["plugins"][0]["version"]
    )
    assert (
        baseline_plugin["configuration_hash"]
        != cases["changed-plugin-config"].bundle["producer"]["plugins"][0][
            "configuration_hash"
        ]
    )
    assert (
        baseline_plugin["limitations"]
        != cases["changed-plugin-limitations"].bundle["producer"]["plugins"][0][
            "limitations"
        ]
    )
    unknown_configuration = cases["unknown-plugin-configuration-basis"].bundle[
        "producer"
    ]["plugins"][0]
    assert "configuration_hash" not in unknown_configuration
    assert "configuration-basis-unknown" in unknown_configuration["limitations"]
    for case in cases.values():
        for group in ("extractors", "plugins"):
            for component in case.bundle["producer"].get(group, []):
                limitations = component.get("limitations", [])
                assert limitations == sorted(set(limitations))
        payload = build_complete_knowledge_payload()
        payload["bundle"] = deepcopy(dict(case.bundle))
        parse_knowledge_index(payload)


def test_load_fixture_matrix_covers_every_load_state_and_policy_boundary():
    cases = load_state_fixtures()
    by_name = {case.name: case for case in cases}

    assert {state.value for state in KnowledgeLoadState} == {
        "valid",
        "absent",
        "invalid",
        "mixed-snapshot",
        "degraded",
    }
    assert {case.expected_state for case in cases} == set(KnowledgeLoadState)
    assert (
        by_name["absent-declared-artifact-missing"].knowledge_bytes is None
        and by_name["absent-declared-artifact-missing"].committed_knowledge_hash
        is not None
        and by_name["absent-declared-artifact-missing"].expected_state
        is KnowledgeLoadState.INVALID
    )
    unsupported = by_name["invalid-unsupported-version"]
    assert unsupported.knowledge_bytes is not None
    assert json.loads(unsupported.knowledge_bytes)["schema_version"] == (
        "llm-wiki-knowledge/v2"
    )
    orphan = by_name["invalid-orphan-without-capable-marker"]
    assert orphan.knowledge_bytes is not None
    assert orphan.committed_knowledge_hash is None
    valid = by_name["valid"]
    assert valid.surface_bytes is not None
    assert valid.knowledge_bytes is not None
    assert valid.committed_surface_hash == _sha256(valid.surface_bytes)
    assert valid.committed_knowledge_hash == _sha256(valid.knowledge_bytes)
    valid_knowledge = json.loads(valid.knowledge_bytes)
    assert valid_knowledge["bundle"]["snapshot"]["surface_index_hash"] == _sha256(
        valid.surface_bytes
    )
    assert json.loads(valid.surface_bytes)["schema_version"] == (
        "llm-wiki-surface-index/v1"
    )
    assert {
        case.name
        for case in cases
        if case.expected_state is KnowledgeLoadState.DEGRADED
    } == {"degraded-from-mixed-snapshot", "degraded-from-invalid"}
    for case in cases:
        if case.expected_state is KnowledgeLoadState.DEGRADED:
            assert case.fallback_selected
            assert case.underlying_state in {
                KnowledgeLoadState.INVALID,
                KnowledgeLoadState.MIXED_SNAPSHOT,
            }
        else:
            assert not case.fallback_selected


def test_projection_mismatch_fixtures_hash_exact_persisted_bytes():
    cases = {case.name: case for case in projection_integrity_fixtures()}

    assert set(cases) == {
        "interrupted-before-manifest-commit",
        "surface-projection-hash-mismatch",
        "knowledge-projection-hash-mismatch",
    }
    for case in cases.values():
        assert case.expected_state is KnowledgeLoadState.MIXED_SNAPSHOT
        assert case.surface_bytes is not None
        assert case.knowledge_bytes is not None

    interrupted = cases["interrupted-before-manifest-commit"]
    assert _sha256(interrupted.surface_bytes) != interrupted.committed_surface_hash
    assert _sha256(interrupted.knowledge_bytes) != interrupted.committed_knowledge_hash

    surface_mismatch = cases["surface-projection-hash-mismatch"]
    assert (
        _sha256(surface_mismatch.surface_bytes)
        != surface_mismatch.committed_surface_hash
    )
    assert (
        _sha256(surface_mismatch.knowledge_bytes)
        == surface_mismatch.committed_knowledge_hash
    )

    knowledge_mismatch = cases["knowledge-projection-hash-mismatch"]
    assert (
        _sha256(knowledge_mismatch.surface_bytes)
        == knowledge_mismatch.committed_surface_hash
    )
    assert (
        _sha256(knowledge_mismatch.knowledge_bytes)
        != knowledge_mismatch.committed_knowledge_hash
    )


def test_fixture_inputs_are_fresh_copies_reusable_by_every_consumer():
    fixture = one_module_two_entities_fixture()
    first = fixture.inputs_for("bootstrap")
    first["inventory"][FIXTURE_SOURCE_PATH]["classes"][0]["name"] = "Mutated"

    for consumer in FIXTURE_CONSUMERS:
        inputs = fixture.inputs_for(consumer)
        assert inputs["inventory"][FIXTURE_SOURCE_PATH]["classes"][0]["name"] == "User"
        assert inputs["extraction_runs"] == 1
        assert parse_knowledge_index(inputs["knowledge_payload"])
        assert inputs["surface_payload"] == fixture.surface_payload
        assert inputs["surface_bytes"] == fixture.surface_bytes
        assert inputs["knowledge_bytes"] == fixture.knowledge_bytes
        assert inputs["extractor_guard"] is fail_if_extraction_runs

    with pytest.raises(ValueError):
        fixture.inputs_for("unknown-consumer")
    with pytest.raises(AssertionError):
        fail_if_extraction_runs()


def test_one_evaluated_fixture_serves_all_current_consumer_seams(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    from llm_wiki_cli import api
    from llm_wiki_cli.commands import (
        bootstrap_cmd,
        context_cmd,
        lint_cmd,
        sync_cmd,
    )
    from llm_wiki_cli.services import mcp_server
    from llm_wiki_cli.services.documentation_queries import (
        DocumentationGraphQueryService,
    )

    fixture = one_module_two_entities_fixture()
    original = fixture.inputs_for("bootstrap")
    tree = materialize_fixture_tree(fixture, tmp_path / "checkout", consumer="mcp")
    inventory = dict(fixture.inventory)

    monkeypatch.setattr(bootstrap_cmd, "get_inventory_result", fail_if_extraction_runs)
    monkeypatch.setattr(sync_cmd, "get_inventory_result", fail_if_extraction_runs)
    monkeypatch.setattr(lint_cmd, "get_inventory_result", fail_if_extraction_runs)
    monkeypatch.setattr(context_cmd, "get_inventory_result", fail_if_extraction_runs)
    monkeypatch.setattr(
        api.extract_cmd, "build_extract_payload", fail_if_extraction_runs
    )
    monkeypatch.setattr(mcp_server, "get_inventory", fail_if_extraction_runs)

    bootstrap_maps = bootstrap_cmd._prepare_bootstrap_page_maps(inventory)
    sync_maps = sync_cmd._prepare_sync_page_maps(inventory)
    assert bootstrap_maps.module_page_map == fixture.module_page_map
    assert (
        bootstrap_maps.entity_occurrence_page_name_cache
        == fixture.entity_occurrence_page_map
    )
    assert sync_maps.module_page_map == fixture.module_page_map
    assert sync_maps.entity_occurrence_page_cache == fixture.entity_occurrence_page_map

    assert lint_cmd._collect_code_classes(inventory) == {
        "User",
        "AccountService",
    }
    assert lint_cmd._collect_code_modules(inventory) == {"accounts"}

    context_payload = context_cmd._build_context_payload(
        inventory,
        {FIXTURE_SOURCE_PATH: "high"},
        32_000,
    )
    surface_filter = context_cmd._surface_filter_payload(
        dict(fixture.surface_payload),
        "entities",
        limit=20,
    )
    assert set(context_payload["files"]) == {FIXTURE_SOURCE_PATH}
    assert surface_filter["total"] == 2

    graph_service = DocumentationGraphQueryService(
        inventory,
        surface_index=fixture.surface_payload,
    )
    api_result = api.pages_for_symbol("User", service=graph_service)
    assert api_result["found"] is True
    assert {page["canonical_path"] for page in api_result["pages"]} >= {
        "entities/User.md",
        "modules/accounts.md",
    }

    monkeypatch.setattr(
        mcp_server,
        "build_documentation_query_service",
        lambda *_args, **_kwargs: graph_service,
    )
    mcp = mcp_server.McpWikiService(
        src_dir=str(tree["root"]),
        wiki_dir=str(tree["wiki_root"]),
    )
    mcp_query = mcp.query_graph({"type": "pages_for_symbol", "value": "User"})
    resource = mcp.read_resource("llm-wiki://entities/User")
    assert mcp_query["found"] is True
    assert resource["uri"] == "llm-wiki://entities/User"
    assert resource["text"].startswith("# User\n")

    assert fixture.inputs_for("bootstrap") == original


def test_fixture_builders_return_equal_but_independent_mutable_payloads():
    first = one_module_two_entities_fixture()
    second = one_module_two_entities_fixture()

    assert first == second
    first.inventory[FIXTURE_SOURCE_PATH]["classes"][0]["name"] = "Mutated"
    first.knowledge_payload["concepts"][0]["title"] = "Mutated"
    assert second.inventory[FIXTURE_SOURCE_PATH]["classes"][0]["name"] == "User"
    assert second.knowledge_payload["concepts"][0]["title"] == "AccountService"


def test_materialized_trees_normalize_identically_without_hiding_payload_paths(
    tmp_path: Path,
):
    fixture = one_module_two_entities_fixture()
    first = materialize_fixture_tree(fixture, tmp_path / "first checkout")
    second = materialize_fixture_tree(fixture, tmp_path / "second-checkout")
    assert first["surface_path"].read_bytes() == fixture.surface_bytes
    assert first["knowledge_path"].read_bytes() == fixture.knowledge_bytes
    assert (
        first["asset_paths"]["assets/account-flow.svg"].read_bytes()
        == (fixture.assets["assets/account-flow.svg"])
    )
    with pytest.raises(AssertionError):
        assert_no_temporary_roots(
            first,
            {tmp_path / "first checkout": "<FIXTURE_ROOT>"},
        )
    first_normalized = normalize_temporary_roots(
        first,
        {
            tmp_path / "first checkout": "<FIXTURE_ROOT>",
        },
    )
    second_normalized = normalize_temporary_roots(
        second,
        {
            tmp_path / "second-checkout": "<FIXTURE_ROOT>",
        },
    )

    assert first_normalized == second_normalized
    assert_no_temporary_roots(
        first_normalized,
        {
            tmp_path / "first checkout": "<FIXTURE_ROOT>",
            tmp_path / "second-checkout": "<FIXTURE_ROOT>",
        },
    )
    persisted_strings = _walk_strings(fixture.knowledge_payload)
    assert all(str(tmp_path) not in value for value in persisted_strings)
    assert all(not Path(value).is_absolute() for value in persisted_strings)


def test_materialized_surface_rebuild_uses_precomputed_inventory_without_extraction(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    from llm_wiki_cli.extractors.python_extractor import PythonExtractor

    fixture = one_module_two_entities_fixture()
    tree = materialize_fixture_tree(fixture, tmp_path / "checkout", consumer="api")
    inputs = tree["evaluated_inputs"]
    monkeypatch.setattr(PythonExtractor, "extract", fail_if_extraction_runs)

    rebuilt = build_surface_index(
        tree["wiki_root"],
        inputs["inventory"],
        src_dir=tree["root"],
        entity_occurrence_page_cache=inputs["entity_occurrence_page_map"],
        module_page_map=inputs["module_page_map"],
    )

    assert rebuilt == inputs["surface_payload"]
    assert inputs["extraction_runs"] == 1


def test_normalizer_handles_native_posix_windows_and_path_spellings(tmp_path: Path):
    root = (tmp_path / "checkout with spaces").resolve()
    value = {
        "path": root / "src" / "accounts.py",
        "native": f"{root}/docs",
        "posix": f"{root.as_posix()}/wiki",
        "windows": f"{str(root).replace('/', chr(92))}\\cache",
        "unrelated_raw_link": r"..\entities\Missing.md",
    }

    normalized = normalize_temporary_roots(value, {root: "<ROOT>"})

    assert normalized == {
        "path": "<ROOT>/src/accounts.py",
        "native": "<ROOT>/docs",
        "posix": "<ROOT>/wiki",
        "windows": "<ROOT>/cache",
        "unrelated_raw_link": r"..\entities\Missing.md",
    }


def test_normalizer_preserves_lexical_and_resolved_root_spellings(tmp_path: Path):
    real_root = tmp_path / "real" / "repo"
    real_root.mkdir(parents=True)
    lexical_root = tmp_path / "placeholder" / ".." / "real" / "repo"
    resolved_root = lexical_root.resolve()
    value = {
        "lexical": str(lexical_root / "source.py"),
        "resolved": str(resolved_root / "source.py"),
        "prefix_collision": f"{lexical_root}-other/source.py",
    }

    normalized = normalize_temporary_roots(value, {lexical_root: "<ROOT>"})

    assert normalized["lexical"] == "<ROOT>/source.py"
    assert normalized["resolved"] == "<ROOT>/source.py"
    assert normalized["prefix_collision"] == f"{lexical_root}-other/source.py"
    with pytest.raises(AssertionError):
        assert_no_temporary_roots(value, {lexical_root: "<ROOT>"})
    assert_no_temporary_roots(normalized, {lexical_root: "<ROOT>"})


def test_only_one_reviewable_golden_is_committed_and_byte_stable():
    first = render_knowledge_goldens()
    second = render_knowledge_goldens()

    assert first == second
    assert set(first) == {"complete-v1.json"}
    assert {path.name for path in GOLDEN_ROOT.glob("*.json")} == set(first)
    for name, rendered in first.items():
        committed = (GOLDEN_ROOT / name).read_bytes()
        assert rendered == committed
        assert rendered.endswith(b"\n")
        assert not rendered.endswith(b"\n\n")
        assert b"\r" not in rendered
    attributes = (Path(__file__).parents[1] / ".gitattributes").read_text(
        encoding="utf-8"
    )
    assert "tests/fixtures/knowledge/*.json text eol=lf" in attributes.splitlines()


def test_golden_regenerator_defaults_to_read_only_check():
    path = GOLDEN_ROOT / "complete-v1.json"
    before = path.read_bytes()

    assert check_or_regenerate_goldens([]) == 0
    assert path.read_bytes() == before


def test_golden_regenerator_rejects_and_explicitly_removes_stale_files(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    rendered = render_knowledge_goldens()
    golden_root = tmp_path / "goldens"
    golden_root.mkdir()
    for name, content in rendered.items():
        (golden_root / name).write_bytes(content)
    stale = golden_root / "obsolete-v0.json"
    stale.write_text("{}\n", encoding="utf-8")
    monkeypatch.setattr(regenerate_knowledge_goldens, "GOLDEN_ROOT", golden_root)

    with pytest.raises(SystemExit):
        regenerate_knowledge_goldens.main([])
    assert stale.exists()

    assert regenerate_knowledge_goldens.main(["--write"]) == 0
    assert not stale.exists()
    assert {path.name for path in golden_root.glob("*.json")} == set(rendered)


def test_golden_regenerator_is_directly_runnable_from_the_repository():
    project_root = Path(__file__).parents[1]
    result = subprocess.run(
        [sys.executable, "tests/regenerate_knowledge_goldens.py"],
        cwd=project_root,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    assert "knowledge goldens are current" in result.stdout


def test_golden_round_trips_to_its_canonical_bytes_and_contains_no_live_state():
    golden = (GOLDEN_ROOT / "complete-v1.json").read_bytes()
    payload = json.loads(golden)
    model = parse_knowledge_index(payload)

    assert knowledge_index_to_payload(model) == payload
    assert set(_walk_strings(payload)).isdisjoint(
        {state.value for state in ComputedFreshness} - {"unknown"}
    )
    assert "freshness" not in _walk_keys(payload)
    assert "computed_freshness" not in _walk_keys(payload)
    assert "load_state" not in _walk_keys(payload)


def test_load_and_freshness_vocabularies_are_nonpersisted_schema_definitions():
    schema = load_knowledge_schema()
    definitions = schema["$defs"]

    assert set(definitions["knowledgeLoadState"]["enum"]) == {
        state.value for state in KnowledgeLoadState
    }
    assert set(definitions["computedFreshness"]["enum"]) == {
        state.value for state in ComputedFreshness
    }
    assert set(definitions["knowledgeProjectionProfile"]["enum"]) == {
        profile.value for profile in KnowledgeProjectionProfile
    }
    properties = schema["properties"]
    assert "knowledge_load_state" not in properties
    assert "computed_freshness" not in properties
    assert "projection_profile" not in properties


def test_fixture_payloads_and_golden_validate_against_packaged_json_schema():
    schema = load_knowledge_schema()
    validator = Draft202012Validator(schema)
    payloads = (
        build_complete_knowledge_payload(),
        duplicate_entity_occurrences_fixture().knowledge_payload,
        json.loads((GOLDEN_ROOT / "complete-v1.json").read_bytes()),
    )

    for payload in payloads:
        assert list(validator.iter_errors(payload)) == []


def test_fixture_payloads_have_no_wall_clock_or_absolute_checkout_state():
    payloads = [
        build_complete_knowledge_payload(),
        duplicate_entity_occurrences_fixture().knowledge_payload,
    ]

    for payload in payloads:
        strings = _walk_strings(payload)
        assert all(not Path(value).is_absolute() for value in strings)
        assert not {
            "timestamp",
            "created_at",
            "updated_at",
            "mtime",
            "mtime_ns",
        } & _walk_keys(payload)
