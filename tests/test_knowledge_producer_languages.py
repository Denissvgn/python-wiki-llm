"""Producer identity follows the selected extractor, not only its output label."""

import pytest

from llm_wiki_cli.config import EXTRACTOR_REGISTRY
from llm_wiki_cli.services.knowledge_envelope import (
    ProducerComponentInput,
    build_producer_record,
)
from llm_wiki_cli.services.knowledge_orchestration import _producer_evidence


def _produce(inventory, registry=None, plugins=()):
    refs, _, extractors, producer_plugins = _producer_evidence(
        inventory,
        inventory_complete=True,
        extractor_registry=EXTRACTOR_REGISTRY if registry is None else registry,
        plugin_extractor_components=plugins,
    )
    return refs, build_producer_record(
        tool=ProducerComponentInput("agent-wiki-cli", "2.0.1", configuration={}),
        extractors=extractors,
        plugins=producer_plugins,
    )


@pytest.mark.parametrize(
    "suffix,language",
    [
        ("js", "javascript"),
        ("jsx", "javascript"),
        ("ts", "typescript"),
        ("tsx", "typescript"),
    ],
)
def test_typescript_family_output_has_known_configuration(suffix, language):
    inventory = {"module." + suffix: {"language": language}}
    refs, producer = _produce(inventory)
    assert refs["module." + suffix] == "llm-wiki/extractor/" + language
    assert producer.extractors[0].configuration_hash is not None
    assert "configuration-basis-unknown" not in producer.extractors[0].limitations
    assert _produce(inventory)[1] == producer


def test_missing_executor_remains_unknown():
    _, producer = _produce({"module.js": {"language": "javascript"}}, registry={})
    assert producer.extractors[0].configuration_hash is None
    assert "configuration-basis-unknown" in producer.extractors[0].limitations


def _plugin(language="typescript", component_id="family"):
    return {
        "type": "extractor",
        "language": language,
        "id": component_id,
        "entry_point": "observer:Extractor",
        "parallel_safe": True,
        "plugin_id": "observer",
        "plugin_version": "1.0.0",
    }


def test_family_plugin_owns_javascript_and_is_order_independent():
    inventory = {"a.js": {"language": "javascript"}, "b.ts": {"language": "typescript"}}
    refs, producer = _produce(
        inventory, {"typescript": "observer:Extractor"}, (_plugin(),)
    )
    assert set(refs.values()) == {"observer/family"}
    assert len(producer.extractors) == 1
    assert producer.extractors[0].configuration_hash is not None
    assert (
        _produce(
            dict(reversed(list(inventory.items()))),
            {"typescript": "observer:Extractor"},
            (_plugin(),),
        )[1]
        == producer
    )
    changed = _produce(
        inventory,
        {"typescript": "observer:Extractor"},
        ({**_plugin(), "plugin_version": "1.0.1"},),
    )[1]
    assert changed != producer


def test_explicit_javascript_plugin_precedes_family_plugin():
    refs, producer = _produce(
        {"a.js": {"language": "javascript"}, "b.ts": {"language": "typescript"}},
        {"typescript": "observer:Extractor", "javascript": "observer:JavaScript"},
        (
            _plugin(),
            {
                **_plugin("javascript", "javascript"),
                "entry_point": "observer:JavaScript",
            },
        ),
    )
    assert refs == {"a.js": "observer/javascript", "b.ts": "observer/family"}
    assert len(producer.extractors) == 2


def test_selected_executor_configuration_changes_the_hash():
    inventory = {"module.js": {"language": "javascript"}}
    baseline = _produce(inventory)[1]
    changed = _produce(inventory, {"typescript": "custom:Extractor"})[1]
    assert (
        baseline.extractors[0].configuration_hash
        != changed.extractors[0].configuration_hash
    )
