"""Provider-neutral model routing for documentation-agent invocations.

The deterministic package does not call a model provider.  This module gives a
host supervisor a small, auditable policy for choosing a configured model route
before it invokes a generic agent or creates a handoff.  Provider credentials,
transport configuration, prompts, and responses are deliberately outside the
contract.

Both invocation modes must start on a ``low-cost`` route.  A more expensive or
capable route is selected only by an explicit user override or a configured
escalation rule.  Model identifiers and aliases remain ordinary configuration
strings; the protocol never enumerates vendor model names or treats one
provider as the default.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, replace
from typing import Any, Mapping

from .contracts import (
    DOCUMENTATION_MODEL_ROUTING_SCHEMA_VERSION,
    DOCUMENTATION_MODEL_SELECTION_SCHEMA_VERSION,
)
from .validation import (
    require_exact_fields,
    require_mapping,
    require_mapping_tuple,
    require_nonempty_text,
    require_string_tuple,
    trimmed_text_or_none,
)

SUPPORTED_PROVIDER_FAMILIES = frozenset(
    {
        "openai-compatible",
        "anthropic",
        "google-gemini",
        "local-self-hosted",
        "other",
    }
)
SUPPORTED_MODEL_TIERS = frozenset({"low-cost", "balanced", "capability"})
SUPPORTED_INVOCATION_MODES = frozenset({"generic-agent", "handoff"})
SUPPORTED_SELECTION_BASES = frozenset(
    {"mode-default", "configured-escalation", "explicit-user-override"}
)

_MODE_ORDER = {"generic-agent": 0, "handoff": 1}
_TIER_ORDER = {"low-cost": 0, "balanced": 1, "capability": 2}
_SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{0,127}$")
_HEX_DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
_CONTROL_RE = re.compile(r"[\x00-\x1f\x7f]")
_PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/@+~-]{0,255}$")
_CREDENTIAL_VALUE_RE = re.compile(
    r"^(?:bearer\s+|sk-[a-z0-9]|xox[baprs]-|gh[pousr]_|AIza)",
    re.IGNORECASE,
)
_SENSITIVE_KEYS = frozenset(
    {
        "api_key",
        "apikey",
        "access_token",
        "auth_token",
        "authorization",
        "client_secret",
        "cookie",
        "cookies",
        "credential",
        "credentials",
        "headers",
        "password",
        "secret",
        "token",
    }
)


class DocumentationModelPolicyError(ValueError):
    """Raised when model-routing configuration is unsafe or ambiguous."""


@dataclass(frozen=True)
class DocumentationModelRoute:
    """One configured provider/model route.

    ``provider_id`` is a public configuration label such as ``anthropic-prod``
    or ``local-ollama``.  It is not an endpoint and must not contain a key.
    ``model_id`` is provider configuration, not a protocol enum.
    """

    route_id: str
    provider_family: str
    provider_id: str
    model_id: str
    tier: str
    modes: tuple[str, ...]
    aliases: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _validate_slug(self.route_id, "route_id")
        _validate_provider_family(self.provider_family)
        _validate_public_identifier(self.provider_id, "provider_id")
        _validate_public_identifier(self.model_id, "model_id")
        _validate_tier(self.tier)
        modes = _normalise_modes(self.modes, "route modes")
        aliases = tuple(
            sorted({_validate_slug(value, "route alias") for value in self.aliases})
        )
        if self.route_id in aliases:
            raise DocumentationModelPolicyError(
                f"Route {self.route_id!r} cannot repeat its route_id as an alias."
            )
        object.__setattr__(self, "modes", modes)
        object.__setattr__(self, "aliases", aliases)

    def to_dict(self) -> dict[str, Any]:
        """Return deterministic, credential-free route configuration."""
        return {
            "route_id": self.route_id,
            "provider_family": self.provider_family,
            "provider_id": self.provider_id,
            "model_id": self.model_id,
            "tier": self.tier,
            "modes": list(self.modes),
            "aliases": list(self.aliases),
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "DocumentationModelRoute":
        _validate_object(
            payload,
            {
                "route_id",
                "provider_family",
                "provider_id",
                "model_id",
                "tier",
                "modes",
                "aliases",
            },
            "model route",
        )
        return cls(
            route_id=_required_text(payload.get("route_id"), "route_id"),
            provider_family=_required_text(
                payload.get("provider_family"), "provider_family"
            ),
            provider_id=_required_text(payload.get("provider_id"), "provider_id"),
            model_id=_required_text(payload.get("model_id"), "model_id"),
            tier=_required_text(payload.get("tier"), "tier"),
            modes=_text_sequence(payload.get("modes"), "route modes"),
            aliases=_text_sequence(payload.get("aliases", ()), "route aliases"),
        )


@dataclass(frozen=True)
class DocumentationModelEscalationRule:
    """Configured signal-to-route promotion owned by the host supervisor."""

    rule_id: str
    signals: tuple[str, ...]
    target_route_id: str
    modes: tuple[str, ...]
    from_tiers: tuple[str, ...] = ("low-cost", "balanced")
    priority: int = 100

    def __post_init__(self) -> None:
        _validate_slug(self.rule_id, "rule_id")
        _validate_slug(self.target_route_id, "target_route_id")
        signals = tuple(
            sorted(
                {_validate_slug(value, "escalation signal") for value in self.signals}
            )
        )
        if not signals:
            raise DocumentationModelPolicyError(
                "An escalation rule requires at least one signal."
            )
        modes = _normalise_modes(self.modes, "escalation modes")
        from_tiers = tuple(
            sorted(
                {_validate_tier(value) for value in self.from_tiers},
                key=_TIER_ORDER.__getitem__,
            )
        )
        if not from_tiers:
            raise DocumentationModelPolicyError(
                "An escalation rule requires at least one source tier."
            )
        if isinstance(self.priority, bool) or not isinstance(self.priority, int):
            raise DocumentationModelPolicyError(
                "Escalation priority must be a non-negative integer."
            )
        if self.priority < 0:
            raise DocumentationModelPolicyError(
                "Escalation priority must be a non-negative integer."
            )
        object.__setattr__(self, "signals", signals)
        object.__setattr__(self, "modes", modes)
        object.__setattr__(self, "from_tiers", from_tiers)

    def to_dict(self) -> dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "signals": list(self.signals),
            "target_route_id": self.target_route_id,
            "modes": list(self.modes),
            "from_tiers": list(self.from_tiers),
            "priority": self.priority,
        }

    @classmethod
    def from_dict(
        cls, payload: Mapping[str, Any]
    ) -> "DocumentationModelEscalationRule":
        _validate_object(
            payload,
            {
                "rule_id",
                "signals",
                "target_route_id",
                "modes",
                "from_tiers",
                "priority",
            },
            "model escalation rule",
        )
        priority = payload.get("priority", 100)
        if isinstance(priority, bool) or not isinstance(priority, int):
            raise DocumentationModelPolicyError(
                "Escalation priority must be a non-negative integer."
            )
        return cls(
            rule_id=_required_text(payload.get("rule_id"), "rule_id"),
            signals=_text_sequence(payload.get("signals"), "escalation signals"),
            target_route_id=_required_text(
                payload.get("target_route_id"), "target_route_id"
            ),
            modes=_text_sequence(payload.get("modes"), "escalation modes"),
            from_tiers=_text_sequence(
                payload.get("from_tiers", ("low-cost", "balanced")),
                "escalation source tiers",
            ),
            priority=priority,
        )


@dataclass(frozen=True)
class DocumentationModelRoutingPolicy:
    """Complete low-cost-first routing configuration for wiki updates."""

    routes: tuple[DocumentationModelRoute, ...]
    mode_defaults: Mapping[str, str]
    escalation_rules: tuple[DocumentationModelEscalationRule, ...] = ()
    schema_version: str = DOCUMENTATION_MODEL_ROUTING_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.schema_version != DOCUMENTATION_MODEL_ROUTING_SCHEMA_VERSION:
            raise DocumentationModelPolicyError(
                "Unsupported documentation model-routing schema_version."
            )
        if not self.routes:
            raise DocumentationModelPolicyError(
                "Model-routing policy requires at least one route."
            )
        if any(not isinstance(route, DocumentationModelRoute) for route in self.routes):
            raise DocumentationModelPolicyError(
                "routes must contain DocumentationModelRoute values."
            )

        routes = tuple(sorted(self.routes, key=lambda route: route.route_id))
        route_ids: dict[str, DocumentationModelRoute] = {}
        references: dict[str, str] = {}
        for route in routes:
            if route.route_id in route_ids:
                raise DocumentationModelPolicyError(
                    f"Duplicate model route_id: {route.route_id!r}."
                )
            route_ids[route.route_id] = route
            for reference in (route.route_id, *route.aliases):
                previous = references.get(reference)
                if previous is not None:
                    raise DocumentationModelPolicyError(
                        f"Model route reference {reference!r} is shared by "
                        f"{previous!r} and {route.route_id!r}."
                    )
                references[reference] = route.route_id

        if not isinstance(self.mode_defaults, Mapping):
            raise DocumentationModelPolicyError("mode_defaults must be an object.")
        if any(not isinstance(mode, str) for mode in self.mode_defaults):
            raise DocumentationModelPolicyError(
                "mode_defaults keys must be invocation-mode strings."
            )
        unknown_modes = set(self.mode_defaults) - SUPPORTED_INVOCATION_MODES
        missing_modes = SUPPORTED_INVOCATION_MODES - set(self.mode_defaults)
        if unknown_modes or missing_modes:
            raise DocumentationModelPolicyError(
                "mode_defaults must define exactly generic-agent and handoff; "
                f"missing={sorted(missing_modes)!r}, "
                f"unknown={sorted(unknown_modes)!r}."
            )
        defaults: dict[str, str] = {}
        for mode in sorted(SUPPORTED_INVOCATION_MODES, key=_MODE_ORDER.__getitem__):
            reference = _required_text(self.mode_defaults.get(mode), f"{mode} default")
            route_id = references.get(reference)
            if route_id is None:
                raise DocumentationModelPolicyError(
                    f"Unknown {mode} default route or alias: {reference!r}."
                )
            route = route_ids[route_id]
            if mode not in route.modes:
                raise DocumentationModelPolicyError(
                    f"Default route {route_id!r} does not support mode {mode!r}."
                )
            if route.tier != "low-cost":
                raise DocumentationModelPolicyError(
                    f"Default route for {mode!r} must use the low-cost tier; "
                    "balanced/capability routes require escalation or an explicit "
                    "user override."
                )
            defaults[mode] = route_id

        rule_ids: set[str] = set()
        rules: list[DocumentationModelEscalationRule] = []
        for rule in self.escalation_rules:
            if not isinstance(rule, DocumentationModelEscalationRule):
                raise DocumentationModelPolicyError(
                    "escalation_rules must contain "
                    "DocumentationModelEscalationRule values."
                )
            if rule.rule_id in rule_ids:
                raise DocumentationModelPolicyError(
                    f"Duplicate escalation rule_id: {rule.rule_id!r}."
                )
            rule_ids.add(rule.rule_id)
            target_id = references.get(rule.target_route_id)
            if target_id is None:
                raise DocumentationModelPolicyError(
                    f"Escalation rule {rule.rule_id!r} references unknown route or "
                    f"alias {rule.target_route_id!r}."
                )
            target = route_ids[target_id]
            unsupported_modes = set(rule.modes) - set(target.modes)
            if unsupported_modes:
                raise DocumentationModelPolicyError(
                    f"Escalation target {target_id!r} does not support modes "
                    f"{sorted(unsupported_modes)!r}."
                )
            if any(
                _TIER_ORDER[target.tier] < _TIER_ORDER[source_tier]
                for source_tier in rule.from_tiers
            ):
                raise DocumentationModelPolicyError(
                    f"Escalation rule {rule.rule_id!r} cannot downgrade from "
                    f"{rule.from_tiers!r} to {target.tier!r}."
                )
            rules.append(replace(rule, target_route_id=target_id))

        object.__setattr__(self, "routes", routes)
        object.__setattr__(self, "mode_defaults", defaults)
        object.__setattr__(
            self,
            "escalation_rules",
            tuple(sorted(rules, key=lambda rule: (rule.priority, rule.rule_id))),
        )

    @property
    def policy_hash(self) -> str:
        """Return the stable hash used to audit a selection."""
        encoded = self.to_json().encode("utf-8")
        return f"sha256:{hashlib.sha256(encoded).hexdigest()}"

    def route_for_reference(self, reference: str) -> DocumentationModelRoute:
        """Resolve a route id or configured alias without provider assumptions."""
        reference = _required_text(reference, "route reference")
        for route in self.routes:
            if reference == route.route_id or reference in route.aliases:
                return route
        raise DocumentationModelPolicyError(
            f"Unknown model route or alias: {reference!r}."
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "routes": [route.to_dict() for route in self.routes],
            "mode_defaults": {
                mode: self.mode_defaults[mode]
                for mode in sorted(
                    SUPPORTED_INVOCATION_MODES, key=_MODE_ORDER.__getitem__
                )
            },
            "escalation_rules": [rule.to_dict() for rule in self.escalation_rules],
        }

    def to_json(self) -> str:
        """Return canonical JSON suitable for hashing and checked-in policy files."""
        return json.dumps(
            self.to_dict(), sort_keys=True, separators=(",", ":"), ensure_ascii=False
        )

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "DocumentationModelRoutingPolicy":
        _validate_object(
            payload,
            {"schema_version", "routes", "mode_defaults", "escalation_rules"},
            "model-routing policy",
        )
        routes_payload = _object_sequence(payload.get("routes"), "routes")
        rules_payload = _object_sequence(
            payload.get("escalation_rules", ()), "escalation_rules"
        )
        mode_defaults = payload.get("mode_defaults")
        if not isinstance(mode_defaults, Mapping):
            raise DocumentationModelPolicyError("mode_defaults must be an object.")
        return cls(
            routes=tuple(
                DocumentationModelRoute.from_dict(route) for route in routes_payload
            ),
            mode_defaults={
                str(mode): _required_text(reference, f"{mode} default")
                for mode, reference in mode_defaults.items()
            },
            escalation_rules=tuple(
                DocumentationModelEscalationRule.from_dict(rule)
                for rule in rules_payload
            ),
            schema_version=_required_text(
                payload.get("schema_version"), "schema_version"
            ),
        )


@dataclass(frozen=True)
class DocumentationModelOverride:
    """Explicit user choice of a configured route or an inline public model id."""

    route_id: str | None = None
    provider_family: str | None = None
    provider_id: str | None = None
    model_id: str | None = None
    tier: str | None = None

    def __post_init__(self) -> None:
        inline_values = (
            self.provider_family,
            self.provider_id,
            self.model_id,
            self.tier,
        )
        if self.route_id is not None:
            _validate_slug(self.route_id, "override route_id")
            if any(value is not None for value in inline_values):
                raise DocumentationModelPolicyError(
                    "A model override must use either route_id or the complete "
                    "inline provider/model fields, not both."
                )
            return
        if any(value is None for value in inline_values):
            raise DocumentationModelPolicyError(
                "An inline model override requires provider_family, provider_id, "
                "model_id, and tier."
            )
        _validate_provider_family(str(self.provider_family))
        _validate_public_identifier(str(self.provider_id), "override provider_id")
        _validate_public_identifier(str(self.model_id), "override model_id")
        _validate_tier(str(self.tier))

    def to_dict(self) -> dict[str, Any]:
        if self.route_id is not None:
            return {"route_id": self.route_id}
        return {
            "provider_family": self.provider_family,
            "provider_id": self.provider_id,
            "model_id": self.model_id,
            "tier": self.tier,
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "DocumentationModelOverride":
        _validate_object(
            payload,
            {"route_id", "provider_family", "provider_id", "model_id", "tier"},
            "model override",
        )
        return cls(
            route_id=_optional_text(payload.get("route_id")),
            provider_family=_optional_text(payload.get("provider_family")),
            provider_id=_optional_text(payload.get("provider_id")),
            model_id=_optional_text(payload.get("model_id")),
            tier=_optional_text(payload.get("tier")),
        )


@dataclass(frozen=True)
class DocumentationModelRoutingRequest:
    """One credential-free request to choose a wiki-update agent model."""

    mode: str
    signals: tuple[str, ...] = ()
    override: DocumentationModelOverride | None = None

    def __post_init__(self) -> None:
        _validate_mode(self.mode)
        if self.override is not None and not isinstance(
            self.override, DocumentationModelOverride
        ):
            raise DocumentationModelPolicyError(
                "override must be a DocumentationModelOverride or null."
            )
        signals = tuple(
            sorted({_validate_slug(value, "routing signal") for value in self.signals})
        )
        object.__setattr__(self, "signals", signals)

    def to_dict(self) -> dict[str, Any]:
        return {
            "mode": self.mode,
            "signals": list(self.signals),
            "override": self.override.to_dict() if self.override else None,
        }

    @classmethod
    def from_dict(
        cls, payload: Mapping[str, Any]
    ) -> "DocumentationModelRoutingRequest":
        _validate_object(payload, {"mode", "signals", "override"}, "routing request")
        override_payload = payload.get("override")
        if override_payload is not None and not isinstance(override_payload, Mapping):
            raise DocumentationModelPolicyError("override must be an object or null.")
        return cls(
            mode=_required_text(payload.get("mode"), "mode"),
            signals=_text_sequence(payload.get("signals", ()), "routing signals"),
            override=(
                DocumentationModelOverride.from_dict(override_payload)
                if isinstance(override_payload, Mapping)
                else None
            ),
        )


@dataclass(frozen=True)
class DocumentationModelSelection:
    """Credential-free model selection produced by a routing decision."""

    mode: str
    route_id: str
    provider_family: str
    provider_id: str
    model_id: str
    tier: str
    basis: str
    policy_hash: str
    default_route_id: str
    matched_rule_id: str | None = None
    signals: tuple[str, ...] = ()
    schema_version: str = DOCUMENTATION_MODEL_SELECTION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.schema_version != DOCUMENTATION_MODEL_SELECTION_SCHEMA_VERSION:
            raise DocumentationModelPolicyError(
                "Unsupported documentation model-selection schema_version."
            )
        _validate_mode(self.mode)
        _validate_slug(self.route_id, "selection route_id")
        _validate_provider_family(self.provider_family)
        _validate_public_identifier(self.provider_id, "selection provider_id")
        _validate_public_identifier(self.model_id, "selection model_id")
        _validate_tier(self.tier)
        if self.basis not in SUPPORTED_SELECTION_BASES:
            raise DocumentationModelPolicyError(
                f"Unsupported model-selection basis: {self.basis!r}."
            )
        if not _HEX_DIGEST_RE.fullmatch(self.policy_hash):
            raise DocumentationModelPolicyError(
                "policy_hash must be a lowercase sha256 digest."
            )
        _validate_slug(self.default_route_id, "default_route_id")
        if self.basis == "configured-escalation":
            if self.matched_rule_id is None:
                raise DocumentationModelPolicyError(
                    "An escalated selection requires matched_rule_id."
                )
            _validate_slug(self.matched_rule_id, "matched_rule_id")
        elif self.matched_rule_id is not None:
            raise DocumentationModelPolicyError(
                "matched_rule_id is valid only for configured escalation."
            )
        if self.basis == "mode-default" and (
            self.route_id != self.default_route_id or self.tier != "low-cost"
        ):
            raise DocumentationModelPolicyError(
                "A mode-default selection must resolve the recorded low-cost "
                "default route."
            )
        signals = tuple(
            sorted(
                {_validate_slug(value, "selection signal") for value in self.signals}
            )
        )
        object.__setattr__(self, "signals", signals)

    def to_dict(self) -> dict[str, Any]:
        """Return fixed-field model metadata that cannot carry credentials."""
        return {
            "schema_version": self.schema_version,
            "mode": self.mode,
            "route_id": self.route_id,
            "provider_family": self.provider_family,
            "provider_id": self.provider_id,
            "model_id": self.model_id,
            "tier": self.tier,
            "basis": self.basis,
            "policy_hash": self.policy_hash,
            "default_route_id": self.default_route_id,
            "matched_rule_id": self.matched_rule_id,
            "signals": list(self.signals),
        }

    def to_json(self) -> str:
        return json.dumps(
            self.to_dict(), sort_keys=True, separators=(",", ":"), ensure_ascii=False
        )

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "DocumentationModelSelection":
        _validate_object(
            payload,
            {
                "schema_version",
                "mode",
                "route_id",
                "provider_family",
                "provider_id",
                "model_id",
                "tier",
                "basis",
                "policy_hash",
                "default_route_id",
                "matched_rule_id",
                "signals",
            },
            "model selection",
        )
        return cls(
            mode=_required_text(payload.get("mode"), "mode"),
            route_id=_required_text(payload.get("route_id"), "route_id"),
            provider_family=_required_text(
                payload.get("provider_family"), "provider_family"
            ),
            provider_id=_required_text(payload.get("provider_id"), "provider_id"),
            model_id=_required_text(payload.get("model_id"), "model_id"),
            tier=_required_text(payload.get("tier"), "tier"),
            basis=_required_text(payload.get("basis"), "basis"),
            policy_hash=_required_text(payload.get("policy_hash"), "policy_hash"),
            default_route_id=_required_text(
                payload.get("default_route_id"), "default_route_id"
            ),
            matched_rule_id=_optional_text(payload.get("matched_rule_id")),
            signals=_text_sequence(payload.get("signals", ()), "selection signals"),
            schema_version=_required_text(
                payload.get("schema_version"), "schema_version"
            ),
        )


def select_documentation_model(
    policy: DocumentationModelRoutingPolicy,
    request: DocumentationModelRoutingRequest,
) -> DocumentationModelSelection:
    """Select a model without invoking a provider or reading credentials."""
    default_route_id = policy.mode_defaults[request.mode]
    default_route = policy.route_for_reference(default_route_id)

    if request.override is not None:
        route = _resolve_override(policy, request.mode, request.override)
        return _selection(
            policy=policy,
            request=request,
            route=route,
            route_id=(
                route.route_id
                if request.override.route_id is not None
                else _inline_override_id(route)
            ),
            default_route_id=default_route_id,
            basis="explicit-user-override",
        )

    signal_set = set(request.signals)
    for rule in policy.escalation_rules:
        if (
            request.mode in rule.modes
            and default_route.tier in rule.from_tiers
            and signal_set.intersection(rule.signals)
        ):
            route = policy.route_for_reference(rule.target_route_id)
            return _selection(
                policy=policy,
                request=request,
                route=route,
                route_id=route.route_id,
                default_route_id=default_route_id,
                basis="configured-escalation",
                matched_rule_id=rule.rule_id,
            )

    return _selection(
        policy=policy,
        request=request,
        route=default_route,
        route_id=default_route.route_id,
        default_route_id=default_route_id,
        basis="mode-default",
    )


def validate_documentation_model_selection(
    policy: DocumentationModelRoutingPolicy,
    request: DocumentationModelRoutingRequest,
    selection: DocumentationModelSelection,
) -> DocumentationModelSelection:
    """Validate selection metadata against its originating policy and request.

    This proves only that the deterministic choice was reproduced.  It is not
    an execution receipt and cannot prove which runner/model was actually used.
    """

    if selection.policy_hash != policy.policy_hash:
        raise DocumentationModelPolicyError(
            "Model selection policy_hash does not match the routing policy."
        )
    expected = select_documentation_model(policy, request)
    if selection.to_dict() != expected.to_dict():
        raise DocumentationModelPolicyError(
            "Model selection does not match the deterministic policy decision."
        )
    return selection


def _selection(
    *,
    policy: DocumentationModelRoutingPolicy,
    request: DocumentationModelRoutingRequest,
    route: DocumentationModelRoute,
    route_id: str,
    default_route_id: str,
    basis: str,
    matched_rule_id: str | None = None,
) -> DocumentationModelSelection:
    return DocumentationModelSelection(
        mode=request.mode,
        route_id=route_id,
        provider_family=route.provider_family,
        provider_id=route.provider_id,
        model_id=route.model_id,
        tier=route.tier,
        basis=basis,
        policy_hash=policy.policy_hash,
        default_route_id=default_route_id,
        matched_rule_id=matched_rule_id,
        signals=request.signals,
    )


def _resolve_override(
    policy: DocumentationModelRoutingPolicy,
    mode: str,
    override: DocumentationModelOverride,
) -> DocumentationModelRoute:
    if override.route_id is not None:
        route = policy.route_for_reference(override.route_id)
        if mode not in route.modes:
            raise DocumentationModelPolicyError(
                f"Override route {route.route_id!r} does not support mode {mode!r}."
            )
        return route
    return DocumentationModelRoute(
        route_id="inline-user-override",
        provider_family=str(override.provider_family),
        provider_id=str(override.provider_id),
        model_id=str(override.model_id),
        tier=str(override.tier),
        modes=(mode,),
    )


def _inline_override_id(route: DocumentationModelRoute) -> str:
    identity = json.dumps(
        {
            "provider_family": route.provider_family,
            "provider_id": route.provider_id,
            "model_id": route.model_id,
            "tier": route.tier,
        },
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return f"user-override-{hashlib.sha256(identity).hexdigest()[:16]}"


def _validate_object(payload: Mapping[str, Any], allowed: set[str], label: str) -> None:
    require_mapping(
        payload,
        error=DocumentationModelPolicyError(f"{label} must be an object."),
    )
    _reject_sensitive_keys(payload)
    require_exact_fields(
        payload,
        allowed=allowed,
        required=(),
        mapping_error=DocumentationModelPolicyError(
            f"{label} must be an object."
        ),
        missing_error=lambda fields: AssertionError(fields),
        unknown_error=lambda fields: DocumentationModelPolicyError(
            f"Unsupported {label} fields: {list(fields)!r}."
        ),
        stringify_keys=True,
    )


def _reject_sensitive_keys(value: Any, path: str = "$") -> None:
    if isinstance(value, Mapping):
        for raw_key, item in value.items():
            key = str(raw_key)
            normalized = re.sub(r"[^a-z0-9]+", "_", key.lower()).strip("_")
            if normalized in _SENSITIVE_KEYS:
                raise DocumentationModelPolicyError(
                    f"Credential-bearing field {path}.{key} is forbidden in "
                    "model-routing contracts."
                )
            _reject_sensitive_keys(item, f"{path}.{key}")
    elif isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            _reject_sensitive_keys(item, f"{path}[{index}]")


def _required_text(value: Any, label: str) -> str:
    """Retain the model policy's historical whitespace normalization."""

    return require_nonempty_text(
        value,
        error=DocumentationModelPolicyError(
            f"{label} must be a non-empty string."
        ),
        normalize=True,
        reject_control_characters=False,
    )


