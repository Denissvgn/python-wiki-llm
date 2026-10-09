"""New owned workflow inputs and source-grounded obligations, independent of queue labels."""

from __future__ import annotations

from copy import deepcopy
from collections.abc import Mapping
import hashlib
import json
from pathlib import Path
from typing import Any

from llm_wiki_cli import api
from llm_wiki_cli.services.knowledge_storage_lifecycle import migrate_knowledge_storage
from tests.developer_value.workflow_fixtures import WorkflowProject, sync_workflow, task_request, write_description
from tests.developer_value.triage_oracle import commitment, occurrence_id

VARIANTS = ("source-only", "native-absent", "legacy", "adopted-flat", "sharded", "packed")
ADOPTED = frozenset({"adopted-flat", "sharded", "packed"})
NATIVE = frozenset({"sharded", "packed"})
BEFORE_PROSE = "Routes the first four records by default. Nonpositive limits return no records."
AFTER_PROSE = "Routes the last four records by default. Nonpositive limits return no records."
SOURCE = '''from pathlib import Path
Path("source-execution-tripwire").write_text("Unexpected source execution")

class Harbor:
    """Route a bounded batch of harbor records."""
    def route(self, records, limit=4):
        return records[:limit] if limit > 0 else []

def public_route(records):
    return Harbor().route(records)
'''
CLIENT = '''from policy import Harbor as LocalHarbor

def direct_route(records):
    return LocalHarbor().route(records)

def assigned_route(records):
    harbor = LocalHarbor()
    return harbor.route(records)

def dynamic_route(factory, records):
    return factory().route(records)
'''
HAZARDS = '''class NamespaceHarbor:
    def route(self, records):
        return records
    (route := lambda self, records: [])

class EarlyHarbor:
    def route(self, records):
        return records

class LaterHarbor:
    def route(self, records):
        return []

def namespace_route(records):
    return NamespaceHarbor().route(records)

def conditional_route(condition, records):
    harbor = EarlyHarbor()
    alias = LaterHarbor()
    condition and (harbor := alias)
    return harbor.route(records)

def ordered_route(condition, records):
    harbor = LaterHarbor()
    alias = EarlyHarbor()
    0 < ((harbor := alias), 1)[1] < condition
    return harbor.route(records)
'''
SCOPE = '''class Repeated:
    def touch(self):
        return 1

class Repeated:
    def touch(self):
        return 2
'''
SOURCES = {"policy.py": SOURCE, "client.py": CLIENT, "hazards.py": HAZARDS, "scope.py": SCOPE}
OWNER = "entities/Harbor.md:Harbor"
STAGES = ("before", "after-source-edit", "pending-after-sync", "after-prose-sync", "acknowledged")


def request_for(variant: str) -> dict[str, Any]:
    request = task_request(native=variant in NATIVE or variant == "native-absent")
    request["task_ref"] = "owned-harbor-combined-change"
    request = json.loads(json.dumps(request).replace("Window.clip", "Harbor.route").replace("Window.md", "Harbor.md"))
    if variant == "native-absent":
        request["options"]["knowledge_mode"] = "auto"
    return request


def source_after() -> str:
    return SOURCE.replace("records[:limit]", "records[max(0, len(records) - limit):]")


def client_after() -> str:
    return CLIENT.replace("return LocalHarbor().route(records)", "return LocalHarbor().route(records, limit=2)")


def input_packet() -> dict[str, Any]:
    """Declared before provider invocation; this is not a blinded judgment packet."""
    return {"schema_version": "combined-workflow-input/v1", "variants": list(VARIANTS),
        "sources_before": deepcopy(SOURCES), "sources_after": {**SOURCES, "policy.py": source_after(), "client.py": client_after()},
        "prose_before": BEFORE_PROSE, "prose_after": AFTER_PROSE,
        "requests": {variant: request_for(variant) for variant in VARIANTS},
        "stages": list(STAGES), "review_visibility": "author-declared; independent source review required before observation",
        "obligations": [{"stage": stage, "owner": OWNER, "operation": "revise-claim",
                         "evidence": "Harbor.route changes first-N to last-N while authored prose still claims first-N"}
                        for stage in ("after-source-edit", "pending-after-sync")],
        "completed_obligations": {"after-prose-sync": "prose matches the new slice; pending exact review must be acknowledged",
                                  "acknowledged": "current source/prose basis acknowledged by ordinary agent; no approval"},
        "caller_expectations": {"policy.py:Harbor.route": ["policy.py:public_route", "client.py:direct_route", "client.py:assigned_route"],
            "hazards.py:NamespaceHarbor.route": [], "hazards.py:EarlyHarbor.route": ["hazards.py:ordered_route"],
            "hazards.py:LaterHarbor.route": []},
        "caller_reasoning": "Class-local assignment replaces NamespaceHarbor.route; short circuit may choose either receiver; first comparison operand always binds EarlyHarbor before the final call.",
        "runtime_scope": "not executed; AST slice and literal source comparisons only"}


