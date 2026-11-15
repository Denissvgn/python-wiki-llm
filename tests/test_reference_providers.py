"""Reference providers contributed by domain packs to publication review."""

from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any

import pytest

from llm_wiki_cli.engine import CODE_DOCS_PACK, Engine, NoProcessHost
from llm_wiki_cli.services import publication_candidate as candidate
from llm_wiki_cli.services import publication_impact as impact
from llm_wiki_cli.services.domain_pack import using_pack
from llm_wiki_cli.services.knowledge_evidence import hash_json
from llm_wiki_cli.services.publication_config import (
    PublicationConfigError,
    validate_publication_config,
)
from llm_wiki_cli.services.publication_contracts import validate_publication_basis
from llm_wiki_cli.services.reference_providers import (
    BUILTIN_REFERENCE_PROVIDERS,
    BehaviorFactsProvider,
    ReferenceContractError,
    ReferenceProvider,
    ReferenceSelectorError,
    check_reference_providers,
    reference_provider,
    reference_providers_identity,
)
from tests.test_publication_impact import consumer as consumer

KIND = "example/operations"


class OperationsProvider(ReferenceProvider):
    """An API description file; dependencies may select one operation."""

    kind = KIND
    reads_file = True
    label = "operations"

    def normalize_selector(self, dependency: Mapping[str, Any], field: str) -> dict[str, Any]:
        unknown = sorted(set(dependency) - {"reference", "operation"})
        if unknown:
            raise ReferenceSelectorError(field, "unknown " + ", ".join(unknown))
        if "operation" in dependency and not isinstance(dependency["operation"], str):
            raise ReferenceSelectorError(f"{field}.operation", "must be an operation id")
        return dict(dependency)

    def parse(self, raw: bytes) -> Any:
        contract = json.loads(raw)
        self.validate_contract(contract)
        return contract

    def validate_contract(self, contract: Any) -> None:
        if not isinstance(contract, dict) or not isinstance(contract.get("operations"), dict):
            raise ReferenceContractError("an operations contract needs an operations object")

    def select(self, contract: Any, dependency: Mapping[str, Any]) -> str | None:
        if "operation" not in dependency:
            return hash_json(contract)
        operation = contract["operations"].get(dependency["operation"])
        return None if operation is None else hash_json(operation)


class ReleaseNotesProvider(ReferenceProvider):
    """Observed from the installation; no selectors."""

    kind = "example/release-notes"
    label = "release notes"
    notes = {"highlights": ["first"]}

    def normalize_selector(self, dependency: Mapping[str, Any], field: str) -> dict[str, Any]:
        if set(dependency) != {"reference"}:
            raise ReferenceSelectorError(field, "release notes take no selector")
        return dict(dependency)

    def capture(self) -> Any:
        return json.loads(json.dumps(self.notes))

    def validate_contract(self, contract: Any) -> None:
        if not isinstance(contract, dict):
            raise ReferenceContractError("release notes are an object")

    def select(self, contract: Any, dependency: Mapping[str, Any]) -> str | None:
        return hash_json(contract)


API_PACK = CODE_DOCS_PACK.with_reference_provider(OperationsProvider()).with_reference_provider(
    ReleaseNotesProvider()
)


def operations(**changes: str) -> dict[str, Any]:
    ops = {"listAccounts": "GET /accounts", "deleteAccount": "DELETE /accounts/{id}"}
    ops.update(changes)
    return {"operations": {name: {"route": route} for name, route in ops.items()}}


def configure(root, dependency: dict[str, Any] | None = None) -> dict[str, Any]:
    target = root / ".llm-wiki/publication.json"
    policy = json.loads(target.read_text())
    policy["reference_providers"] = {
        "api": {"kind": KIND, "path": "api-operations.json"},
        "notes": {"kind": "example/release-notes"},
    }
    policy["topics"][0]["depends_on"] = [
        dependency or {"reference": "api", "operation": "listAccounts"}
    ]
    target.write_text(json.dumps(policy))
    return policy


def capture(root, baseline=None):
    return impact.capture_publication_basis(root, target_dir="public", baseline=baseline)


def test_code_docs_pack_contributes_the_builtin_providers():
    assert CODE_DOCS_PACK.reference_providers == BUILTIN_REFERENCE_PROVIDERS
    assert [provider.kind for provider in BUILTIN_REFERENCE_PROVIDERS] == [
        "llm-wiki-cli",
        "llm-wiki-behavior",
        "contract-file",
    ]
    assert reference_providers_identity(BUILTIN_REFERENCE_PROVIDERS) is None
    assert reference_providers_identity(API_PACK.reference_providers) is not None
    assert CODE_DOCS_PACK.describe()["reference_providers"] == [
        "llm-wiki-cli", "llm-wiki-behavior", "contract-file",
    ]
    assert reference_provider("contract-file").reads_file
    with pytest.raises(KeyError, match="provides no"):
        reference_provider(KIND)
    with using_pack(API_PACK):
        assert isinstance(reference_provider(KIND), OperationsProvider)


