"""Falsifiable persistence/comparison controls independent of public adapters."""

from __future__ import annotations

import ast
from copy import deepcopy
from dataclasses import replace
import json
from pathlib import Path
from typing import Any, cast

from jsonschema import Draft202012Validator
import pytest

from llm_wiki_cli.services import implementation_evidence as ie
from llm_wiki_cli.services import python_implementation as pi
from llm_wiki_cli.services.analysis_capture import _issued, attach
from llm_wiki_cli.services.knowledge_envelope import (
    ProducerComponentInput,
    build_producer_record,
)
from llm_wiki_cli.services.sync_manifest import ManifestPageSource

HASH = "sha256:" + "a" * 64
OTHER = "sha256:" + "b" * 64
SOURCE = 'FLAG = 3\nclass Batch:\n    """A policy."""\n    def cap(self, values, limit=3):\n        return values[:limit]\ndef sibling(): return FLAG\n'


def issuer():
    return _issued(
        {
            name: {
                "implementation": HASH,
                "runtime": HASH,
                "provenance": {
                    "python": "model",
                    "platform": "model",
                    "helper": "none",
                },
            }
            for name in ("agent-wiki-cli", "llm-wiki/extractor/python")
        }
    )


def producer():
    captured = issuer()
    return build_producer_record(
        tool=attach(
            ProducerComponentInput(
                component_id="agent-wiki-cli", version="1", configuration={}
            ),
            captured,
        ),
        extractors=[
            attach(
                ProducerComponentInput(
                    component_id="llm-wiki/extractor/python",
                    version="1",
                    configuration={},
                ),
                captured,
            )
        ],
    )


def compare(*args, **options):
    options.setdefault("expected_analysis_hash", pi.analysis_identity(issuer()))
    return ie.compare_implementation_observations(*args, **options)


def captured(text=SOURCE, analysis=None):
    configured = pi.producer(analysis or pi.analysis_identity(issuer()))
    return pi.capture(
        ast.parse(text),
        text.encode(),
        "policy.py",
        configured=configured,
        parsed_source=text,
    )


def owner(value, name="Batch.cap", occurrence=1):
    return next(
        row["evidence"]
        for row in value["observations"]
        if row["evidence"]["coordinate"]["qualified_owner"] == name
        and row["evidence"]["coordinate"]["occurrence"] == occurrence
    )


def projected(text=SOURCE):
    capture = captured(text)
    mappings = {
        "modules/policy.md": ManifestPageSource(
            scope="module", source_path="policy.py"
        ),
        "entities/Batch.md": ManifestPageSource(
            scope="entity", source_path="policy.py", entity_name="Batch", occurrence=1
        ),
    }
    extensions = ie.project_concept_implementations(
        pi.envelope({"policy.py": capture}),
        mappings,
        producer=producer(),
        source_content_hashes={"policy.py": capture["source_hash"]},
    )
    concepts = [
        {
            "locator": path,
            "document": {
                "page_kind": "modules" if path.startswith("modules") else "entities",
                "canonical_path": path,
            },
            "extensions": value,
        }
        for path, value in extensions.items()
    ]
    return concepts, capture, mappings


@pytest.mark.parametrize(
    "before,after,expected,docs",
    [
        ("values[:limit]", "values[:limit - 1]", "changed", False),
        ("limit=3", "limit=4", "changed", False),
        ("A policy.", "An authored explanation.", "unchanged", False),
        (
            "return values[:limit]",
            "# shifted\n        return values[:limit]",
            "unchanged",
            False,
        ),
        ("FLAG = 3", "FLAG = 4", "unchanged", False),
    ],
)
def test_callable_comparison_scopes_actual_syntax(before, after, expected, docs):
    first = owner(captured())
    second = owner(captured(SOURCE.replace(before, after)))
    result = compare(
        first,
        second,
        analysis_scope="selected-source",
        expected_analysis_hash=pi.analysis_identity(issuer()),
    )
    assert result.state == expected
    assert result.documentation_changed is docs
    assert result.source_changed is True
    assert result.live_comparison_performed
    assert result.scope == "callable"


