"""The checks every parsed knowledge index must pass, as one registry.

:func:`~llm_wiki_engine.knowledge_model.parse_knowledge_index` first
parses the core record shapes, then runs each :class:`ModelValidator` of the
active :class:`ValidatorRegistry` in order. The built-in registry checks
implementation evidence, the maintenance projection and the governance
projection, in that order: governance relies on the other reserved
extensions being valid.

The registry also names the modules whose functions and policy values define
acceptance. Its :meth:`ValidatorRegistry.identity` snapshots them, so a
validation receipt or cached validated model stops being trusted as soon as a
check, a module it depends on, or the registry itself changes.

A host extends validation by adding a validator and running work inside
:func:`using_validators`, or by passing the registry to an engine. The choice
is scoped to the current context, so engines with different registries can
run side by side.
"""

from __future__ import annotations

from llm_wiki_engine.integrations import attributes, provider

import importlib
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass, replace
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .knowledge_model import KnowledgeIndex

_PACKAGE = __name__.rpartition(".")[0]


@dataclass(frozen=True)
class ModelValidator:
    """One acceptance check run on every parsed knowledge index.

    ``check`` receives the parsed model and raises
    :class:`~llm_wiki_engine.knowledge_model.KnowledgeModelError` to
    reject it; a ``ValueError``, ``TypeError`` or ``KeyError`` is reported as
    one too. ``modules`` are importable module names whose functions and
    upper-case policy values define the check; changing any of them
    invalidates earlier validation.
    """

    name: str
    check: Callable[[KnowledgeIndex], object]
    modules: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.name, str) or not self.name:
            raise ValueError("validator name must be a non-empty string")
        if not callable(self.check):
            raise TypeError("validator check must be callable")
        modules = tuple(self.modules)
        if not all(isinstance(module, str) and module for module in modules):
            raise TypeError("validator modules must be module names")
        object.__setattr__(self, "modules", modules)


@dataclass(frozen=True)
class ValidatorRegistry:
    """Ordered model validators plus the modules that define core parsing."""

    validators: tuple[ModelValidator, ...]
    core_modules: tuple[str, ...]

    def __post_init__(self) -> None:
        validators = tuple(self.validators)
        if not all(isinstance(item, ModelValidator) for item in validators):
            raise TypeError("validators must be ModelValidator values")
        names = [item.name for item in validators]
        if len(set(names)) != len(names):
            raise ValueError("validator names must be unique")
        object.__setattr__(self, "validators", validators)
        object.__setattr__(self, "core_modules", tuple(self.core_modules))

    @property
    def names(self) -> tuple[str, ...]:
        return tuple(item.name for item in self.validators)

    def with_validator(self, validator: ModelValidator) -> ValidatorRegistry:
        """A copy of this registry that also runs ``validator``, last."""
        return replace(self, validators=(*self.validators, validator))

    def modules(self) -> tuple[str, ...]:
        """Every module that defines acceptance, each once, in a stable order.

        ``integration:<capability>`` names the module the host provides for that
        capability (see :mod:`llm_wiki_engine.integrations`).
        """
        names = [*self.core_modules, *(name for item in self.validators for name in item.modules)]
        return tuple(dict.fromkeys(_module_name(name) for name in names))

    def run(self, model: KnowledgeIndex) -> None:
        """Run every validator on ``model``; the first rejection propagates."""
        from .knowledge_model import KnowledgeModelError

        for validator in self.validators:
            try:
                validator.check(model)
            except KnowledgeModelError:
                raise
            except (ValueError, TypeError, KeyError) as exc:
                raise KnowledgeModelError("extensions", f"{validator.name}: {exc}") from exc

    def identity(self) -> tuple:
        """A value that changes whenever what this registry accepts may change."""
        from .knowledge_index import _validation_callable_identity, _validation_module_identity

        return (
            tuple(_validation_module_identity(importlib.import_module(name)) for name in self.modules()),
            tuple((item.name, _validation_callable_identity(item.check)) for item in self.validators),
        )