def _optional_text(value: Any) -> str | None:
    return trimmed_text_or_none(
        value,
        error=DocumentationModelPolicyError(
            "Optional text values must be strings."
        ),
    )


def _text_sequence(value: Any, label: str) -> tuple[str, ...]:
    return require_string_tuple(
        value,
        error=DocumentationModelPolicyError(
            f"{label} must be a list of strings."
        ),
        container_type=(list, tuple),
        item_parser=lambda item: _required_text(item, label),
    )


def _object_sequence(value: Any, label: str) -> tuple[Mapping[str, Any], ...]:
    return require_mapping_tuple(
        value,
        error=DocumentationModelPolicyError(
            f"{label} must be a list of objects."
        ),
        container_type=(list, tuple),
    )


def _validate_slug(value: Any, label: str) -> str:
    text = _required_text(value, label)
    if value != text:
        raise DocumentationModelPolicyError(
            f"{label} cannot have leading or trailing whitespace."
        )
    if not _SLUG_RE.fullmatch(text):
        raise DocumentationModelPolicyError(
            f"{label} must be a lowercase portable identifier: {text!r}."
        )
    return text


def _validate_public_identifier(value: Any, label: str) -> str:
    text = _required_text(value, label)
    if value != text:
        raise DocumentationModelPolicyError(
            f"{label} cannot have leading or trailing whitespace."
        )
    if len(text) > 256 or _CONTROL_RE.search(text):
        raise DocumentationModelPolicyError(
            f"{label} must be a single printable value of at most 256 characters."
        )
    if "://" in text or text.startswith("//") or "?" in text or "#" in text:
        raise DocumentationModelPolicyError(
            f"{label} must be a public identifier, not an endpoint or URL."
        )
    if _CREDENTIAL_VALUE_RE.match(text):
        raise DocumentationModelPolicyError(
            f"{label} resembles credential material; credentials are forbidden."
        )
    if not _PUBLIC_IDENTIFIER_RE.fullmatch(text):
        raise DocumentationModelPolicyError(
            f"{label} must be an argv-safe public identifier without shell "
            "metacharacters or whitespace."
        )
    return text


