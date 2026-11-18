"""Knowledge index validation runs through one context-scoped registry."""

from __future__ import annotations

import json

import pytest

from llm_wiki_cli.engine import DEFAULT_VALIDATORS, Engine, ModelValidator, NoProcessHost, ValidatorRegistry
from llm_wiki_engine import knowledge_index as index
from llm_wiki_engine import knowledge_model as model
from llm_wiki_engine.knowledge_validators import current_validators, using_validators
from tests.knowledge_fixtures import one_module_two_entities_fixture
from tests.test_knowledge_artifacts import _plan
from tests.test_knowledge_validation_receipt import _consume


def _payload(root):
    plan = _plan(root, one_module_two_entities_fixture())
    return plan, json.loads(plan.knowledge_index.content)


def _refuse_all(knowledge) -> None:
    raise model.KnowledgeModelError("extensions.team", "every concept needs an owner")


def test_the_default_registry_runs_the_reserved_extension_checks_in_order() -> None:
    assert DEFAULT_VALIDATORS.names == (
        "implementation-evidence", "maintenance-projection", "governance-projection",
    )
    assert current_validators() is DEFAULT_VALIDATORS
    modules = DEFAULT_VALIDATORS.modules()
    assert len(modules) == len(set(modules))
    assert "llm_wiki_engine.knowledge_model" in modules
    assert "llm_wiki_engine.knowledge_validators" in modules
    # The host's implementation evidence still defines part of what is accepted.
    assert "llm_wiki_cli.services.implementation_evidence" in modules


def test_an_added_validator_applies_only_inside_its_scope(tmp_path) -> None:
    _, payload = _payload(tmp_path)
    strict = DEFAULT_VALIDATORS.with_validator(ModelValidator("team-ownership", _refuse_all))

    with using_validators(strict), pytest.raises(model.KnowledgeModelError, match="needs an owner") as refused:
        model.parse_knowledge_index(payload)

    assert refused.value.field == "extensions.team"
    assert model.parse_knowledge_index(payload).concepts


def test_plain_errors_from_a_validator_are_reported_as_model_errors(tmp_path) -> None:
    _, payload = _payload(tmp_path)

    def broken(knowledge) -> None:
        raise KeyError("owner")

    with using_validators(DEFAULT_VALIDATORS.with_validator(ModelValidator("team", broken))):
        with pytest.raises(model.KnowledgeModelError, match="team: 'owner'"):
            model.parse_knowledge_index(payload)


def test_identity_covers_added_validators_and_their_modules() -> None:
    accept = ModelValidator("accept", lambda knowledge: None)
    with_module = ModelValidator("accept", lambda knowledge: None, ("json",))

    base = DEFAULT_VALIDATORS.identity()
    assert DEFAULT_VALIDATORS.with_validator(accept).identity() != base
    assert DEFAULT_VALIDATORS.with_validator(with_module).modules()[-1] == "json"
    assert DEFAULT_VALIDATORS.identity() == base


def test_a_receipt_is_not_trusted_under_another_registry(tmp_path) -> None:
    plan, payload = _payload(tmp_path)
    knowledge = model.parse_knowledge_index(payload)
    extended = DEFAULT_VALIDATORS.with_validator(ModelValidator("accept", lambda knowledge: None))

    with index._knowledge_validation_operation(tmp_path):
        receipt = index._validated_index_receipt(knowledge, tmp_path)
        with using_validators(extended), pytest.raises(TypeError, match="validators"):
            _consume(plan, receipt, tmp_path)
        assert _consume(plan, receipt, tmp_path).knowledge == knowledge


def test_engines_validate_with_their_own_registry(tmp_path) -> None:
    _, payload = _payload(tmp_path)
    strict = Engine(host=NoProcessHost(), validators=DEFAULT_VALIDATORS.with_validator(
        ModelValidator("team-ownership", _refuse_all)))

    with pytest.raises(model.KnowledgeModelError, match="needs an owner"):
        strict.call(model.parse_knowledge_index, payload)
    assert Engine(host=NoProcessHost()).call(model.parse_knowledge_index, payload).concepts
    assert strict.capabilities()["validators"] == [*DEFAULT_VALIDATORS.names, "team-ownership"]


def test_registry_values_are_checked() -> None:
    with pytest.raises(ValueError, match="unique"):
        DEFAULT_VALIDATORS.with_validator(ModelValidator("governance-projection", _refuse_all))
    with pytest.raises(TypeError, match="callable"):
        ModelValidator("team", "not callable")  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="non-empty"):
        ModelValidator("", _refuse_all)
    with pytest.raises(TypeError, match="ModelValidator"):
        ValidatorRegistry(validators=("team",), core_modules=())  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="ValidatorRegistry"):
        Engine(validators=object())  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="ValidatorRegistry"), using_validators(object()):  # type: ignore[arg-type]
        pass