def test_class_documentation_changes_are_separate_and_global_edit_does_not_claim_method_change():
    base = captured()
    docs = captured(SOURCE.replace("A policy.", "New rationale."))
    result = compare(
        owner(base, "Batch"), owner(docs, "Batch"), analysis_scope="full-inventory"
    )
    assert result.state == "unchanged" and result.documentation_changed is True
    global_edit = captured(SOURCE.replace("FLAG = 3", "FLAG = 4"))
    assert (
        compare(
            owner(base, "__module__"),
            owner(global_edit, "__module__"),
            analysis_scope="full-inventory",
        ).state
        == "changed"
    )
    assert (
        compare(owner(base), owner(global_edit), analysis_scope="full-inventory").state
        == "unchanged"
    )


@pytest.mark.parametrize(
    "change", ["parser", "analysis", "scope", "algorithm", "unavailable"]
)
def test_incompatible_or_unavailable_inputs_never_assert_executable_change(change):
    left = owner(captured())
    right = deepcopy(left)
    right["executable_hash"] = OTHER
    if change == "parser":
        right["producer"]["parser_version"] = "3.14.999"
    elif change == "analysis":
        right["producer"]["analysis_compatibility_hash"] = OTHER
    elif change == "scope":
        right["scope"] = "class"
    elif change == "algorithm":
        right["producer"]["algorithm"] = "future-ast/v2"
    else:
        right.update(
            status="unavailable",
            executable_hash=None,
            documentation_hash=None,
            unavailable_reason="unsupported-syntax",
        )
        right["aggregation"]["complete_scope"] = False
    right["comparison_id"] = pi.comparison_id(right["producer"])
    result = compare(left, right, analysis_scope="selected-source")
    assert result.state == "unavailable" and not result.live_comparison_performed
    assert result.documentation_changed is None


@pytest.mark.parametrize("digest", ["executable_hash", "documentation_hash"])
def test_same_source_compatible_observation_contradiction_is_unavailable(digest):
    left = owner(captured())
    right = {**left, digest: OTHER}
    result = compare(left, right, analysis_scope="full-inventory")
    assert result.reason == "identical-source-observation-mismatch"
    assert result.state == "unavailable" and not result.live_comparison_performed


def test_snapshot_has_no_live_comparison_even_when_live_is_supplied():
    left = owner(captured())
    right = owner(captured(SOURCE.replace("values[:limit]", "values[:limit - 1]")))
    result = compare(left, right)
    assert result.reason == "live-evaluation-not-performed"
    assert result.live is None and result.source_changed is None
    assert not result.live_comparison_performed


@pytest.mark.parametrize(
    "options,reason",
    [
        ({"source_captured": False}, "source-not-captured"),
        ({"source_present": False}, "missing-source"),
        ({}, "owner-not-observed"),
    ],
)
def test_missing_capture_is_explicit(options, reason):
    result = compare(
        owner(captured()), None, analysis_scope="selected-source", **options
    )
    assert result.state == "unavailable" and result.reason == reason


@pytest.mark.parametrize(
    "edit",
    [
        lambda r: r.update(schema_version="llm-wiki-implementation-evidence/v2"),
        lambda r: r["coordinate"].update(occurrence=True),
        lambda r: r["coordinate"].update(source_path="."),
        lambda r: r["coordinate"].update(source_path="../policy.py"),
        lambda r: r.update(source_hash="a" * 64),
        lambda r: r.update(comparison_id=OTHER),
        lambda r: r["aggregation"].update(observations_returned=True),
        lambda r: r["aggregation"].update(truncated=True),
        lambda r: r.update(unavailable_reason="unknown"),
        lambda r: r.update(executable_hash=None),
        lambda r: r.update(extra=True),
    ],
)
def test_strict_primary_contract_rejects_corruption(edit):
    record = owner(captured())
    edit(record)
    with pytest.raises(ValueError):
        ie.validate_implementation_evidence(record)


