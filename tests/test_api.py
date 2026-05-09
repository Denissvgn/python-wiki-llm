"""Tests for the supported Python source-adapter API."""

from __future__ import annotations

from llm_wiki_cli.api import (
    EXTRACT_SCHEMA_VERSION,
    build_context,
    extract_source,
)


def test_extract_source_returns_stable_payload(tmp_project):
    payload = extract_source(".", summary=True, read_only=True)

    assert payload["schema_version"] == EXTRACT_SCHEMA_VERSION
    assert payload["inventory"]
    first = next(iter(payload["inventory"].values()))
    assert "language" in first


def test_build_context_returns_json_payload(tmp_project):
    payload = build_context(".", budget=100000, focus="all", format="json")

    assert payload["budget"] == 100000
    assert payload["files"]


def test_build_context_returns_markdown_content_and_raw_payload(tmp_project):
    payload = build_context(".", budget=100000, focus="all", format="markdown")

    assert "Context Budget" in payload["content"]
    assert payload["payload"]["files"]