def packet_sha256() -> str:
    return hashlib.sha256(json.dumps(input_packet(), sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def prepare_combined(root: Path, variant: str) -> WorkflowProject:
    if variant not in VARIANTS:
        raise ValueError("Unknown storage variant")
    project = WorkflowProject(root.resolve(), variant)
    project.source.mkdir()
    for path, source in SOURCES.items():
        (project.source / path).write_text(source, encoding="utf-8")
    if variant not in {"source-only", "native-absent"}:
        profile = project.source / ".llm-wiki/source-selection.json"
        profile.parent.mkdir()
        profile.write_text(json.dumps({"schema_version": "llm-wiki-source-selection/v1", "include": list(SOURCES), "exclude": []}) + "\n")
        api.bootstrap_wiki(str(project.source), str(project.wiki))
        write_description(project, BEFORE_PROSE, "entities/Harbor.md")
        sync_workflow(project)
        if variant in ADOPTED:
            api.adopt_maintenance(**project.options, recovery_dir=root / "maintenance-recovery")
        if variant in NATIVE:
            migrate_knowledge_storage(project.wiki, to="sharded-v2" if variant == "sharded" else "packed-v4-deflate", recovery_dir=root / "storage-recovery")
            migrate_knowledge_storage(project.wiki, to="indexed-v8", recovery_dir=root / "manifest-recovery")
    elif variant == "native-absent":
        (project.wiki / "guides").mkdir(parents=True)
        (project.wiki / "guides/orientation.md").write_text("# Harbor routing\n\nInspect policy.py:Harbor.route.\n")
    return project


def reconcile_queue(response: Mapping[str, Any], stage: str, *, sources: dict[str, str], prose: str,
                    durable_owner_available: bool = True) -> dict[str, Any]:
    """Keep every occurrence; provider reasons, weights and labels cannot justify prose edits.

    Rows outside the declared changed prose owner remain unknown for external
    review. This reconciliation is not the prospective 80% triage gate.
    """
    assert stage in STAGES
    expected_sources = SOURCES if stage == "before" else {**SOURCES, "policy.py": source_after(), "client.py": client_after()}
    assert sources == expected_sources, "Stage source bytes differ from the reviewed inputs"
    expected_prose = BEFORE_PROSE if stage in {"before", "after-source-edit", "pending-after-sync"} else AFTER_PROSE
    assert expected_prose in prose, "Stage prose bytes disagree with reviewed claim"
    assert response["advisory"] is True
    assert response["returned"] == len(response["items"])
    assert response["total"] == response["returned"] + response["omitted"]
    assert response["omitted"] == 0 and response.get("truncated", False) is False
    rows = []
    response_sha256 = commitment(response)
    for index, item in enumerate(response["items"]):
        target = item["path"] == "entities/Harbor.md"
        operation = "revise-claim" if target and stage in {"after-source-edit", "pending-after-sync"} else None
        rows.append({"index": index, "response_sha256": response_sha256,
                     "occurrence_id": occurrence_id("combined-harbor", "current", stage, response_sha256, index),
                     "path": item["path"], "owner": OWNER if target else None,
                     "label": "actionable" if operation else "unknown", "operation": operation,
                     "justification": "frozen source/prose mismatch" if operation else "requires separate row source review"})
    assert type(durable_owner_available) is bool
    assert durable_owner_available or stage == "pending-after-sync", "Only the unsolved unadopted pending stage may lack durable custody"
    required = stage in {"after-source-edit", "pending-after-sync"}
    surfaced = any(row["operation"] == "revise-claim" for row in rows)
    if required and durable_owner_available:
        assert surfaced, "Required mismatched prose owner not surfaced"
    return {"stage": stage, "rows": rows, "denominator": len(rows), "not_an_acceptance_score": True,
            "provider_labels_used": False, "frozen_packet_sha256": packet_sha256(), "response_sha256": response_sha256,
            "required_owner_surfaced": surfaced if required else None,
            "covered_owner_actions": [{"owner": OWNER, "operation": "revise-claim"}] if required and surfaced else [],
            "missing_owner_actions": [{"owner": OWNER, "operation": "revise-claim"}] if required and not surfaced else [],
            "unavailable_unsolved": required and not surfaced and not durable_owner_available,
            "source_artifacts": {path: {"text": text, "sha256": hashlib.sha256(text.encode()).hexdigest()} for path, text in sources.items()},
            "prose_artifact": {"text": prose, "sha256": hashlib.sha256(prose.encode()).hexdigest()}}
