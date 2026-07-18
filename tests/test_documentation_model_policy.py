"""Focused tests for provider-neutral documentation model routing."""

from __future__ import annotations

import json

import pytest

from llm_wiki_cli.services.documentation_model_policy import (
    DOCUMENTATION_MODEL_ROUTING_SCHEMA_VERSION,
    DOCUMENTATION_MODEL_SELECTION_SCHEMA_VERSION,
    SUPPORTED_PROVIDER_FAMILIES,
    DocumentationModelEscalationRule,
    DocumentationModelOverride,
    DocumentationModelPolicyError,
    DocumentationModelRoute,
    DocumentationModelRoutingPolicy,
    DocumentationModelRoutingRequest,
    DocumentationModelSelection,
    select_documentation_model,
    validate_documentation_model_selection,
)


def _route(
    route_id: str,
    family: str,
    provider_id: str,
    model_id: str,
    tier: str,
    *,
    modes: tuple[str, ...] = ("generic-agent", "handoff"),
    aliases: tuple[str, ...] = (),
) -> DocumentationModelRoute:
    return DocumentationModelRoute(
        route_id=route_id,
        provider_family=family,
        provider_id=provider_id,
        model_id=model_id,
        tier=tier,
        modes=modes,
        aliases=aliases,
    )


def _policy() -> DocumentationModelRoutingPolicy:
    return DocumentationModelRoutingPolicy(
        routes=(
            _route(
                "openai-small",
                "openai-compatible",
                "configured-openai-gateway",
                "gpt-4.1-mini",
                "low-cost",
                aliases=("openai-wiki",),
            ),
            _route(
                "anthropic-small",
                "anthropic",
                "configured-anthropic",
                "claude-3-5-haiku-latest",
                "low-cost",
                modes=("handoff",),
                aliases=("handoff-economy",),
            ),
            _route(
                "gemini-small",
                "google-gemini",
                "configured-google",
                "gemini-2.0-flash",
                "low-cost",
                modes=("generic-agent",),
                aliases=("generic-economy",),
            ),
            _route(
                "local-small",
                "local-self-hosted",
                "configured-local-runner",
                "qwen2.5-coder:7b",
                "low-cost",
                aliases=("local-wiki",),
            ),
            _route(
                "other-balanced",
                "other",
                "configured-third-party",
                "vendor/docs-balanced-v17",
                "balanced",
            ),
            _route(
                "other-capable",
                "other",
                "configured-third-party",
                "vendor/docs-capability-v9",
                "capability",
            ),
        ),
        mode_defaults={
            "generic-agent": "generic-economy",
            "handoff": "handoff-economy",
        },
        escalation_rules=(
            DocumentationModelEscalationRule(
                rule_id="capability-on-high-risk",
                signals=("high-severity-review", "repeated-failure"),
                target_route_id="other-capable",
                modes=("handoff", "generic-agent"),
                priority=10,
            ),
            DocumentationModelEscalationRule(
                rule_id="balanced-on-ambiguity",
                signals=("semantic-ambiguity",),
                target_route_id="other-balanced",
                modes=("generic-agent", "handoff"),
                priority=20,
            ),
        ),
    )


def test_supports_provider_families_without_an_openai_default():
    policy = _policy()

    assert SUPPORTED_PROVIDER_FAMILIES == {
        "openai-compatible",
        "anthropic",
        "google-gemini",
        "local-self-hosted",
        "other",
    }
    assert {route.provider_family for route in policy.routes} == (
        SUPPORTED_PROVIDER_FAMILIES
    )

    generic = select_documentation_model(
        policy, DocumentationModelRoutingRequest(mode="generic-agent")
    )
    handoff = select_documentation_model(
        policy, DocumentationModelRoutingRequest(mode="handoff")
    )

    assert (generic.provider_family, generic.model_id, generic.tier) == (
        "google-gemini",
        "gemini-2.0-flash",
        "low-cost",
    )
    assert (handoff.provider_family, handoff.model_id, handoff.tier) == (
        "anthropic",
        "claude-3-5-haiku-latest",
        "low-cost",
    )
    assert generic.basis == handoff.basis == "mode-default"


def test_both_invocation_modes_require_low_cost_defaults():
    policy = _policy()
    routes = tuple(
        route
        for route in policy.routes
        if route.route_id not in {"gemini-small", "other-capable"}
    ) + (
        _route(
            "gemini-capable",
            "google-gemini",
            "configured-google",
            "gemini-configured-capability",
            "capability",
            modes=("generic-agent",),
        ),
    )

    with pytest.raises(DocumentationModelPolicyError, match="must use the low-cost"):
        DocumentationModelRoutingPolicy(
            routes=routes,
            mode_defaults={
                "generic-agent": "gemini-capable",
                "handoff": "anthropic-small",
            },
        )

    with pytest.raises(DocumentationModelPolicyError, match="define exactly"):
        DocumentationModelRoutingPolicy(
            routes=policy.routes,
            mode_defaults={"generic-agent": "gemini-small"},
        )


