"""Ordinary downstream type usage; no provider-private imports or execution."""

from llm_wiki_cli import api
from llm_wiki_cli.api_types import (
    ContextPayload,
    KnowledgeCoverageResult,
    KnowledgeMode,
    MarkdownContextResult,
    NativeInspectionResult,
    TaskContextRequest,
    SearchResult,
    MaintenanceQueueResult,
)


def inspect_project(source: str, wiki: str) -> NativeInspectionResult:
    result = api.inspect_concept(
        "llm-wiki://entities/Item", src_dir=source, wiki_dir=wiki
    )
    count: int = result["cost"]["supplied_paths"]
    bounded: bool = result["truncated"]
    limits: dict[str, int] = result["limits"]
    print(count, bounded, limits)
    return result


def coverage(wiki: str) -> KnowledgeCoverageResult:
    result = api.get_knowledge_coverage(wiki_dir=wiki)
    counts = result["counts"]
    if counts is not None:
        modeled: int = counts["modeled"]
        outcomes = counts["modeled_freshness"]
        if outcomes is not None:
            current: int = outcomes["current"]
            print(modeled, current)
    return result


def contexts(
    source: str, wiki: str, mode: KnowledgeMode
) -> tuple[ContextPayload, MarkdownContextResult]:
    structured = api.build_context(
        source, format="json", wiki_dir=wiki, knowledge_mode=mode
    )
    markdown = api.build_context(
        source, format="markdown", wiki_dir=wiki, knowledge_mode=mode
    )
    return structured, markdown


def offline(raw: bytes) -> tuple[bool, str, bytes]:
    checked = api.validate_context_packet(raw)
    return checked.freshness_evaluated, checked.packet_id, checked.packet.to_bytes()


def reuse(source: str, wiki: str) -> KnowledgeCoverageResult:
    service = api.build_documentation_query_service(source, wiki_dir=wiki)
    api.get_concept("llm-wiki://entities/Item", service=service)
    api.list_concept_sections("llm-wiki://entities/Item", service=service)
    api.traverse_typed_graph("llm-wiki://entities/Item", service=service)
    return api.get_knowledge_coverage(service=service)


def workflow(source: str, wiki: str) -> tuple[SearchResult, MaintenanceQueueResult, api.TaskContext]:
    request: TaskContextRequest = {"schema_version": "llm-wiki-task-request/v1",
        "requirements": [{"id": "contract", "facet": "source-contract", "selector": "app.py:run"}]}
    context = api.build_task_context(request, src_dir=source, wiki_dir=wiki)
    rendered: str = context.rendered
    identity: str | None = context.result_id
    print(rendered, identity)
    with api.open_context_session(src_dir=source, wiki_dir=wiki) as session:
        reply: api.SessionReply = session.read(request)
        print(reply.state, reply.metadata())
    return api.search_wiki("run", src_dir=source, wiki_dir=wiki), api.build_maintenance_queue(source, wiki), context


def scoped_workflow(source: str, wiki: str) -> api.TaskContext:
    request: TaskContextRequest = {"schema_version": "llm-wiki-task-request/v2",
        "requirements": [{"id": "contract", "facet": "source-contract", "selector": "app.py:run"}]}
    return api.build_task_context(request, src_dir=source, wiki_dir=wiki)