def test_project_exact_duplicate_class_occurrence_and_descendant_lineage():
    text = "class Batch:\n def cap(self): return 1\nclass Batch:\n def cap(self): return 2\n"
    capture = captured(text)
    mappings = {
        f"entities/Batch{i}.md": ManifestPageSource(
            scope="entity", source_path="policy.py", entity_name="Batch", occurrence=i
        )
        for i in (1, 2)
    }
    result = ie.project_concept_implementations(
        pi.envelope({"policy.py": capture}),
        mappings,
        producer=producer(),
        source_content_hashes={"policy.py": capture["source_hash"]},
    )
    for i in (1, 2):
        rows = result[f"entities/Batch{i}.md"][ie.DECLARATIONS_KEY]["observations"]
        assert len(rows) == 1
        assert rows[0]["evidence"]["coordinate"]["occurrence"] == i
        assert rows[0]["lineage"][-1]["coordinate"]["occurrence"] == i
    changed = deepcopy(result["entities/Batch1.md"][ie.DECLARATIONS_KEY])
    changed["observations"] = result["entities/Batch2.md"][ie.DECLARATIONS_KEY][
        "observations"
    ]
    with pytest.raises(ValueError, match="exact parent occurrence"):
        ie.validate_implementation_declarations(changed)


def test_projection_gap_never_fabricates_producer():
    _, capture, mappings = projected()
    gap = pi.capture(
        None,
        SOURCE.encode(),
        "policy.py",
        configured=None,
        reason="unsupported-producer",
    )
    result = ie.project_concept_implementations(
        pi.envelope({"policy.py": gap}),
        mappings,
        producer=producer(),
        source_content_hashes={"policy.py": capture["source_hash"]},
    )
    assert all(
        ie.IMPLEMENTATION_KEY not in extensions for extensions in result.values()
    )
    assert all(
        value[ie.DECLARATIONS_KEY]["bounds"]["reason"] == "unsupported-producer"
        for value in result.values()
    )


@pytest.mark.parametrize(
    "change", ["source", "producer", "mapping", "supplement-owner"]
)
def test_concept_crosschecks_actual_commitments_without_historical_structural_hash(
    change,
):
    concepts, capture, mappings = projected()
    concept = concepts[1]
    concept["facets"] = {"structure": {"basis": {"source_content_hash": OTHER}}}
    options = dict(
        producer=producer(),
        source_content_hashes={"policy.py": capture["source_hash"]},
        mapping=mappings["entities/Batch.md"],
    )
    ie.validate_concept_implementation(concept, **options)
    if change == "source":
        options["source_content_hashes"] = {"policy.py": OTHER}
    elif change == "producer":
        options["producer"] = replace(producer(), extractors=())
    elif change == "mapping":
        options["mapping"] = ManifestPageSource(
            scope="entity", source_path="policy.py", entity_name="Batch", occurrence=2
        )
    else:
        concept["extensions"][ie.DECLARATIONS_KEY]["owner"]["coordinate"][
            "occurrence"
        ] = 2
    with pytest.raises(ValueError):
        ie.validate_concept_implementation(concept, **options)


def test_report_is_immutable_scoped_and_selects_exact_qualified_coordinate():
    concepts, capture, _ = projected()
    live = captured(SOURCE.replace("values[:limit]", "values[:limit - 1]"))
    report = ie.compare_knowledge_implementation(
        concepts,
        pi.envelope({"policy.py": live}),
        analysis_scope="selected",
        captured_paths={"policy.py"},
        source_content_hashes={"policy.py": live["source_hash"]},
        analysis_compatibility_hash=pi.analysis_identity(issuer()),
    )
    selected = ie.select_implementation_comparison(report, "policy.py:Batch.cap#1")
    assert selected.state == "changed" and selected.analysis_scope == "selected-source"
    assert (
        ie.select_implementation_comparison(report, "policy.py:sibling#1").state
        == "unchanged"
    )
    assert selected.recorded is not None
    with pytest.raises(TypeError):
        cast(dict[str, Any], report.by_coordinate)["other"] = selected
    with pytest.raises(TypeError):
        cast(dict[str, Any], selected.recorded)["source_hash"] = OTHER
    payload = selected.to_payload()
    payload["recorded"]["source_hash"] = OTHER
    assert selected.recorded["source_hash"] == capture["source_hash"]


def test_report_rejects_live_hashes_differing_from_capture_commitment():
    concepts, capture, _ = projected()
    fake = deepcopy(capture)
    fake["observations"][0]["evidence"]["source_hash"] = OTHER
    report = ie.compare_knowledge_implementation(
        concepts,
        pi.envelope({"policy.py": fake}),
        analysis_scope="full-inventory",
        source_content_hashes={"policy.py": capture["source_hash"]},
    )
    assert report.by_locator["modules/policy.md"].reason == "invalid-captured-evidence"


