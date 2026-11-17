"""Reference providers: declared contracts that public documentation depends on.

A publication policy declares ``reference_providers`` by ``kind`` and lets
topics depend on a whole reference or on a selected part of it. A
:class:`ReferenceProvider` owns one kind:

* :attr:`~ReferenceProvider.reads_file` says where its contract comes from.
  A file provider's configuration names a repository JSON file
  (``{"kind", "path"}``) that :meth:`~ReferenceProvider.parse` reads; a
  missing file is recorded as known-missing input. Any other provider's
  configuration is ``{"kind"}`` alone and :meth:`~ReferenceProvider.capture`
  observes the contract from the running installation;
* :meth:`~ReferenceProvider.normalize_selector` validates a topic dependency
  on the provider and returns its normalized form;
* :meth:`~ReferenceProvider.validate_contract` checks a captured contract
  stored in publication evidence;
* :meth:`~ReferenceProvider.select` commits the selected part of a contract
  as a digest, or returns ``None`` when the selection is absent.

Domain packs contribute providers (``DomainPack.reference_providers``); the
code-documentation pack contributes :data:`BUILTIN_REFERENCE_PROVIDERS`: the
installed ``llm-wiki-cli`` command contract, the installed
``llm-wiki-behavior`` facts and ``contract-file`` command contracts. A policy
may only declare kinds the active pack provides. Providers are inert: they
read declarations and never execute the referenced program.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from typing import Any

from llm_wiki_engine.knowledge_evidence import hash_json

_TOKEN = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}\Z")
_MAX_COMMAND_TOKENS = 32


class ReferenceSelectorError(ValueError):
    """A topic dependency selects a reference in a way its provider refuses."""

    def __init__(self, field: str, message: str):
        self.field = field
        self.message = message
        super().__init__(f"{field}: {message}")


class ReferenceContractError(ValueError):
    """A stored contract could not have come from its provider."""


def _selector_fields(dependency: Mapping[str, Any], field: str, optional: str) -> None:
    if not isinstance(dependency, Mapping) or any(type(key) is not str for key in dependency):
        raise ReferenceSelectorError(field, "must be an object with string keys")
    unknown = sorted(set(dependency) - {"reference", optional})
    missing = [] if "reference" in dependency else ["reference"]
    details = []
    if missing:
        details.append("missing " + ", ".join(missing))
    if unknown:
        details.append("unknown " + ", ".join(unknown))
    if details:
        raise ReferenceSelectorError(field, "; ".join(details))


class ReferenceProvider:
    """The rules of one reference provider kind.

    Subclasses set :attr:`kind`, choose :attr:`reads_file` and implement the
    hooks. Hooks must be deterministic: publication evidence is rechecked by
    running them again.
    """

    kind: str = ""
    #: Whether the configuration names a repository JSON file to parse.
    reads_file: bool = False
    #: How messages name this provider's installed declarations.
    label: str = "reference"

    def normalize_selector(self, dependency: Mapping[str, Any], field: str) -> dict[str, Any]:
        """The normalized form of ``dependency`` (which names the provider in ``reference``).

        Raise :class:`ReferenceSelectorError` for a selector this provider
        does not accept.
        """
        raise NotImplementedError

    def capture(self) -> Any:
        """The contract observed from the running installation (``reads_file`` false)."""
        raise NotImplementedError

    def parse(self, raw: bytes) -> Any:
        """The contract read from the configured file (``reads_file`` true)."""
        raise NotImplementedError

    def validate_contract(self, contract: Any) -> None:
        """Refuse a stored contract this provider could not have captured.

        Raise :class:`ReferenceContractError` (or ``ValueError``).
        """
        raise NotImplementedError

    def select(self, contract: Any, dependency: Mapping[str, Any]) -> str | None:
        """A digest of the part of ``contract`` that ``dependency`` selects."""
        raise NotImplementedError

    def identity(self) -> Any:
        """A JSON-ready value that changes whenever this provider's results may change."""
        return {"kind": self.kind, "class": f"{type(self).__module__}.{type(self).__qualname__}"}


