"""Captured executable syntax stays scoped, bounded and distinct from behavior."""

from __future__ import annotations

import ast
from copy import deepcopy
import hashlib
import json
from pathlib import Path
from typing import Any

import pytest

from llm_wiki_cli.extractors.python_extractor import PythonExtractor
from llm_wiki_cli.services import python_implementation as impl
from llm_wiki_cli.services import extraction_service as extraction
from llm_wiki_cli.services.analysis_capture import _issued
from llm_wiki_cli.services.extraction_service import (
    InventoryRequest,
    get_inventory_result,
)
from llm_wiki_cli.services.inventory_cache import InventoryCacheOptions
from llm_wiki_cli.services.source_snapshot import (
    SourceSnapshotMutationError,
    build_source_snapshot,
)

HASH = "sha256:" + "a" * 64
SOURCE = 'class Batch:\n    """Keep all permitted items."""\n    def cap(self, values, limit=3):\n        return values[:limit]\n\ndef sibling(value=9):\n    return value + 1\n'


def captured(text: str, **options: Any) -> dict:
    data = text.encode("utf-8")
    tree = ast.parse(text)
    return impl.capture(
        tree,
        data,
        "policy.py",
        configured=impl.producer(HASH),
        parsed_source=text,
        **options,
    )


def by_owner(result, owner, occurrence=1):
    return next(
        row["evidence"]
        for row in result["observations"]
        if row["evidence"]["coordinate"]["qualified_owner"] == owner
        and row["evidence"]["coordinate"]["occurrence"] == occurrence
    )


@pytest.mark.parametrize(
    "before,after",
    [
        ("values[:limit]", "values[:limit - 1]"),
        ("limit=3", "limit=4"),
        ("value + 1", "value * 1"),
    ],
)
def test_meaningful_syntax_changes_update_selected_and_parent_digests(before, after):
    first, second = captured(SOURCE), captured(SOURCE.replace(before, after))
    owner = "sibling" if before == "value + 1" else "Batch.cap"
    assert (
        by_owner(first, owner)["executable_hash"]
        != by_owner(second, owner)["executable_hash"]
    )
    assert (
        by_owner(first, "__module__")["executable_hash"]
        != by_owner(second, "__module__")["executable_hash"]
    )
    unchanged = "Batch.cap" if owner == "sibling" else "sibling"
    assert (
        by_owner(first, unchanged)["executable_hash"]
        == by_owner(second, unchanged)["executable_hash"]
    )


def test_formatting_line_shifts_and_source_docstrings_do_not_become_executable_changes():
    first = captured(SOURCE)
    formatting = captured(
        "\n# shifted\n" + SOURCE.replace("values[:limit]", "values[ : limit ]")
    )
    documentation = captured(
        SOURCE.replace("Keep all permitted items.", "A newly documented rationale.")
    )
    for owner in ("__module__", "Batch", "Batch.cap", "sibling"):
        assert (
            by_owner(first, owner)["executable_hash"]
            == by_owner(formatting, owner)["executable_hash"]
        )
        assert (
            by_owner(first, owner)["executable_hash"]
            == by_owner(documentation, owner)["executable_hash"]
        )
    assert (
        by_owner(first, "Batch")["documentation_hash"]
        != by_owner(documentation, "Batch")["documentation_hash"]
    )
    assert (
        by_owner(first, "Batch.cap")["documentation_hash"]
        == by_owner(documentation, "Batch.cap")["documentation_hash"]
    )
    assert first["source_hash"] != formatting["source_hash"]


