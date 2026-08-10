"""Privacy and performance gates for generated knowledge."""

from __future__ import annotations

import json
import re
from collections.abc import Iterator, Mapping
from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest

from llm_wiki_cli.services.knowledge_envelope import (
    ConsumedInput,
    ConsumedInputKind,
    ProducerComponentInput,
    RepositoryEvidence,
)
from llm_wiki_cli.services.knowledge_evidence import sha256_bytes
from llm_wiki_cli.services.knowledge_generation import (
    build_knowledge_generation_plan,
)
from llm_wiki_cli.services.wiki_media import contains_uri_authority_userinfo
from tests.knowledge_generation_benchmark import (
    KNOWLEDGE_BENCHMARK_SCALES,
    build_knowledge_benchmark_inputs,
    run_knowledge_benchmark,
)

_WINDOWS_ABSOLUTE_RE = re.compile(r"^[A-Za-z]:[\\/]")
_SENSITIVE_KEY_RE = re.compile(
    r"(?:password|passwd|secret|api[_-]?key|access[_-]?token|private[_-]?key)",
    re.IGNORECASE,
)


def _json_strings(value: Any) -> Iterator[str]:
    if isinstance(value, str):
        yield value
    elif isinstance(value, Mapping):
        for key, child in value.items():
            yield str(key)
            yield from _json_strings(child)
    elif isinstance(value, list):
        for child in value:
            yield from _json_strings(child)


def _json_keys(value: Any) -> Iterator[str]:
    if isinstance(value, Mapping):
        for key, child in value.items():
            yield str(key)
            yield from _json_keys(child)
    elif isinstance(value, list):
        for child in value:
            yield from _json_keys(child)


def test_generated_knowledge_omits_private_runtime_and_credential_canaries(
    tmp_path,
    monkeypatch,
):
    scale = KNOWLEDGE_BENCHMARK_SCALES[0]
    base = build_knowledge_benchmark_inputs(tmp_path, scale)
    source_canary = "knowledge-source-private-4fdd8bf3"
    markdown_canary = "knowledge-markdown-private-20a913ae"
    environment_canary = "knowledge-environment-private-945ac40b"
    option_canary = "knowledge-option-private-e02dd9fd"
    producer_canary = "knowledge-producer-private-a66a380e"
    credential = "https://alice:p4ssw0rd@private.example.invalid/repository"
    private_checkout = Path("/Users/alice/private-checkout")
    monkeypatch.setenv("LLM_WIKI_KNOWLEDGE_PRIVACY_CANARY", environment_canary)

    source_hashes = {
        path: sha256_bytes(f"{source_canary}:{path}".encode())
        for path in base.inventory
    }
    content = dict(base.content_by_page)
    content["index.md"] = (
        content["index.md"]
        + f"\n{markdown_canary}\n"
        + f"\n[credential-canary]({credential})\n"
    )
    private_pages = tuple(
        replace(
            page,
            path=private_checkout / page.relative_path,
        )
        for page in base.pages
    )
    inputs = replace(
        base,
        pages=private_pages,
        content_by_page=content,
        source_content_hashes=source_hashes,
        consumed_inputs=tuple(
            ConsumedInput(
                path=path,
                content_hash=content_hash,
                kind=ConsumedInputKind.SOURCE,
            )
            for path, content_hash in source_hashes.items()
        ),
        repository_evidence=RepositoryEvidence(
            remotes={"origin": credential},
            upstream_remote="origin",
        ),
        generation_options={"privacy_profile": option_canary},
        generation_option_defaults={"privacy_profile": "default"},
        generation_option_allowlist=("privacy_profile",),
        tool=ProducerComponentInput(
            component_id="agent-wiki-cli",
            version="1.4.0",
            configuration={"privacy_canary": producer_canary},
        ),
    )

    plan = build_knowledge_generation_plan(inputs)
    artifact_bytes = {
        "surface": plan.surface_index.content,
        "knowledge": plan.knowledge_index.content,
        "manifest": plan.manifest.content,
    }
    forbidden_values = (
        source_canary,
        markdown_canary,
        environment_canary,
        option_canary,
        producer_canary,
        credential,
        "alice:p4ssw0rd@",
        "private.example.invalid",
        str(private_checkout),
        str(tmp_path),
        "credential-canary",
    )

    for artifact_name, content_bytes in artifact_bytes.items():
        serialized = content_bytes.decode("utf-8")
        payload = json.loads(serialized)
        strings = tuple(_json_strings(payload))

        for forbidden in forbidden_values:
            assert forbidden not in serialized, artifact_name
        has_unix_absolute_path = any(value.startswith("/") for value in strings)
        has_windows_absolute_path = any(
            _WINDOWS_ABSOLUTE_RE.match(value) for value in strings
        )
        has_authority_userinfo = any(
            contains_uri_authority_userinfo(value) for value in strings
        )
        has_sensitive_key = any(
            _SENSITIVE_KEY_RE.search(key) for key in _json_keys(payload)
        )
        assert not has_unix_absolute_path, artifact_name
        assert not has_windows_absolute_path, artifact_name
        assert not has_authority_userinfo, artifact_name
        assert not has_sensitive_key, artifact_name


@pytest.mark.slow
def test_representative_knowledge_generation_stays_deterministic_and_within_budget(
    tmp_path,
):
    results = [
        run_knowledge_benchmark(tmp_path / scale.name, scale, repeats=2)
        for scale in KNOWLEDGE_BENCHMARK_SCALES
    ]

    for scale, result in zip(KNOWLEDGE_BENCHMARK_SCALES, results, strict=True):
        assert result.source_count == scale.source_count
        assert result.page_count == scale.page_count
        assert result.knowledge_bytes <= scale.max_knowledge_bytes
        assert result.max_build_seconds <= scale.max_build_seconds
    assert [result.knowledge_bytes for result in results] == sorted(
        result.knowledge_bytes for result in results
    )