class _CommandSelector(ReferenceProvider):
    """Dependencies select a command subtree: ``{"reference", "command": [...]}``."""

    def normalize_selector(self, dependency: Mapping[str, Any], field: str) -> dict[str, Any]:
        _selector_fields(dependency, field, "command")
        tokens = dependency.get("command", [])
        if type(tokens) is not list or len(tokens) > _MAX_COMMAND_TOKENS:
            raise ReferenceSelectorError(
                f"{field}.command",
                f"must be an array containing zero to {_MAX_COMMAND_TOKENS} entries",
            )
        for index, token in enumerate(tokens):
            token_field = f"{field}.command[{index}]"
            if type(token) is not str or not token or token != token.strip():
                raise ReferenceSelectorError(
                    token_field, "must be non-empty text without surrounding whitespace"
                )
            if not _TOKEN.fullmatch(token):
                raise ReferenceSelectorError(
                    token_field, "must be a literal portable command token"
                )
        return {"reference": dependency["reference"], "command": list(tokens)}

    def validate_contract(self, contract: Any) -> None:
        from .cli_reference import validate_cli_contract

        validate_cli_contract(contract)

    def select(self, contract: Any, dependency: Mapping[str, Any]) -> str | None:
        return select_command(contract, dependency.get("command", []))


class CliContractProvider(_CommandSelector):
    """The installed ``llm-wiki`` command-line contract."""

    kind = "llm-wiki-cli"
    label = "CLI"

    def capture(self) -> Any:
        from .cli_reference import get_cli_contract

        return get_cli_contract()

    def validate_contract(self, contract: Any) -> None:
        super().validate_contract(contract)
        if contract["program"] != "llm-wiki" or contract["package"]["name"] != "agent-wiki-cli":
            raise ReferenceContractError("built-in provider identity must be agent-wiki-cli/llm-wiki")


class ContractFileProvider(_CommandSelector):
    """A command-line contract file committed to the repository."""

    kind = "contract-file"
    reads_file = True
    label = "contract file"

    def parse(self, raw: bytes) -> Any:
        from .cli_reference import parse_cli_contract

        return parse_cli_contract(raw)


class BehaviorFactsProvider(ReferenceProvider):
    """The installed behavior facts; dependencies may select one fact group."""

    kind = "llm-wiki-behavior"
    label = "behavior"

    def normalize_selector(self, dependency: Mapping[str, Any], field: str) -> dict[str, Any]:
        from .behavior_reference import BEHAVIOR_FACT_GROUPS

        _selector_fields(dependency, field, "fact")
        if "fact" not in dependency:
            return {"reference": dependency["reference"]}
        fact = dependency["fact"]
        if type(fact) is not str or fact not in BEHAVIOR_FACT_GROUPS:
            raise ReferenceSelectorError(
                f"{field}.fact", "must be one of " + ", ".join(sorted(BEHAVIOR_FACT_GROUPS))
            )
        return {"reference": dependency["reference"], "fact": fact}

    def capture(self) -> Any:
        from .behavior_reference import get_behavior_facts

        return get_behavior_facts()

    def validate_contract(self, contract: Any) -> None:
        from .behavior_reference import validate_behavior_facts

        validate_behavior_facts(contract)

    def select(self, contract: Any, dependency: Mapping[str, Any]) -> str | None:
        if "fact" in dependency:
            return select_behavior_fact(contract, dependency["fact"])
        return contract["contract_id"]


def select_behavior_fact(contract, fact):
    """Commit one named behavior fact group."""
    return hash_json(
        {
            "schema_version": contract["schema_version"],
            "package": contract["facts"]["package"]["name"],
            "fact": fact,
            "value": contract["facts"][fact],
        }
    )


def select_command(contract, path):
    """Commit a complete command contract or one command subtree."""
    if not path:
        return contract["contract_id"]
    node = contract["root"]
    ancestors = []
    for token in path:
        ancestors.append(_ancestor_context(node))
        node = next(
            (
                child
                for child in node["commands"]
                if token == child["name"] or token in child["aliases"]
            ),
            None,
        )
        if node is None:
            return None
    # Bind the declared subtree. Whole-contract dependencies additionally
    # bind release-version and unrelated-command metadata.
    return hash_json(
        {
            "schema_version": contract["schema_version"],
            "program": contract["program"],
            "package": {
                key: value
                for key, value in contract["package"].items()
                if key != "version"
            },
            "command": node,
            "ancestors": ancestors,
        }
    )