def test_provider_values_are_checked():
    with pytest.raises(TypeError):
        check_reference_providers([object()])
    with pytest.raises(ValueError, match="non-empty kind"):
        check_reference_providers([ReferenceProvider()])
    with pytest.raises(ValueError, match="unique"):
        check_reference_providers([OperationsProvider(), OperationsProvider()])
    replaced = API_PACK.with_reference_provider(OperationsProvider())
    assert [p.kind for p in replaced.reference_providers][-1] == KIND
    assert len(replaced.reference_providers) == len(API_PACK.reference_providers)
    narrowed = CODE_DOCS_PACK.with_reference_provider(BehaviorFactsProvider())
    assert reference_providers_identity(narrowed.reference_providers) is not None


def test_policy_kinds_and_selectors_follow_the_active_pack(consumer):
    policy = configure(consumer)
    with pytest.raises(PublicationConfigError, match="reference_providers.api.kind"):
        validate_publication_config(policy, consumer_root=None)
    with using_pack(API_PACK):
        normalized = validate_publication_config(policy, consumer_root=None)
        assert normalized["reference_providers"]["api"] == {
            "kind": KIND,
            "path": "api-operations.json",
        }
        bad = json.loads(json.dumps(policy))
        bad["topics"][0]["depends_on"] = [{"reference": "api", "command": ["list"]}]
        with pytest.raises(PublicationConfigError) as caught:
            validate_publication_config(bad, consumer_root=None)
        assert caught.value.field == "topics[0].depends_on[0]"
        assert caught.value.message == "unknown command"
        bad["topics"][0]["depends_on"] = [{"reference": "api", "operation": 3}]
        with pytest.raises(PublicationConfigError) as caught:
            validate_publication_config(bad, consumer_root=None)
        assert caught.value.field == "topics[0].depends_on[0].operation"


def test_builtin_selector_errors_keep_their_fields(consumer):
    policy = configure(consumer)
    policy["reference_providers"] = {"installed": {"kind": "llm-wiki-behavior"}}
    policy["topics"][0]["depends_on"] = [{"reference": "installed", "fact": "unknown"}]
    with pytest.raises(PublicationConfigError) as caught:
        validate_publication_config(policy, consumer_root=None)
    assert caught.value.field == "topics[0].depends_on[0].fact"
    assert caught.value.message.startswith("must be one of ")
    policy["reference_providers"] = {"installed": {"kind": "llm-wiki-cli"}}
    policy["topics"][0]["depends_on"] = [{"reference": "installed", "command": ["bad token"]}]
    with pytest.raises(PublicationConfigError) as caught:
        validate_publication_config(policy, consumer_root=None)
    assert caught.value.field == "topics[0].depends_on[0].command[0]"
    assert caught.value.message == "must be a literal portable command token"


def test_custom_provider_scopes_publication_review(consumer):
    configure(consumer)
    path = consumer / "api-operations.json"
    path.write_text(json.dumps(operations()))
    with using_pack(API_PACK):
        before = capture(consumer)
        validate_publication_basis(before)
        reference = next(
            item for item in before["references"].values() if item["provider"] == "api"
        )
        assert reference["contract"] == operations()

        # An unrelated operation changes the contract but not the reviewed scope.
        path.write_text(json.dumps(operations(deleteAccount="DELETE /accounts")))
        report = impact.compare_publication_impact(capture(consumer, before), before)
        assert report["changed"] and not report["review_required"]

        # The selected operation reopens review.
        path.write_text(json.dumps(operations(listAccounts="GET /v2/accounts")))
        report = impact.compare_publication_impact(capture(consumer, before), before)
        assert report["review_required"]
        assert report["findings"][0]["status"] == "needs-review"

        # A missing file is known-missing input and never clears review.
        path.unlink()
        report = impact.compare_publication_impact(capture(consumer))
        assert not report["complete"] and not report["ready"]
    # Evidence naming the custom kind is refused without its provider.
    with pytest.raises(ValueError):
        validate_publication_basis(before)


def test_stored_contracts_are_checked_by_their_provider(consumer):
    configure(consumer)
    (consumer / "api-operations.json").write_text(json.dumps(operations()))
    with using_pack(API_PACK):
        basis = capture(consumer)
        tampered = json.loads(json.dumps(basis))
        for item in tampered["references"].values():
            if item["provider"] == "api":
                item["contract"] = {"paths": {}}
        tampered["basis_id"] = hash_json(
            {key: value for key, value in tampered.items() if key != "basis_id"}
        )
        with pytest.raises(ValueError, match="operations contract needs"):
            validate_publication_basis(tampered)


def test_installed_provider_is_rechecked_after_capture(consumer, monkeypatch):
    configure(consumer, {"reference": "notes"})
    (consumer / "api-operations.json").write_text(json.dumps(operations()))
    generations = iter([{"highlights": ["first"]}, {"highlights": ["second"]}])
    monkeypatch.setattr(ReleaseNotesProvider, "capture", lambda self: next(generations))
    with using_pack(API_PACK), pytest.raises(
        ValueError, match="Installed release notes declarations changed"
    ):
        capture(consumer)


def test_custom_providers_change_the_candidate_provider_fingerprint():
    default = candidate._provider()["fingerprint"]
    with using_pack(API_PACK):
        assert candidate._provider()["fingerprint"] != default
    pack = Engine(host=NoProcessHost(), pack=API_PACK).capabilities()["pack"]
    assert isinstance(pack, dict)
    assert pack["reference_providers"] == [
        "llm-wiki-cli", "llm-wiki-behavior", "contract-file", KIND, "example/release-notes",
    ]
