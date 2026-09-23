"""Freshness, ownership and retention controls for static-analysis inputs."""

import ast
import os
from pathlib import Path, PureWindowsPath
from typing import cast

import pytest

from tests.python_source_inventory import PythonSourceInventory
from tests import test_architecture_layers as guards


@pytest.fixture
def source(tmp_path):
    path = tmp_path / "module.py"
    path.write_text("value = 1\n", encoding="utf-8")
    return path


def value(module):
    return ast.literal_eval(module.tree.body[0].value)


def test_one_consumer_reuses_a_parse_and_releases_its_cache(source):
    inventory = PythonSourceInventory([source.parent])
    with inventory:
        assert inventory.module(source) is inventory.module(source)
        assert inventory.stats["parse_calls"] == inventory.stats["parse_hits"] == 1
        assert inventory.identity
    assert not inventory._parsed and not inventory._raw and not inventory._digests
    with pytest.raises(RuntimeError, match="not active"):
        inventory.module(source)
    with pytest.raises(RuntimeError, match="one consumer"):
        with inventory:
            pass


@pytest.mark.parametrize(
    "mutation", ["edit", "same-mtime", "replace", "add", "remove", "rename"]
)
def test_changed_inputs_cannot_finish_with_a_stale_pass(source, mutation):
    before = source.stat()
    with pytest.raises(AssertionError, match="changed during analysis"):
        with PythonSourceInventory([source.parent]) as inventory:
            inventory.module(source)
            if mutation in {"edit", "same-mtime"}:
                source.write_text("value = 2\n", encoding="utf-8")
                if mutation == "same-mtime":
                    os.utime(source, ns=(before.st_atime_ns, before.st_mtime_ns))
            elif mutation == "replace":
                replacement = source.with_suffix(".replacement")
                replacement.write_text("value = 2\n", encoding="utf-8")
                os.utime(replacement, ns=(before.st_atime_ns, before.st_mtime_ns))
                os.replace(replacement, source)
            elif mutation == "add":
                source.with_name("new.py").write_text("value = 2\n")
            elif mutation == "remove":
                source.unlink()
            else:
                source.rename(source.with_name("renamed.py"))


def test_next_consumer_sees_same_mtime_edits_and_added_files(source):
    before = source.stat()
    with PythonSourceInventory([source.parent]) as first:
        assert value(first.module(source)) == 1
        identity = first.identity
    source.write_text("value = 2\n", encoding="utf-8")
    os.utime(source, ns=(before.st_atime_ns, before.st_mtime_ns))
    extra = source.with_name("extra.py")
    extra.write_text("value = 3\n", encoding="utf-8")
    with PythonSourceInventory([source.parent]) as second:
        assert second.identity != identity
        assert value(second.module(source)) == 2
        assert extra in second.paths


def test_consumer_ast_mutation_cannot_contaminate_another_consumer(source):
    with PythonSourceInventory([source.parent]) as first:
        tree = first.module(source).tree
        tree.body.clear()
    with PythonSourceInventory([source.parent]) as second:
        assert value(second.module(source)) == 1
        assert second.module(source).tree is not tree


def test_parser_singletons_cannot_leak_between_consumers(source, monkeypatch):
    source.write_text("value = left + right\n", encoding="utf-8")
    with PythonSourceInventory([source.parent]) as first:
        operators = [
            node
            for node in first.module(source).nodes
            if isinstance(node, (ast.operator, ast.expr_context))
        ]
        assert operators
        for node in operators:
            monkeypatch.setattr(node, "owned_mutation", True, raising=False)
    with PythonSourceInventory([source.parent]) as second:
        assert not any(
            hasattr(node, "owned_mutation") for node in second.module(source).nodes
        )
    assert not any(
        hasattr(node, "owned_mutation")
        for node in ast.walk(ast.parse(source.read_text()))
    )


def test_owned_node_index_keeps_ast_walk_order_and_attributes(source):
    source.write_text(
        "values = [x + 1 for x in items if x > 0 and x != 3]\n", encoding="utf-8"
    )
    original = ast.parse(source.read_text(encoding="utf-8"), filename=str(source))
    with PythonSourceInventory([source.parent]) as inventory:
        parsed = inventory.module(source)
        assert [ast.dump(n, include_attributes=True) for n in parsed.nodes] == [
            ast.dump(n, include_attributes=True) for n in ast.walk(original)
        ]


def test_validation_normalizer_does_not_mutate_borrowed_nodes(source):
    source.write_text(
        "def _require_value(value):\n    result = value\n    return result\n"
    )
    with PythonSourceInventory([source.parent]) as inventory:
        module = inventory.module(source)
        before = ast.dump(module.tree, include_attributes=True)
        function = module.tree.body[0]
        assert isinstance(function, ast.FunctionDef)
        guards._validation_body_fingerprint(function)
        assert ast.dump(module.tree, include_attributes=True) == before


