"""The engine's own Engine runs with no application code."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

import pytest

from llm_wiki_engine import Engine, integrations
from llm_wiki_engine.host import NoProcessHost
from llm_wiki_engine.pack_interfaces import (
    DomainPack,
    ExtensionSourceClassifier,
    active_pack,
)

ROOT = Path(__file__).resolve().parents[1]
NOTES = DomainPack("example/notes", ExtensionSourceClassifier({"notes": (".md",)}))


def test_importing_the_engine_loads_no_application_code():
    probe = (
        "import sys; from llm_wiki_engine import Engine; "
        "from llm_wiki_engine.pack_interfaces import DomainPack, ExtensionSourceClassifier; "
        "from llm_wiki_engine.host import NoProcessHost; "
        "engine = Engine(host=NoProcessHost(), pack=DomainPack('x/y', ExtensionSourceClassifier({'n': ('.md',)}))); "
        "engine.capabilities(); "
        "print(sorted(m for m in sys.modules if m.split('.')[0] == 'llm_wiki_cli'))"
    )
    result = subprocess.run([sys.executable, "-I", "-c", probe], capture_output=True, text=True, check=True)
    assert result.stdout.strip() == "[]"


def test_capabilities_follow_the_published_format():
    import jsonschema

    schema = json.loads(
        (ROOT / "src/llm_wiki_cli/schemas/llm-wiki-engine-capabilities-v1.schema.json").read_text(encoding="utf-8")
    )
    document = Engine(host=NoProcessHost(), pack=NOTES).capabilities()
    jsonschema.validate(document, schema)
    assert document["helper_preparation"] == "never"
    assert document["publication_targets"] == {"kinds": []}
    assert document["pack"]["page_namer"] == "llm_wiki_engine.pack_interfaces.StemPageNamer"


def test_an_operation_applies_the_pack_and_integrations():
    isolated = integrations.IntegrationSet(inherit=False)
    engine = Engine(host=NoProcessHost(), pack=NOTES, integrations=isolated)
    assert active_pack() is None
    with engine.operation() as operation:
        assert active_pack() is NOTES and operation.pack is NOTES
        with pytest.raises(integrations.IntegrationUnavailable):
            integrations.provider("source_snapshots")
    assert active_pack() is None


def test_the_engine_checks_what_it_is_given():
    with pytest.raises(TypeError, match="pack"):
        Engine(pack="notes")  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="host"):
        Engine(pack=NOTES, host="host")  # type: ignore[arg-type]