def test_bound_omitted_declaration_edit_changes_aggregate_without_invented_detail():
    text = "\n".join(f"def f{i}(): return {i}" for i in range(150)) + "\n"
    concepts, capture, _ = projected(text)
    changed = captured(text.replace("return 149", "return -149"))
    report = ie.compare_knowledge_implementation(
        concepts,
        pi.envelope({"policy.py": changed}),
        analysis_scope="full-inventory",
        analysis_compatibility_hash=pi.analysis_identity(issuer()),
    )
    assert report.by_locator["modules/policy.md"].state == "changed"
    assert report.by_locator["modules/policy.md"].truncated
    assert "policy.py:f149#1" not in report.by_coordinate
    declarations = concepts[0]["extensions"][ie.DECLARATIONS_KEY]
    assert declarations["bounds"]["truncated"]
    assert len(pi.canonical_bytes(declarations)) <= pi.MAX_OBJECT_BYTES


def test_packaged_schema_matches_valid_reserved_contracts():
    concepts, _, _ = projected()
    directory = Path(__file__).parents[1] / "src/llm_wiki_cli/schemas"
    for extension, name in (
        (ie.IMPLEMENTATION_KEY, "evidence"),
        (ie.DECLARATIONS_KEY, "declarations"),
    ):
        schema = json.loads(
            (directory / f"llm-wiki-implementation-{name}-v1.schema.json").read_text()
        )
        Draft202012Validator.check_schema(schema)
        for concept in concepts:
            value = concept["extensions"][extension]
            assert list(Draft202012Validator(schema).iter_errors(value)) == []
            corrupted = {**value, "schema_version": "future/v2"}
            assert list(Draft202012Validator(schema).iter_errors(corrupted))


@pytest.mark.parametrize(
    "mutation",
    [
        lambda v: v.update(coordinate={}),
        lambda v: v.update(live_comparison_performed=1),
        lambda v: v.update(state="unchanged"),
        lambda v: v.update(reason="matching-executable-syntax"),
        lambda v: v.update(analysis_scope="full-source"),
        lambda v: v.update(limitations=[]),
        lambda v: v.update(source_changed=True),
    ],
)
def test_compact_summary_closed_fields_and_snapshot_flags(mutation):
    comparison = compare(owner(captured()), None)
    summary = ie.compact_implementation_summary(comparison)
    assert set(summary) == ie.SUMMARY_FIELDS
    assert "recorded" not in summary and "coordinate" not in summary
    assert ie.compact_implementation_summary(comparison.to_payload()) == summary
    mutation(summary)
    with pytest.raises(ValueError):
        ie.validate_implementation_summary(summary)


@pytest.mark.parametrize("basis", [None, "unqualified", "sha256:" + "f" * 64])
def test_absent_or_changed_live_surrounding_analysis_never_earns_verdict(basis):
    evidence = owner(captured())
    result = ie.compare_implementation_observations(
        evidence,
        evidence,
        analysis_scope="selected-source",
        expected_analysis_hash=basis,
    )
    assert result.reason == "producer-incompatible"
    assert result.state == "unavailable" and not result.live_comparison_performed


def test_full_record_collection_rejects_contradictory_primary_and_supplement():
    concepts, _, _ = projected()
    concepts[1]["extensions"][ie.IMPLEMENTATION_KEY]["executable_hash"] = OTHER
    with pytest.raises(ValueError, match="contradictory observations"):
        ie.validate_implementation_collection(concepts, producer=producer())