@pytest.mark.parametrize(
    "text,mutated,owner",
    [
        (
            "@decorate(1)\ndef run(value=3):\n    return value\n",
            "@decorate(2)\ndef run(value=3):\n    return value\n",
            "run",
        ),
        (
            "def run(value):\n    if value:\n        return 1\n    return 2\n",
            "def run(value):\n    if not value:\n        return 1\n    return 2\n",
            "run",
        ),
        (
            "VALUE=1\ndef run():\n    return VALUE\n",
            "VALUE=2\ndef run():\n    return VALUE\n",
            "__module__",
        ),
        (
            "from first import VALUE\ndef run():\n    return VALUE\n",
            "from second import VALUE\ndef run():\n    return VALUE\n",
            "__module__",
        ),
    ],
)
def test_decorators_defaults_control_flow_and_module_bindings_remain_meaningful(
    text, mutated, owner
):
    before, after = captured(text), captured(mutated)
    assert (
        by_owner(before, owner)["executable_hash"]
        != by_owner(after, owner)["executable_hash"]
    )
    if owner == "__module__":
        assert (
            by_owner(before, "run")["executable_hash"]
            == by_owner(after, "run")["executable_hash"]
        )
        assert (
            "dependencies-and-runtime-behavior-not-evaluated"
            in impl.envelope({"policy.py": after})["limitations"]
        )


def test_nested_duplicate_coordinates_keep_exact_parent_lineage_and_sibling_isolation():
    text = "class Repeated:\n    def touch(self):\n        def inner():\n            return 1\n        return inner()\n\nclass Repeated:\n    def touch(self):\n        def inner():\n            return 2\n        return inner()\n"
    result = captured(text)
    keys = [
        (
            row["evidence"]["coordinate"]["qualified_owner"],
            row["evidence"]["coordinate"]["occurrence"],
        )
        for row in result["observations"]
    ]
    assert len(keys) == len(set(keys))
    assert ("Repeated.touch.inner", 1) in keys and ("Repeated.touch.inner", 2) in keys
    second = next(
        row
        for row in result["observations"]
        if row["evidence"]["coordinate"]["qualified_owner"] == "Repeated.touch.inner"
        and row["evidence"]["coordinate"]["occurrence"] == 2
    )
    assert [
        (a["coordinate"]["qualified_owner"], a["coordinate"]["occurrence"], a["scope"])
        for a in second["lineage"]
    ] == [
        ("__module__", 1, "module"),
        ("Repeated", 2, "class"),
        ("Repeated.touch", 2, "callable"),
    ]
    edited = captured(text.replace("return 2", "return 7"))
    assert (
        by_owner(result, "Repeated.touch", 1)["executable_hash"]
        == by_owner(edited, "Repeated.touch", 1)["executable_hash"]
    )
    assert (
        by_owner(result, "Repeated.touch", 2)["executable_hash"]
        != by_owner(edited, "Repeated.touch", 2)["executable_hash"]
    )


def test_capture_never_mutates_borrowed_ast_or_parses_or_imports_application(
    monkeypatch,
):
    text = 'raise RuntimeError("must never execute")\ndef run():\n    """Docstring."""\n    return 3\n'
    tree = ast.parse(text)
    before = ast.dump(tree, include_attributes=True)
    monkeypatch.setattr(
        ast, "parse", lambda *args, **kwargs: pytest.fail("capture reparsed source")
    )
    result = impl.capture(
        tree,
        text.encode(),
        "policy.py",
        configured=impl.producer(HASH),
        parsed_source=text,
    )
    assert by_owner(result, "run")["status"] == "available"
    assert ast.dump(tree, include_attributes=True) == before


@pytest.mark.parametrize(
    "literal", ["True", "1", "1.0", "1j", "b'one'", "'one'", "...", "0.0", "-0.0"]
)
def test_tagged_constants_emit_finite_json_and_distinct_scalar_identities(literal):
    result = captured(f"def value():\n    return {literal}\n")
    assert by_owner(result, "value")["status"] == "available"
    json.dumps(result, allow_nan=False)


