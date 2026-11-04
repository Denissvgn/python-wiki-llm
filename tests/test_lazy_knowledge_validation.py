"""Hot knowledge validators allocate diagnostics only for rejected values."""

from __future__ import annotations

import pytest

from llm_wiki_cli.services import knowledge_graph, knowledge_model, validation


def test_valid_knowledge_primitives_do_not_construct_domain_errors(monkeypatch):
    constructed = []
    for error_type in (
        knowledge_model.KnowledgeModelError,
        knowledge_graph.KnowledgeGraphError,
    ):
        original = error_type.__init__

        def counted(self, *args, _original=original, **kwargs):
            constructed.append(type(self))
            _original(self, *args, **kwargs)

        monkeypatch.setattr(error_type, "__init__", counted)

    digest = "sha256:" + "a" * 64
    for _ in range(100):
        assert knowledge_model._string("text", "record.text") == "text"
        assert knowledge_model._nonempty_string("name", "record.name") == "name"
        assert knowledge_model._object({"nested": True}, "record") == {"nested": True}
        assert knowledge_model._array([None], "records") == [None]
        assert knowledge_model._nonnegative_integer(0, "record.offset") == 0
        assert knowledge_model._positive_integer(1.0, "record.line") == 1
        assert knowledge_model._hash(digest, "record.hash") == digest
        assert knowledge_graph._name("name", "graph.name") == "name"
        assert knowledge_graph._object({"kind": "calls"}, "edge") == {"kind": "calls"}
        assert knowledge_graph._array([], "edges") == []
        assert knowledge_graph._nonnegative_int(0, "graph.total") == 0
        assert knowledge_graph._positive_int(1, "graph.limit") == 1
        assert knowledge_graph._hash(digest, "graph.hash") == digest
        assert knowledge_graph._enum("calls", ("calls", "reads"), "edge.kind") == "calls"
        knowledge_graph._only_fields({"kind": "calls"}, "edge", {"kind"}, required={"kind"})

    assert constructed == []


@pytest.mark.parametrize(
    ("invoke", "valid", "invalid"),
    [
        (lambda value, error: validation.require_string(value, error=error, error_context="field"), "", None),
        (lambda value, error: validation.require_list(value, error=error, error_context="field"), [], ()),
        (lambda value, error: validation.require_mapping(value, error=error, error_context="field"), {}, []),
        (lambda value, error: validation.require_nonempty_text(value, error=error, error_context="field"), "name", ""),
        (lambda value, error: validation.require_trimmed_text(value, error=error, error_context="field"), "name", " padded "),
        (lambda value, error: validation.require_int(value, error=error, error_context="field"), 0, True),
        (lambda value, error: validation.require_nonnegative_int(value, error=error, error_context="field"), 0, -1),
        (lambda value, error: validation.require_positive_int(value, invalid_error=error, error_context="field"), 1, 0),
        (lambda value, error: validation.require_bounded_integral_number(value, invalid_error=error, maximum=2, error_context="field"), 2.0, 3),
        (lambda value, error: validation.require_sha256(value, digest_error=error, error_context="field"), "sha256:" + "a" * 64, "sha256:bad"),
    ],
    ids=("string", "list", "mapping", "nonempty", "trimmed", "int", "nonnegative", "positive", "bounded", "digest"),
)
def test_shared_factory_is_lazy_and_receives_context(invoke, valid, invalid):
    calls = []

    def factory(context):
        calls.append(context)
        return ValueError(f"{context}: invalid")

    invoke(valid, factory)
    assert calls == []
    with pytest.raises(ValueError, match="^field: invalid$"):
        invoke(invalid, factory)
    assert calls == ["field"]


def test_mapping_factories_preserve_failure_precedence_and_unicode_cause():
    calls = []

    def factory(label):
        def create(context):
            calls.append((label, context))
            return ValueError(label)

        return create

    mapping_error = factory("mapping")
    key_error = factory("key")
    utf8_error = factory("utf8")

    def require_mapping(value):
        return validation.require_mapping(
            value,
            error=mapping_error,
            key_error=key_error,
            utf8_key_error=utf8_error,
            error_context="record",
            require_string_keys=True,
            require_utf8_keys=True,
        )

    assert require_mapping({"valid": True}) == {"valid": True}
    assert calls == []
    with pytest.raises(ValueError, match="^key$"):
        require_mapping({1: "invalid"})
    assert calls == [("key", "record")]
    with pytest.raises(ValueError, match="^utf8$") as raised:
        require_mapping({"\ud800": "invalid"})
    assert isinstance(raised.value.__cause__, UnicodeEncodeError)
    assert calls == [("key", "record"), ("utf8", "record")]


def test_domain_string_keeps_unicode_cause_and_field():
    with pytest.raises(knowledge_model.KnowledgeModelError) as raised:
        knowledge_model._string("\ud800", "record.text")
    assert raised.value.field == "record.text"
    assert raised.value.reason == "must contain only Unicode scalar values encodable as UTF-8"
    assert isinstance(raised.value.__cause__, UnicodeEncodeError)
    assert raised.value.__context__ is raised.value.__cause__


def test_callable_exception_instance_is_still_raised_unchanged():
    class CallableError(ValueError):
        def __call__(self, context):
            pytest.fail("an existing exception must not be treated as a factory")

    error = CallableError("original")
    with pytest.raises(CallableError) as raised:
        validation.require_string(None, error=error, error_context="field")
    assert raised.value is error


@pytest.mark.parametrize("value", ["", " padded ", None, 1])
def test_graph_enum_fast_path_keeps_nonempty_trimmed_choice_policy(value):
    choices = ("", " padded ", "valid")
    with pytest.raises(knowledge_graph.KnowledgeGraphError) as raised:
        knowledge_graph._enum(value, choices, "graph.kind")
    assert raised.value.field == "graph.kind"
    assert str(raised.value) == "graph.kind: must be one of '', ' padded ', 'valid'"


def test_graph_enum_keeps_explicit_control_character_policy():
    assert knowledge_graph._enum("line\nbreak", ("line\nbreak",), "graph.kind") == "line\nbreak"