def test_configured_signals_escalate_deterministically_not_implicitly():
    policy = _policy()

    ordinary = select_documentation_model(
        policy,
        DocumentationModelRoutingRequest(
            mode="generic-agent", signals=("unrecognized-but-public-signal",)
        ),
    )
    escalated = select_documentation_model(
        policy,
        DocumentationModelRoutingRequest(
            mode="generic-agent",
            signals=("semantic-ambiguity", "repeated-failure"),
        ),
    )

    assert ordinary.route_id == "gemini-small"
    assert ordinary.tier == "low-cost"
    assert ordinary.matched_rule_id is None
    assert escalated.route_id == "other-capable"
    assert escalated.tier == "capability"
    assert escalated.basis == "configured-escalation"
    assert escalated.matched_rule_id == "capability-on-high-risk"
    assert escalated.signals == ("repeated-failure", "semantic-ambiguity")


def test_explicit_user_override_accepts_route_alias_or_inline_provider():
    policy = _policy()

    configured = select_documentation_model(
        policy,
        DocumentationModelRoutingRequest(
            mode="handoff",
            override=DocumentationModelOverride(route_id="local-wiki"),
        ),
    )
    inline = select_documentation_model(
        policy,
        DocumentationModelRoutingRequest(
            mode="generic-agent",
            override=DocumentationModelOverride(
                provider_family="other",
                provider_id="configured-future-provider",
                model_id="future-provider/arbitrary-model-2042@preview",
                tier="capability",
            ),
        ),
    )

    assert configured.route_id == "local-small"
    assert configured.provider_family == "local-self-hosted"
    assert configured.basis == "explicit-user-override"
    assert inline.route_id.startswith("user-override-")
    assert inline.model_id == "future-provider/arbitrary-model-2042@preview"
    assert inline.tier == "capability"
    assert inline.basis == "explicit-user-override"


def test_exact_model_names_are_configuration_not_protocol_enums():
    route = _route(
        "new-vendor-model",
        "other",
        "configured-new-vendor",
        "some-provider/model-that-did-not-exist-at-schema-freeze@nightly",
        "low-cost",
    )
    policy = DocumentationModelRoutingPolicy(
        routes=(route,),
        mode_defaults={
            "generic-agent": "new-vendor-model",
            "handoff": "new-vendor-model",
        },
    )

    selected = select_documentation_model(
        policy, DocumentationModelRoutingRequest(mode="handoff")
    )

    assert selected.model_id == route.model_id
    assert selected.provider_family == "other"


def test_policy_and_selection_round_trip_with_canonical_serialization():
    policy = _policy()
    payload = policy.to_dict()
    reordered = {
        "escalation_rules": list(reversed(payload["escalation_rules"])),
        "mode_defaults": {
            "handoff": payload["mode_defaults"]["handoff"],
            "generic-agent": payload["mode_defaults"]["generic-agent"],
        },
        "routes": list(reversed(payload["routes"])),
        "schema_version": payload["schema_version"],
    }

    restored = DocumentationModelRoutingPolicy.from_dict(reordered)
    selection = select_documentation_model(
        restored,
        DocumentationModelRoutingRequest.from_dict(
            {
                "mode": "handoff",
                "signals": ["repeated-failure"],
                "override": None,
            }
        ),
    )
    restored_selection = DocumentationModelSelection.from_dict(selection.to_dict())

    assert restored.to_json() == policy.to_json()
    assert restored.policy_hash == policy.policy_hash
    assert restored_selection == selection
    assert json.loads(selection.to_json()) == selection.to_dict()
    assert payload["schema_version"] == DOCUMENTATION_MODEL_ROUTING_SCHEMA_VERSION
    assert selection.schema_version == DOCUMENTATION_MODEL_SELECTION_SCHEMA_VERSION


def test_forged_mode_default_selection_and_policy_hash_fail_closed():
    policy = _policy()
    request = DocumentationModelRoutingRequest(mode="generic-agent")
    genuine = select_documentation_model(policy, request)

    forged_default = {
        **genuine.to_dict(),
        "route_id": "other-capable",
        "provider_family": "other",
        "provider_id": "configured-third-party",
        "model_id": "vendor/docs-capability-v9",
        "tier": "capability",
    }
    with pytest.raises(DocumentationModelPolicyError, match="mode-default"):
        DocumentationModelSelection.from_dict(forged_default)

    forged_hash = {
        **genuine.to_dict(),
        "policy_hash": "sha256:" + ("0" * 64),
    }
    parsed = DocumentationModelSelection.from_dict(forged_hash)
    with pytest.raises(DocumentationModelPolicyError, match="policy_hash"):
        validate_documentation_model_selection(policy, request, parsed)