def test_constant_types_and_signed_zero_are_not_coerced_and_overflow_is_unavailable():
    values = [
        by_owner(captured(f"def value():\n    return {literal}\n"), "value")[
            "executable_hash"
        ]
        for literal in (
            "True",
            "1",
            "1.0",
            "1j",
            "b'one'",
            "'one'",
            "...",
            "0.0",
            "-0.0",
        )
    ]
    assert len(set(values)) == len(values)
    overflow = captured("VALUE=1e999\ndef safe():\n    return 3\n")
    assert by_owner(overflow, "__module__")["status"] == "unavailable"
    assert by_owner(overflow, "__module__")["executable_hash"] is None
    assert by_owner(overflow, "safe")["status"] == "available"
    json.dumps(overflow, allow_nan=False)


def test_record_and_object_bounds_disclose_omission_without_losing_full_module_aggregate():
    text = "\n".join(f"def method_{i}():\n    return {i}\n" for i in range(200))
    before, after = captured(text), captured(text.replace("return 199", "return 999"))
    assert before["bounds"]["truncated"] and before["bounds"]["omitted"] > 0
    assert len(before["observations"]) <= 128
    assert len(impl.canonical_bytes(before)) <= 65536
    assert by_owner(before, "__module__")["aggregation"]["complete_scope"] is True
    assert (
        by_owner(before, "__module__")["executable_hash"]
        != by_owner(after, "__module__")["executable_hash"]
    )
    assert (
        by_owner(before, "__module__")["aggregation"]["observations_returned"]
        == len(before["observations"]) - 1
    )


def test_class_aggregate_includes_omitted_method_129_and_later():
    text = "class Wide:\n" + "\n".join(
        f"    def method_{i}(self):\n        return {i}\n" for i in range(200)
    )
    before, after = captured(text), captured(text.replace("return 199", "return 999"))
    assert before["bounds"]["truncated"]
    assert by_owner(before, "Wide")["aggregation"]["complete_scope"] is True
    assert (
        by_owner(before, "Wide")["executable_hash"]
        != by_owner(after, "Wide")["executable_hash"]
    )


@pytest.mark.parametrize(
    "path",
    [".", "../policy.py", "/policy.py", "folder/./policy.py", "bad\n.py", "bad\x00.py"],
)
def test_nonportable_source_paths_are_rejected(path):
    with pytest.raises(ValueError, match="portable"):
        impl.capture(
            ast.parse("pass"),
            b"pass",
            path,
            configured=impl.producer(HASH),
            parsed_source="pass",
        )


def test_long_selector_is_an_explicit_gap_and_unicode_identifiers_remain_valid():
    name = "é" * 2200
    result = captured(f"def {name}():\n    return 3\n")
    assert (
        result["bounds"]["truncated"]
        and result["bounds"]["reason"] == "selector-limit-or-ambiguous-owner"
    )
    assert (
        len(result["observations"]) == 1
        and by_owner(result, "__module__")["status"] == "available"
    )
    short = captured("def café():\n    return 3\n")
    assert by_owner(short, "café")["status"] == "available"
    minimum = impl.capture(
        ast.parse("pass"),
        b"pass",
        "é" * 2200 + ".py",
        configured=impl.producer(HASH),
        parsed_source="pass",
    )
    assert minimum["observations"] == [] and minimum["status"] == "unavailable"


def test_reserved_module_owner_cannot_collide_with_a_callable_coordinate():
    result = captured("def __module__():\n    return 3\n")
    assert result["bounds"]["truncated"]
    assert (
        len(result["observations"]) == 1
        and result["observations"][0]["evidence"]["scope"] == "module"
    )


def test_analysis_identity_requires_issuer_and_binds_surrounding_code_not_source():
    rows = {
        name: {"implementation": HASH, "runtime": HASH, "provenance": {}}
        for name in ("agent-wiki-cli", "llm-wiki/extractor/python")
    }
    assert impl.analysis_identity(rows) is None
    first = impl.analysis_identity(_issued(rows))
    changed = deepcopy(rows)
    changed["llm-wiki/extractor/python"]["implementation"] = "sha256:" + "b" * 64
    assert first is not None and first != impl.analysis_identity(_issued(changed))
    assert impl.analysis_identity(_issued({})) is None