@pytest.mark.parametrize("corruption", ["source", "mapping", "copied-line"])
def test_selected_native_read_rejects_rehashed_inconsistent_commit(
    tmp_path, monkeypatch, capsys, corruption
):
    from llm_wiki_cli import api
    from llm_wiki_cli.services.knowledge_storage import ROOT_FILENAME
    from llm_wiki_cli.services.knowledge_loader import load_knowledge_state
    from llm_wiki_cli.services.knowledge_model import knowledge_index_to_payload
    from llm_wiki_cli.services.knowledge_storage import (
        build_knowledge_store,
        KnowledgeStorageError,
        digest,
    )
    from llm_wiki_cli.services.knowledge_storage_access import capture_knowledge_slice
    from llm_wiki_cli.services.manifest_storage import build_manifest_store
    from llm_wiki_cli.services.sync_manifest import MANIFEST_FILENAME

    monkeypatch.chdir(tmp_path)
    Path("src").mkdir()
    Path("src/policy.py").write_text(SOURCE)
    api.bootstrap_wiki("src", "wiki")
    capsys.readouterr()
    loaded = load_knowledge_state(Path("wiki"))
    assert loaded.knowledge is not None
    knowledge = knowledge_index_to_payload(loaded.knowledge)
    manifest = json.loads((Path("wiki") / MANIFEST_FILENAME).read_text())
    if corruption == "source":
        # Keep every redundant observation coherent but falsify the per-source
        # commitment. The aggregate snapshot and honest manifest stay original.
        for concept in knowledge["concepts"]:
            extensions = concept.get("extensions", {})
            if ie.IMPLEMENTATION_KEY in extensions:
                extensions[ie.IMPLEMENTATION_KEY]["source_hash"] = OTHER
            for row in extensions.get(ie.DECLARATIONS_KEY, {}).get("observations", []):
                row["evidence"]["source_hash"] = OTHER
    elif corruption == "mapping":
        manifest["page_source_mappings"]["entities/Batch.md"]["occurrence"] = 2
    else:
        module = next(
            c
            for c in knowledge["concepts"]
            if c["document"]["canonical_path"] == "modules/policy.md"
        )
        rows = module["extensions"][ie.DECLARATIONS_KEY]["observations"]
        method = next(
            r
            for r in rows
            if r["evidence"]["coordinate"]["qualified_owner"] == "Batch.cap"
        )
        method["line"] += 1
    store = build_knowledge_store(knowledge)
    manifest["artifact_hashes"]["knowledge_index_hash"] = digest(store.root_bytes)
    indexed = build_manifest_store(manifest)
    wiki = Path("wiki")
    (wiki / ROOT_FILENAME).write_bytes(store.root_bytes)
    for path, raw in {**store.objects, **indexed.objects}.items():
        target = wiki / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(raw)
    (wiki / MANIFEST_FILENAME).write_bytes(indexed.root_bytes)
    before = {path: path.read_bytes() for path in wiki.rglob("*") if path.is_file()}
    with pytest.raises(KnowledgeStorageError, match="implementation"):
        capture_knowledge_slice(
            wiki,
            ["source:policy.py"]
            if corruption == "copied-line"
            else ["concept:llm-wiki://entities/Batch"],
        )
    assert before == {
        path: path.read_bytes() for path in wiki.rglob("*") if path.is_file()
    }


@pytest.mark.parametrize(
    "change",
    [
        "parent-occurrence",
        "parent-absent",
        "parent-scope",
        "copied-line",
        "copied-lineage",
    ],
)
def test_recorded_lineage_requires_real_parent_occurrence_and_duplicate_parity(change):
    concepts, _, _ = projected()
    module_rows = concepts[0]["extensions"][ie.DECLARATIONS_KEY]["observations"]
    child = next(
        r
        for r in module_rows
        if r["evidence"]["coordinate"]["qualified_owner"] == "Batch.cap"
    )
    if change in {"parent-occurrence", "parent-absent"}:
        child["lineage"][-1]["coordinate"]["occurrence"] = 999
    elif change == "parent-scope":
        child["lineage"][-1]["scope"] = "callable"
    elif change == "copied-line":
        child["line"] += 1
    else:
        # Same coordinate, actual parent, contradictory copied line ancestry.
        class_row = concepts[1]["extensions"][ie.DECLARATIONS_KEY]["observations"][0]
        class_row["lineage"][-1]["coordinate"]["occurrence"] = 2
    with pytest.raises(ValueError, match="lineage|parent|contradictory copied"):
        ie.validate_implementation_collection(concepts, producer=producer())


def test_scope_incompatibility_has_its_own_unavailable_reason():
    left = owner(captured())
    right = {**left, "scope": "class"}
    result = compare(left, right, analysis_scope="selected-source")
    assert result.state == "unavailable" and result.reason == "scope-incompatible"
    assert not result.live_comparison_performed