def test_private_fixture_roots_and_candidate_identities_stay_distinct(source):
    other = source.parent / "other"
    other.mkdir()
    path = other / source.name
    path.write_text("value = 2\n")
    with PythonSourceInventory([source.parent], candidate="first") as first:
        first_id = first.identity
        assert value(first.module(source)) == 1
    with PythonSourceInventory([other], candidate="first") as second:
        assert value(second.module(path)) == 2
        assert second.identity != first_id
    with PythonSourceInventory([source.parent], candidate="second") as third:
        assert third.identity != first_id


@pytest.mark.parametrize("budget", [0, 32, 1024])
def test_eviction_and_oversized_inputs_preserve_all_results(source, budget):
    for number in range(4):
        source.with_name(f"module{number}.py").write_text(f"value = {number}\n")
    with PythonSourceInventory(
        [source.parent],
        max_source_bytes=budget,
        max_ast_nodes=budget,
        max_cached_files=2,
    ) as inventory:
        for _ in range(2):
            for path in inventory.paths:
                assignment = ast.parse(path.read_text()).body[0]
                assert isinstance(assignment, ast.Assign)
                assert value(inventory.module(path)) == ast.literal_eval(
                    assignment.value
                )
        assert inventory.stats["peak_source_bytes"] <= budget
        assert inventory.stats["peak_ast_nodes"] <= budget
        assert len(inventory._parsed) <= 2 and len(inventory._raw) <= 2


def test_uncached_input_change_is_rejected_before_parsing(source):
    with pytest.raises(AssertionError, match="changed during analysis"):
        with PythonSourceInventory([source.parent], max_cached_files=0) as inventory:
            source.write_text("value = 2\n")
            inventory.module(source)


def test_source_errors_keep_their_filename_and_cleanup(source):
    source.write_text("def broken(:\n")
    inventory = PythonSourceInventory([source.parent])
    with pytest.raises(SyntaxError) as actual:
        with inventory:
            inventory.module(source)
    with pytest.raises(SyntaxError) as expected:
        ast.parse(source.read_text(encoding="utf-8"), filename=str(source))
    assert actual.value.args == expected.value.args
    assert not inventory._parsed and not inventory._raw


def test_exception_cleanup_does_not_mask_the_original_failure(source):
    inventory = PythonSourceInventory([source.parent])
    with pytest.raises(ValueError, match="owned failure"):
        with inventory:
            inventory.module(source)
            source.unlink()
            raise ValueError("owned failure")
    assert not inventory._parsed and not inventory._raw


@pytest.mark.parametrize(
    "raw", [b"value = 'caf\xc3\xa9'\r\n", b"value = 1\r", b"value = 1\n"]
)
def test_decoding_and_positions_match_read_text(source, raw):
    source.write_bytes(raw)
    with PythonSourceInventory([source.parent]) as inventory:
        assert ast.dump(
            inventory.module(source).tree, include_attributes=True
        ) == ast.dump(
            ast.parse(source.read_text(encoding="utf-8"), filename=str(source)),
            include_attributes=True,
        )


@pytest.mark.parametrize("budget", [-1, True, 1.5, float("nan"), None])
def test_invalid_retention_budgets_fail(source, budget):
    with pytest.raises(ValueError):
        PythonSourceInventory([source.parent], max_ast_nodes=budget)


def test_windows_path_equality_cannot_merge_distinct_lexical_files(source, monkeypatch):
    upper = cast(Path, PureWindowsPath("C:/source/Module.py"))
    lower = cast(Path, PureWindowsPath("C:/source/module.py"))
    assert upper == lower  # WindowsPath equality alone is insufficient.
    contents = {str(upper): b"value = 1\n", str(lower): b"value = 2\n"}
    monkeypatch.setattr(Path, "rglob", lambda self, pattern: iter([upper, lower]))
    monkeypatch.setattr(
        PythonSourceInventory, "_read", lambda self, path: contents[str(path)]
    )
    with PythonSourceInventory([source.parent]) as inventory:
        assert len(inventory.paths) == 2
        assert value(inventory.module(upper)) == 1
        assert value(inventory.module(lower)) == 2


def test_real_guard_refuses_a_mid_analysis_source_change(tmp_path, monkeypatch):
    validation = tmp_path / "validation.py"
    validation.write_text("def require_value(value):\n    return value\n")
    first = tmp_path / "first.py"
    first.write_text("def _required_first(value):\n    return str(value)\n")
    second = tmp_path / "second.py"
    second.write_text("def _required_second(value):\n    return str(value)\n")
    original = guards._validation_body_fingerprint

    def mutate(node):
        second.write_text("def _required_second(value):\n    return int(value)\n")
        return original(node)

    monkeypatch.setattr(guards, "_validation_body_fingerprint", mutate)
    with pytest.raises(AssertionError, match="changed during analysis"):
        guards._duplicated_unshared_validation_helpers(
            services_root=tmp_path, validation_path=validation
        )