@pytest.mark.parametrize("change", ["parser", "algorithm", "language"])
def test_unsupported_producers_do_not_get_available_digests(change):
    configured = impl.producer(HASH)
    assert configured is not None
    configured[change] = {
        "parser": "pypy-ast",
        "algorithm": "future-ast/v2",
        "language": "go",
    }[change]
    text = "def run():\n    return 3\n"
    result = impl.capture(
        ast.parse(text),
        text.encode(),
        "policy.py",
        configured=configured,
        parsed_source=text,
    )
    assert all(
        row["evidence"]["status"] == "unavailable"
        and row["evidence"]["executable_hash"] is None
        for row in result["observations"]
    )


def test_missing_source_and_unknown_analysis_are_explicit_not_complete_empty_evidence():
    missing = impl.capture(None, None, "policy.py", configured=impl.producer(HASH))
    assert by_owner(missing, "__module__")["unavailable_reason"] == "missing-source"
    unknown = impl.capture(
        ast.parse(SOURCE),
        SOURCE.encode(),
        "policy.py",
        configured=None,
        parsed_source=SOURCE,
    )
    assert unknown["status"] == "unavailable" and unknown["producer"] is None
    assert unknown["observations"] == [] and unknown["bounds"]["omitted"] > 0


@pytest.mark.parametrize(
    "data,expected",
    [
        (b"def value():\n    return 1\n", True),
        ('def value():\n    return "é"\n'.encode(), True),
        (b'# coding: latin-1\ndef value():\n    return "\xe9"\n', True),
        (b'# coding: cp1252\ndef value():\n    return "\x80"\n', True),
        ('# coding: latin-1\ndef value():\n    return "é"\n'.encode(), False),
        ('# coding: ascii\ndef value():\n    return "é"\n'.encode(), False),
        (b"\xef\xbb\xbfdef value():\n    return 1\n", False),
        (b'def value():\n    return "\xe9"\n', False),
    ],
)
def test_scanner_decode_must_match_python_cookie_and_bom_semantics(
    tmp_path, data, expected
):
    (tmp_path / "policy.py").write_bytes(data)
    extractor = PythonExtractor()
    extractor.extract(
        str(tmp_path),
        deep=True,
        capture_implementation_observations=True,
        implementation_analysis_hash=HASH,
    )
    result = extractor.last_implementation_observations
    assert result is not None
    source = result["files"]["policy.py"]
    assert source["source_hash"] == "sha256:" + hashlib.sha256(data).hexdigest()
    assert (by_owner(source, "__module__")["status"] == "available") is expected


def test_optin_reuses_parse_count_and_preserves_capture_off_inventory(
    tmp_path, monkeypatch
):
    (tmp_path / "policy.py").write_text(SOURCE)
    actual = ast.parse
    calls = []

    def count(*args, **kwargs):
        calls.append(1)
        return actual(*args, **kwargs)

    monkeypatch.setattr(ast, "parse", count)
    ordinary = PythonExtractor().extract(str(tmp_path), deep=True)
    baseline = len(calls)
    calls.clear()
    extractor = PythonExtractor()
    captured_inventory = extractor.extract(
        str(tmp_path),
        deep=True,
        capture_implementation_observations=True,
        implementation_analysis_hash=HASH,
    )
    assert ordinary == captured_inventory and len(calls) == baseline
    assert extractor.last_implementation_observations is not None
    extractor.extract(str(tmp_path), deep=True)
    assert extractor.last_implementation_observations is None