def test_full_artifact_parity_rejects_available_evidence_on_unmapped_retained_page(
    tmp_path, monkeypatch, capsys
):
    from llm_wiki_cli import api
    from llm_wiki_cli.services.knowledge_artifacts import (
        KnowledgeArtifactError,
        _validate_manifest_knowledge_parity,
    )
    from llm_wiki_cli.services.knowledge_loader import load_knowledge_state
    from llm_wiki_cli.services.knowledge_model import StructuralFacet
    from llm_wiki_cli.services.sync_manifest import (
        ManifestTombstone,
        TOMBSTONE_UNKNOWN_PROVENANCE,
    )

    monkeypatch.chdir(tmp_path)
    Path("src").mkdir()
    Path("src/policy.py").write_text(SOURCE)
    api.bootstrap_wiki("src", "wiki")
    capsys.readouterr()
    loaded = load_knowledge_state(Path("wiki"))
    assert (
        loaded.knowledge is not None
        and loaded.manifest_basis is not None
        and loaded.surface is not None
    )
    manifest = loaded.manifest_basis
    retained = "modules/policy.md"
    manifest = replace(
        manifest,
        page_source_mappings={
            k: v for k, v in manifest.page_source_mappings.items() if k != retained
        },
        evidence_baselines={
            k: v for k, v in manifest.evidence_baselines.items() if k != retained
        },
        tombstones={
            **manifest.tombstones,
            retained: ManifestTombstone(
                reason=TOMBSTONE_UNKNOWN_PROVENANCE,
                unknown_reason="evidence-not-recorded",
            ),
        },
    )
    concepts = tuple(
        replace(c, facets=replace(c.facets, structure=StructuralFacet()))
        if c.document.canonical_path == retained
        else c
        for c in loaded.knowledge.concepts
    )
    knowledge = replace(loaded.knowledge, concepts=concepts)
    # The enclosing legacy structural/tombstone rules accept this retained page.
    manifest.to_payload()
    with pytest.raises(
        KnowledgeArtifactError, match="committed owner mapping is absent"
    ):
        _validate_manifest_knowledge_parity(manifest, loaded.surface, knowledge)


@pytest.mark.parametrize(
    "mutation",
    [
        lambda v: v.update(extra=True),
        lambda v: v.update(scope="module"),
        lambda v: v["coordinate"].update(occurrence=True),
        lambda v: v["live"].update(comparison_id=OTHER),
        lambda v: v.update(source_changed=False),
        lambda v: v.update(documentation_changed=True),
        lambda v: v.update(state="unchanged", reason="matching-executable-syntax"),
        lambda v: v.update(recorded=None),
    ],
)
def test_full_comparison_validator_rejects_forged_verdict_shape_and_deltas(mutation):
    left = owner(captured())
    right = owner(captured(SOURCE.replace("values[:limit]", "values[:limit - 1]")))
    payload = compare(left, right, analysis_scope="selected-source").to_payload()
    assert ie.validate_implementation_comparison(payload) == payload
    mutation(payload)
    with pytest.raises(ValueError):
        ie.validate_implementation_comparison(payload)


def test_full_comparison_validator_retains_explicit_contradiction_without_claiming_capture_proof():
    left = owner(captured())
    right = {**left, "executable_hash": OTHER}
    result = compare(left, right, analysis_scope="full-inventory")
    assert (
        ie.validate_implementation_comparison(result.to_payload())["reason"]
        == "identical-source-observation-mismatch"
    )
    snapshot = compare(left, None).to_payload()
    snapshot["live"] = left
    with pytest.raises(ValueError, match="snapshot cannot carry"):
        ie.validate_implementation_comparison(snapshot)