def _check_implementation_evidence(model: KnowledgeIndex) -> None:
    (validate_implementation_collection,) = attributes("implementation_evidence", "validate_implementation_collection")
    from .knowledge_model import KnowledgeModelError

    try:
        validate_implementation_collection(model.concepts, producer=model.bundle.producer)
    except (ValueError, TypeError, KeyError) as exc:
        raise KnowledgeModelError("concepts.extensions", str(exc)) from exc


def _check_maintenance_projection(model: KnowledgeIndex) -> None:
    from .knowledge_model import KnowledgeModelError
    from .maintenance_projection import validate_maintenance_projection

    try:
        validate_maintenance_projection(model)
    except (ValueError, TypeError, KeyError) as exc:
        raise KnowledgeModelError("maintenance", str(exc)) from exc


def _check_governance_projection(model: KnowledgeIndex) -> None:
    # Governance is an independently versioned projection whose authority is
    # the separate ledger. Its lifecycle/UID/alias/event parity is checked
    # only after the enclosing model and the other reserved extensions exist.
    from .knowledge_governance import validate_governance_projection
    from .knowledge_model import KnowledgeModelError

    try:
        validate_governance_projection(model)
    except ValueError as exc:
        field = getattr(exc, "field", "extensions")
        message = getattr(exc, "message", str(exc))
        code = getattr(exc, "code", None)
        raise KnowledgeModelError(
            str(field), str(message), code=str(code) if isinstance(code, str) else None,
        ) from exc


def _module(name: str) -> str:
    return f"{_PACKAGE}.{name}"


_INTEGRATION = "integration:"


def _module_name(name: str) -> str:
    if name.startswith(_INTEGRATION):
        return provider(name.removeprefix(_INTEGRATION)).__name__
    return name


#: The validation every knowledge index gets unless a host chooses otherwise.
DEFAULT_VALIDATORS = ValidatorRegistry(
    validators=(
        ModelValidator("implementation-evidence", _check_implementation_evidence,
                       (_INTEGRATION + "implementation_evidence", _INTEGRATION + "implementation_analysis")),
        ModelValidator("maintenance-projection", _check_maintenance_projection,
                       (_module("maintenance_projection"), _module("maintenance_shapes"),
                        _module("maintenance_state"))),
        ModelValidator("governance-projection", _check_governance_projection,
                       (_module("knowledge_governance"),)),
    ),
    # Parsers dispatch through module globals and reserved-extension
    # validators; a stamp of only their entry points would miss changed
    # lower-level acceptance rules.
    core_modules=tuple(_module(name) for name in (
        "analysis_compatibility", "concept_identity", "contracts", "immutable",
        "knowledge_evidence", "knowledge_graph", "knowledge_index", "knowledge_kinds", "knowledge_links",
        "knowledge_model", "knowledge_reuse_format", "knowledge_validators", "markdown_sections",
        "section_ownership", "source_retirement", "historical_sources", "validation", "wiki_media", "wiki_surface",
    )),
)

_ACTIVE_VALIDATORS: ContextVar[ValidatorRegistry | None] = ContextVar("llm_wiki_validators", default=None)


def current_validators() -> ValidatorRegistry:
    """The registry chosen for this context, or :data:`DEFAULT_VALIDATORS`."""
    return _ACTIVE_VALIDATORS.get() or DEFAULT_VALIDATORS


@contextmanager
def using_validators(registry: ValidatorRegistry) -> Iterator[ValidatorRegistry]:
    """Validate knowledge indexes inside the block with ``registry``."""
    if not isinstance(registry, ValidatorRegistry):
        raise TypeError("registry must be a ValidatorRegistry")
    token = _ACTIVE_VALIDATORS.set(registry)
    try:
        yield registry
    finally:
        _ACTIVE_VALIDATORS.reset(token)


__all__ = [
    "DEFAULT_VALIDATORS",
    "ModelValidator",
    "ValidatorRegistry",
    "current_validators",
    "using_validators",
]