def test_inventory_capture_binds_issued_analysis_and_exact_snapshot_hash(tmp_path):
    (tmp_path / "policy.py").write_text(SOURCE)
    snapshot = build_source_snapshot(tmp_path, coherent=True)
    result = get_inventory_result(
        InventoryRequest(
            src_dir=tmp_path,
            deep=True,
            include_plugins=False,
            source_snapshot=snapshot,
            capture_implementation_observations=True,
        )
    )
    sidecar = result.implementation_observations
    assert sidecar is not None
    source = sidecar["files"]["policy.py"]
    evidence = by_owner(source, "Batch.cap")
    assert evidence["status"] == "available"
    assert evidence["producer"][
        "analysis_compatibility_hash"
    ] == impl.analysis_identity(result.analysis_components)
    assert evidence["source_hash"] == snapshot.captured_content_hashes["policy.py"]


def test_requested_capture_bypasses_legacy_warm_cache_without_changing_normal_inventory(
    tmp_path,
):
    (tmp_path / "policy.py").write_text(SOURCE)
    options = InventoryCacheOptions(
        enabled=True, cache_dir=str(tmp_path / "cache"), stats_enabled=True
    )
    before = get_inventory_result(
        InventoryRequest(
            src_dir=tmp_path, deep=True, include_plugins=False, cache_options=options
        )
    )
    after = get_inventory_result(
        InventoryRequest(
            src_dir=tmp_path,
            deep=True,
            include_plugins=False,
            cache_options=options,
            capture_implementation_observations=True,
        )
    )
    assert (
        before.inventory == after.inventory
        and before.implementation_observations is None
    )
    assert after.implementation_observations is not None
    assert (
        by_owner(after.implementation_observations["files"]["policy.py"], "Batch.cap")[
            "status"
        ]
        == "available"
    )


def test_custom_python_override_cannot_supply_forged_builtin_sidecar(
    tmp_path, monkeypatch
):
    (tmp_path / "policy.py").write_text(SOURCE)

    class Custom:
        last_implementation_observations = impl.envelope(
            {"policy.py": captured(SOURCE)}
        )

        def extract(self, **kwargs):
            return {"policy.py": {"language": "python", "classes": [], "functions": []}}

    monkeypatch.setattr(
        extraction, "runtime_project_plugins_enabled", lambda *args, **kwargs: True
    )
    monkeypatch.setattr(
        extraction, "_selected_runtime_plugin_components", lambda *args: ((), tmp_path)
    )
    monkeypatch.setattr(
        extraction,
        "get_extractor_registry",
        lambda **kwargs: {"python": "custom:Python"},
    )
    monkeypatch.setattr(extraction, "_load_extractor", lambda *args: Custom())
    result = get_inventory_result(
        InventoryRequest(
            src_dir=tmp_path, deep=True, capture_implementation_observations=True
        )
    )
    assert result.implementation_observations is not None
    gap = result.implementation_observations["files"]["policy.py"]
    assert (
        gap["producer"] is None
        and gap["observations"] == []
        and gap["reason"] == "unsupported-producer"
    )


@pytest.mark.parametrize("tamper", ["row-source", "row-producer", "file-producer"])
def test_builtin_sidecar_scope_and_producer_must_match_issued_capture(
    tmp_path, monkeypatch, tamper
):
    (tmp_path / "policy.py").write_text(SOURCE)
    original = PythonExtractor.extract

    def altered(self, *args, **kwargs):
        result = original(self, *args, **kwargs)
        sidecar = self.last_implementation_observations
        if sidecar is not None:
            file = sidecar["files"]["policy.py"]
            if tamper == "row-source":
                file["observations"][0]["evidence"]["source_hash"] = (
                    "sha256:" + "b" * 64
                )
            elif tamper == "row-producer":
                file["observations"][0]["evidence"]["producer"] = {
                    **file["producer"],
                    "analysis_compatibility_hash": HASH,
                }
            else:
                file["producer"] = {
                    **file["producer"],
                    "analysis_compatibility_hash": HASH,
                }
        return result

    monkeypatch.setattr(PythonExtractor, "extract", altered)
    with pytest.raises((SourceSnapshotMutationError, ValueError)):
        get_inventory_result(
            InventoryRequest(
                src_dir=tmp_path,
                deep=True,
                include_plugins=False,
                capture_implementation_observations=True,
            )
        )