def _ancestor_context(command):
    """Global parser declarations also govern a selected descendant command."""
    arguments = [
        arg
        for arg in command["arguments"]
        if arg["action"] not in {"subparsers", "help", "version"}
    ]
    identities = {arg["id"]: f"argument:{index}" for index, arg in enumerate(arguments)}
    positional_syntax = []
    for argument in command["arguments"]:
        if argument["action"] == "subparsers":
            # A subcommand boundary changes how ancestor positionals consume
            # tokens. Keep its namespace and grammar, excluding sibling choices
            # and presentation metadata that do not govern this descendant.
            positional_syntax.append(
                {
                    "subcommand": {
                        key: argument[key]
                        for key in ("dest", "nargs", "required", "default")
                    }
                }
            )
        elif argument["positional"] and argument["id"] in identities:
            positional_syntax.append({"argument": identities[argument["id"]]})

    def project_groups(key, prefix):
        groups, identities_for_groups = [], {}
        for group in command[key]:
            members = [
                identities[member]
                for member in group["members"]
                if member in identities
            ]
            if members:
                identity = f"{prefix}:{len(groups)}"
                identities_for_groups[group["id"]] = identity
                groups.append({**group, "id": identity, "members": members})
        return groups, identities_for_groups

    groups, group_ids = project_groups("groups", "group")
    exclusive, exclusive_ids = project_groups("exclusive_groups", "exclusive")
    # IDs are local coordinates in the full declaration. Rebase retained IDs
    # so an excluded help/version action cannot shift a scoped review basis.
    arguments = [
        {
            **arg,
            "id": identities[arg["id"]],
            "group": None if arg["group"] is None else group_ids[arg["group"]],
            "exclusive_groups": [
                exclusive_ids[identity] for identity in arg["exclusive_groups"]
            ],
        }
        for arg in arguments
    ]
    return {
        "path": command["path"],
        "aliases": command["aliases"],
        "deprecated": command["deprecated"],
        "notes": command["notes"],
        "defaults": command["defaults"],
        "settings": command["settings"],
        "arguments": arguments,
        "positional_syntax": positional_syntax,
        "groups": groups,
        "exclusive_groups": exclusive,
    }


#: The providers of the code-documentation pack, in declaration order.
BUILTIN_REFERENCE_PROVIDERS: tuple[ReferenceProvider, ...] = (
    CliContractProvider(),
    BehaviorFactsProvider(),
    ContractFileProvider(),
)
_BUILTIN_TYPES = tuple(type(provider) for provider in BUILTIN_REFERENCE_PROVIDERS)


def check_reference_providers(providers: object) -> tuple[ReferenceProvider, ...]:
    """Return ``providers`` as a tuple of distinct-kind providers or raise."""
    values = tuple(providers)  # type: ignore[arg-type]
    kinds = set()
    for provider in values:
        if not isinstance(provider, ReferenceProvider):
            raise TypeError("reference_providers must be ReferenceProvider values")
        if not isinstance(provider.kind, str) or not provider.kind:
            raise ValueError("a reference provider needs a non-empty kind")
        if provider.kind in kinds:
            raise ValueError(f"reference provider kinds must be unique: {provider.kind!r}")
        kinds.add(provider.kind)
    return values


def reference_providers_identity(providers: tuple[ReferenceProvider, ...]) -> Any:
    """``None`` for the built-in providers, else a value naming every provider."""
    if tuple(type(provider) for provider in providers) == _BUILTIN_TYPES:
        return None
    return [provider.identity() for provider in providers]


def current_reference_providers() -> dict[str, ReferenceProvider]:
    """The active pack's providers keyed by kind."""
    from .domain_pack import current_pack

    return {provider.kind: provider for provider in current_pack().reference_providers}


def reference_provider(kind: str) -> ReferenceProvider:
    """The active pack's provider for ``kind``; ``KeyError`` when it has none."""
    providers = current_reference_providers()
    if kind not in providers:
        raise KeyError(f"the active domain pack provides no {kind!r} references")
    return providers[kind]


__all__ = [
    "BUILTIN_REFERENCE_PROVIDERS",
    "BehaviorFactsProvider",
    "CliContractProvider",
    "ContractFileProvider",
    "ReferenceContractError",
    "ReferenceProvider",
    "ReferenceSelectorError",
    "check_reference_providers",
    "current_reference_providers",
    "reference_provider",
    "reference_providers_identity",
]