@pytest.mark.parametrize(
    ("payload_factory", "message"),
    [
        (
            lambda: {
                **_policy().to_dict(),
                "api_key": "sk-should-not-be-here",
            },
            "Credential-bearing field",
        ),
        (
            lambda: {
                **_policy().to_dict(),
                "routes": [
                    {
                        **_policy().to_dict()["routes"][0],
                        "headers": {"Authorization": "Bearer hidden"},
                    }
                ],
            },
            "Credential-bearing field",
        ),
    ],
)
def test_policy_payload_rejects_secret_bearing_fields(payload_factory, message):
    with pytest.raises(DocumentationModelPolicyError, match=message):
        DocumentationModelRoutingPolicy.from_dict(payload_factory())


def test_selection_has_only_fixed_public_runner_fields():
    selection = select_documentation_model(
        _policy(), DocumentationModelRoutingRequest(mode="generic-agent")
    )
    payload = selection.to_dict()
    serialized = json.dumps(payload, sort_keys=True).lower()

    assert set(payload) == {
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
    }
    for forbidden in (
        "api_key",
        "authorization",
        "password",
        "secret",
        "access_token",
        "endpoint",
        "base_url",
    ):
        assert forbidden not in serialized


def test_invalid_provider_alias_mode_and_credential_like_values_fail_closed():
    with pytest.raises(DocumentationModelPolicyError, match="provider_family"):
        _route(
            "unknown-provider",
            "openai",
            "configured-openai",
            "some-model",
            "low-cost",
        )
    with pytest.raises(DocumentationModelPolicyError, match="credential material"):
        _route(
            "credential-model",
            "other",
            "configured-provider",
            "sk-not-a-model-id",
            "low-cost",
        )
    with pytest.raises(DocumentationModelPolicyError, match="not an endpoint"):
        _route(
            "endpoint-provider",
            "other",
            "https://provider.example.test/v1?token=hidden",
            "some-model",
            "low-cost",
        )
    with pytest.raises(DocumentationModelPolicyError, match="Unsupported invocation"):
        DocumentationModelRoutingRequest(mode="automatic")

    duplicate_alias = _route(
        "alias-a",
        "other",
        "configured-a",
        "model-a",
        "low-cost",
        aliases=("shared",),
    )
    with pytest.raises(DocumentationModelPolicyError, match="is shared"):
        DocumentationModelRoutingPolicy(
            routes=(
                duplicate_alias,
                _route(
                    "alias-b",
                    "local-self-hosted",
                    "configured-b",
                    "model-b",
                    "low-cost",
                    aliases=("shared",),
                ),
            ),
            mode_defaults={
                "generic-agent": "alias-a",
                "handoff": "alias-b",
            },
        )


@pytest.mark.parametrize(
    ("provider_id", "model_id"),
    [
        ("runner;echo-pwn", "safe-model"),
        ("safe-runner", "model$(touch-pwn)"),
        ("safe-runner", "model`whoami`"),
        ("safe-runner", "model&echo-pwn"),
        ("safe-runner", "model|echo-pwn"),
        ("safe-runner", "model%PATH%"),
        ("safe-runner", "model^echo-pwn"),
        ("safe-runner", "model!PATH!"),
    ],
)
def test_runner_identifiers_reject_cross_shell_argv_metacharacters(
    provider_id, model_id
):
    with pytest.raises(DocumentationModelPolicyError, match="argv-safe"):
        _route(
            "unsafe-route",
            "other",
            provider_id,
            model_id,
            "low-cost",
        )


def test_override_shape_and_mode_support_are_validated():
    with pytest.raises(DocumentationModelPolicyError, match="either route_id"):
        DocumentationModelOverride(
            route_id="local-small",
            provider_family="other",
            provider_id="configured-provider",
            model_id="model",
            tier="low-cost",
        )
    with pytest.raises(DocumentationModelPolicyError, match="requires provider_family"):
        DocumentationModelOverride(provider_family="other")
    with pytest.raises(DocumentationModelPolicyError, match="does not support mode"):
        select_documentation_model(
            _policy(),
            DocumentationModelRoutingRequest(
                mode="generic-agent",
                override=DocumentationModelOverride(route_id="anthropic-small"),
            ),
        )