def test_snapshot_raw_hash_mismatch_aborts_publication(tmp_path, monkeypatch):
    path = tmp_path / "policy.py"
    path.write_text(SOURCE)
    snapshot = build_source_snapshot(tmp_path, coherent=True)
    original = Path.read_bytes

    def changed(self):
        return (
            SOURCE.replace("values[:limit]", "values[:limit - 1]").encode()
            if self == path
            else original(self)
        )

    monkeypatch.setattr(Path, "read_bytes", changed)
    with pytest.raises(SourceSnapshotMutationError):
        get_inventory_result(
            InventoryRequest(
                src_dir=tmp_path,
                deep=True,
                include_plugins=False,
                source_snapshot=snapshot,
                capture_implementation_observations=True,
            )
        )


@pytest.mark.parametrize("text", ["VALUE=1e999\ndef safe():\n    return 3\n", SOURCE])
def test_final_partial_or_unavailable_metadata_is_recounted_at_byte_boundary(
    monkeypatch, text
):
    full = captured(text)
    limit = len(impl.canonical_bytes(full)) - 1
    monkeypatch.setattr(impl, "MAX_OBJECT_BYTES", limit)
    bounded = captured(text)
    assert len(impl.canonical_bytes(bounded)) <= limit
    assert bounded["bounds"]["truncated"] and bounded["bounds"]["omitted"] > 0
    assert bounded["bounds"]["returned"] == len(bounded["observations"])
    assert (
        by_owner(bounded, "__module__")["executable_hash"]
        == by_owner(full, "__module__")["executable_hash"]
    )


def test_deep_owned_ast_has_iterative_declaration_walk_and_explicit_digest_gap():
    # This is an owned AST stress control, not independent source/AST verification.
    expression = ast.Constant(value=1)
    for _ in range(1500):
        expression = ast.UnaryOp(op=ast.UAdd(), operand=expression)
    safe = ast.parse("def safe():\n    return 3\n").body[0]
    tree = ast.Module(body=[ast.Expr(value=expression), safe], type_ignores=[])
    result = impl.capture(
        tree, b"pass", "policy.py", configured=impl.producer(HASH), parsed_source="pass"
    )
    assert by_owner(result, "__module__")["status"] == "unavailable"
    assert by_owner(result, "__module__")["unavailable_reason"] == "unsupported-syntax"
    assert by_owner(result, "safe")["status"] == "available"
    assert result["bounds"]["total"] == 2


def test_missing_precaptured_analysis_is_not_reissued_during_completion(
    tmp_path, monkeypatch
):
    from llm_wiki_cli.services import analysis_capture

    (tmp_path / "policy.py").write_text(SOURCE)
    calls = []

    def captured_once(*args, **kwargs):
        calls.append(1)
        return (
            None
            if len(calls) == 1
            else _issued(
                {
                    name: {"implementation": HASH, "runtime": HASH, "provenance": {}}
                    for name in ("agent-wiki-cli", "llm-wiki/extractor/python")
                }
            )
        )

    monkeypatch.setattr(analysis_capture, "capture_analysis", captured_once)
    result = get_inventory_result(
        InventoryRequest(
            src_dir=tmp_path,
            deep=True,
            include_plugins=False,
            capture_implementation_observations=True,
        )
    )
    assert len(calls) == 1 and result.analysis_components is None
    assert result.implementation_observations is not None
    gap = result.implementation_observations["files"]["policy.py"]
    assert (
        gap["producer"] is None
        and gap["reason"] == "unsupported-producer"
        and gap["observations"] == []
    )