def _validate_provider_family(value: Any) -> str:
    text = _required_text(value, "provider_family")
    if value != text:
        raise DocumentationModelPolicyError(
            "provider_family cannot have leading or trailing whitespace."
        )
    if text not in SUPPORTED_PROVIDER_FAMILIES:
        raise DocumentationModelPolicyError(
            f"Unsupported provider_family {text!r}; expected one of "
            f"{sorted(SUPPORTED_PROVIDER_FAMILIES)!r}."
        )
    return text


def _validate_tier(value: Any) -> str:
    text = _required_text(value, "model tier")
    if value != text:
        raise DocumentationModelPolicyError(
            "model tier cannot have leading or trailing whitespace."
        )
    if text not in SUPPORTED_MODEL_TIERS:
        raise DocumentationModelPolicyError(
            f"Unsupported model tier {text!r}; expected one of "
            f"{sorted(SUPPORTED_MODEL_TIERS)!r}."
        )
    return text


def _validate_mode(value: Any) -> str:
    text = _required_text(value, "invocation mode")
    if value != text:
        raise DocumentationModelPolicyError(
            "invocation mode cannot have leading or trailing whitespace."
        )
    if text not in SUPPORTED_INVOCATION_MODES:
        raise DocumentationModelPolicyError(
            f"Unsupported invocation mode {text!r}; expected one of "
            f"{sorted(SUPPORTED_INVOCATION_MODES)!r}."
        )
    return text


def _normalise_modes(values: Any, label: str) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)) or not isinstance(values, (list, tuple)):
        raise DocumentationModelPolicyError(f"{label} must be a list of modes.")
    modes = tuple(
        sorted({_validate_mode(value) for value in values}, key=_MODE_ORDER.__getitem__)
    )
    if not modes:
        raise DocumentationModelPolicyError(f"{label} cannot be empty.")
    return modes