def test_late_mapped_class_and_method_are_truthful_bounded_gaps():
    text = (
        "\n".join(f"def f{i}(): return {i}" for i in range(150))
        + "\nclass Batch:\n def cap(self): return 2\n"
    )
    concepts, capture, _ = projected(text)
    assert capture["bounds"]["truncated"]
    late_class = concepts[1]
    assert ie.IMPLEMENTATION_KEY not in late_class["extensions"]
    gap = late_class["extensions"][ie.DECLARATIONS_KEY]
    assert gap["observations"] == []
    assert gap["bounds"]["total"] is None and gap["bounds"]["omitted"] is None
    assert gap["bounds"]["returned"] == 0 and gap["bounds"]["truncated"]
    assert gap["bounds"]["reason"] in {"object-limit", "observation-limit"}
    report = ie.compare_knowledge_implementation(
        concepts,
        pi.envelope({"policy.py": capture}),
        analysis_scope="selected-source",
        analysis_compatibility_hash=pi.analysis_identity(issuer()),
    )
    selected = report.by_locator["entities/Batch.md"]
    assert selected.state == "unavailable" and selected.truncated
    assert selected.coordinate == {
        "source_path": "policy.py",
        "qualified_owner": "Batch",
        "occurrence": 1,
    }
    assert selected.scope == "class"
    assert selected.recorded is None and selected.live is None
    assert selected.reason in {"observation-limit", "object-limit"}
    method = ie.select_implementation_comparison(report, "policy.py:Batch.cap#1")
    assert method.state == "unavailable" and method.truncated
    assert method.reason == "observation-limit"
    assert not method.live_comparison_performed
    # An omitted method's type/coordinate is not fabricated from its name.
    assert method.coordinate is None and method.scope is None
    snapshot = ie.compare_knowledge_implementation(concepts, None).by_locator[
        "entities/Batch.md"
    ]
    assert snapshot.reason == "live-evaluation-not-performed" and snapshot.truncated
    assert snapshot.scope == "class" and snapshot.coordinate == selected.coordinate
    assert (
        ie.validate_implementation_comparison(snapshot.to_payload())
        == snapshot.to_payload()
    )


def test_selected_collection_rejects_individually_valid_copied_detail_line_conflict():
    concepts, _, _ = projected()
    class_detail = concepts[1]["extensions"][ie.DECLARATIONS_KEY]["observations"][0]
    class_detail["line"] += 1
    for concept in concepts:
        ie.validate_concept_implementation(concept, producer=producer())
    with pytest.raises(ValueError, match="contradictory copied line or lineage"):
        ie.validate_implementation_collection(
            concepts, producer=producer(), complete=False
        )


def test_live_bound_omission_preserves_unavailable_diagnostic_for_previously_recorded_method():
    concepts, _, _ = projected()
    grown = "\n".join(f"def f{i}(): return {i}" for i in range(150)) + "\n" + SOURCE
    live = captured(grown)
    report = ie.compare_knowledge_implementation(
        concepts,
        pi.envelope({"policy.py": live}),
        analysis_scope="selected-source",
        analysis_compatibility_hash=pi.analysis_identity(issuer()),
    )
    result = ie.select_implementation_comparison(report, "policy.py:Batch.cap#1")
    assert result.reason == "observation-limit" and result.truncated
    assert result.state == "unavailable" and not result.live_comparison_performed
    assert (
        ie.validate_implementation_comparison(result.to_payload())
        == result.to_payload()
    )


def test_selected_nested_class_allows_explicitly_outside_projection_ancestors():
    text = "class Outer:\n class Inner:\n  def method(self): return 1\n"
    capture = captured(text)
    mappings = {
        "entities/Inner.md": ManifestPageSource(
            scope="entity",
            source_path="policy.py",
            entity_name="Outer.Inner",
            occurrence=1,
        )
    }
    extensions = ie.project_concept_implementations(
        pi.envelope({"policy.py": capture}),
        mappings,
        producer=producer(),
        source_content_hashes={"policy.py": capture["source_hash"]},
    )
    concepts = [
        {
            "locator": "entities/Inner.md",
            "document": {
                "page_kind": "entities",
                "canonical_path": "entities/Inner.md",
            },
            "extensions": extensions["entities/Inner.md"],
        }
    ]
    ie.validate_implementation_collection(concepts, producer=producer(), complete=False)
    with pytest.raises(ValueError, match="ancestor is absent"):
        ie.validate_implementation_collection(
            concepts, producer=producer(), complete=True
        )


@pytest.mark.parametrize("snapshot", [False, True])
def test_full_comparison_validator_requires_included_observation_truncation(snapshot):
    text = "\n".join(f"def f{i}(): return {i}" for i in range(150)) + "\n"
    evidence = owner(captured(text), "__module__")
    assert evidence["aggregation"]["truncated"]
    payload = compare(
        evidence,
        None if snapshot else evidence,
        analysis_scope="snapshot" if snapshot else "selected-source",
    ).to_payload()
    assert payload["truncated"] is True
    ie.validate_implementation_comparison(payload)
    # Both observations remain valid and hash-bound; only the summary lies.
    payload["truncated"] = False
    with pytest.raises(ValueError, match="truncation must be disclosed"):
        ie.validate_implementation_comparison(payload)
