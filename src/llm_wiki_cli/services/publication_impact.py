"""Portable, deterministic architecture-to-public-topic impact and review."""

from __future__ import annotations

from collections import Counter
from copy import deepcopy
from fnmatch import fnmatchcase
import json
from pathlib import Path
from typing import Any, Mapping

from .instruction_ownership import markdown_anchor
from .knowledge_evidence import hash_json, sha256_bytes
from .knowledge_storage_io import StorageReadSession
from .markdown_sections import parse_markdown_document
from .publication_config import load_publication_config, publication_path
from .publication_contracts import (
    PublicationProtocolError,
    validate_publication_basis,
    validate_publication_report,
    validate_publication_reviews,
)
from .publication_snapshot import (
    build_publication_snapshot,
    build_bootstrap_publication_snapshot,
)


BASIS_SCHEMA = "llm-wiki-publication-basis/v1"
IMPACT_SCHEMA = "llm-wiki-publication-impact/v1"
REVIEWS_SCHEMA = "llm-wiki-publication-reviews/v1"
MAX_JSON_BYTES = 64 * 1024 * 1024


PublicationImpactError = PublicationProtocolError


def read_publication_document(path: str | Path) -> dict[str, Any]:
    """Read bounded JSON with unique keys and finite values."""
    path = Path(path).absolute()
    with StorageReadSession(path.parent).phase() as session:
        raw = session.read(path.name, MAX_JSON_BYTES)
    try:
        result = json.loads(
            raw, object_pairs_hook=_unique_object, parse_constant=_invalid_constant
        )
    except (ValueError, UnicodeError, RecursionError) as exc:
        raise PublicationImpactError(f"Invalid publication JSON: {path.name}") from exc
    if not isinstance(result, dict):
        raise PublicationImpactError("Publication JSON must be an object")
    return result


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise PublicationImpactError(f"Duplicate JSON key: {key}")
        result[key] = value
    return result


def _invalid_constant(value):
    raise PublicationImpactError(f"Nonfinite JSON value: {value}")


def _seal(value: dict[str, Any], key: str) -> dict[str, Any]:
    return {**value, key: hash_json(value)}


def _file_hash(session: StorageReadSession, root: Path, relative: str) -> str | None:
    path = publication_path(root, relative)
    if not path.exists():
        return None
    return sha256_bytes(session.read(relative, MAX_JSON_BYTES))


def _topic_versions(config, baseline):
    previous = (
        {} if baseline is None else {t["id"]: t for t in baseline["config"]["topics"]}
    )
    current = {t["id"]: t for t in config["topics"]}
    for key in sorted(previous.keys() & current.keys()):
        old, new = previous[key], current[key]
        if (old["wiki_page"], old.get("anchor")) != (
            new["wiki_page"],
            new.get("anchor"),
        ):
            identity = "previous:" + hash_json(old).removeprefix("sha256:")[:32]
            previous[identity] = {**old, "id": identity}
    return previous, current


def _target_hash(
    session: StorageReadSession, topic: Mapping[str, Any]
) -> dict[str, Any]:
    path = topic["wiki_page"]
    if not publication_path(session.root, path).exists():
        return {"state": "missing", "hash": None}
    raw = session.read(path, MAX_JSON_BYTES)
    if not topic.get("anchor"):
        return {"state": "available", "hash": sha256_bytes(raw)}
    try:
        document = parse_markdown_document(raw.decode("utf-8"), "publication://target")
    except UnicodeError as exc:
        raise PublicationImpactError(f"Target is not UTF-8 Markdown: {path}") from exc
    # Native locators and public anchors remain separate. Resolve only unique
    # ATX anchors supported by this profile; ambiguous legacy pages use page scope.
    matches = [
        section
        for section in document.sections
        if markdown_anchor(section.title) == topic["anchor"]
    ]
    if len(matches) != 1:
        return {"state": "unresolved-anchor", "hash": None}
    return {"state": "available", "hash": matches[0].exact_hash}


def capture_publication_basis(
    consumer_root: str | Path = ".",
    *,
    config_path: str | Path = ".llm-wiki/publication.json",
    target_dir: str | Path | None = None,
    baseline: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Capture a portable input basis without extraction or remote access.

    The native wiki must be populated by its owning workflow first. A source-only
    consumer may point architecture.root at an isolated bootstrap output.
    """
    root = Path(consumer_root).absolute()
    config = load_publication_config(root, config_path=config_path)
    if baseline is not None:
        validate_publication_basis(baseline)
    old_topics, new_topics = _topic_versions(config, baseline)
    topics = {**old_topics, **new_topics}
    architecture_root = publication_path(root, config["architecture"]["root"])
    snapshot_builder = (
        build_bootstrap_publication_snapshot
        if config["architecture"]["baseline"] == "bootstrap-source"
        else build_publication_snapshot
    )
    native = snapshot_builder(architecture_root)
    files = {}
    targets = {}
    source_paths = {
        dep["source_file"]
        for topic in config["topics"]
        for dep in topic["depends_on"]
        if "source_file" in dep
    }
    source_paths.update(
        topic["source_document"]
        for topic in config["topics"]
        if topic.get("source_document")
    )
    with StorageReadSession(root).phase() as session:
        for path in sorted(source_paths):
            files[path] = _file_hash(session, root, path)
        if target_dir is not None:
            target = publication_path(root, str(target_dir))
            if not target.is_dir():
                raise PublicationImpactError(
                    "target-dir must be an existing consumer-relative directory"
                )
            with StorageReadSession(target).phase() as target_session:
                for topic in topics.values():
                    targets[topic["id"]] = _target_hash(target_session, topic)
            target_session.recheck()
    session.recheck()
    # A prose edit can occur without a manifest write. Revalidate the full
    # native snapshot after capturing external inputs, including its pages.
    if snapshot_builder(architecture_root)["snapshot_id"] != native["snapshot_id"]:
        raise PublicationImpactError("Native snapshot changed during input capture")
    if config != load_publication_config(root, config_path=config_path):
        raise PublicationImpactError("Publication configuration changed during capture")
    return _seal(
        {
            "schema_version": BASIS_SCHEMA,
            "config": config,
            "architecture": native,
            "files": files,
            "targets": targets,
        },
        "basis_id",
    )


def _dependency_basis(dep: Mapping[str, Any], basis: Mapping[str, Any]) -> Any:
    if "source_file" in dep:
        return basis["files"].get(dep["source_file"])
    page = next(
        (
            p
            for p in basis["architecture"]["pages"]
            if p["canonical_path"] == dep["architecture_page"]
        ),
        None,
    )
    if page is None:
        return None
    source_basis = page.get("source_basis")
    if dep.get("section"):
        page = next(
            (s for s in page["sections"] if s["locator"] == dep["section"]), None
        )
        if page is None:
            return None
    facets = dep.get("facets", ["whole"])
    if facets == ["whole"]:
        hashes = page.get("normalized_hash", page.get("exact_hash"))
    else:
        hashes = {facet: page.get(facet + "_hash") for facet in facets}
        if not all(hashes.values()):
            return None
    return {
        "content": hashes,
        "source_basis": source_basis,
        "generation_options": basis["architecture"]["commitments"][
            "generation_options_hash"
        ],
        "producer": basis["architecture"]["commitments"]["producer_hash"],
    }


def _topic_inputs(topic: Mapping[str, Any], basis: Mapping[str, Any]) -> dict[str, Any]:
    inputs = {
        hash_json(dep): {"dependency": dep, "hash": _dependency_basis(dep, basis)}
        for dep in topic["depends_on"]
    }
    if topic.get("source_document"):
        path = topic["source_document"]
        inputs["authored"] = {
            "dependency": {"source_file": path},
            "hash": basis["files"].get(path),
        }
    return inputs


def _finding(kind: str, subject: str, details: Mapping[str, Any]) -> dict[str, Any]:
    body = {"kind": kind, "subject": subject, **details}
    return {**body, "id": hash_json(body)}


def _topic_findings(before, after) -> list[dict[str, Any]]:
    old_topics, new_topics = _topic_versions(after["config"], before)
    findings = []
    for key in sorted(old_topics.keys() | new_topics.keys()):
        old, new = old_topics.get(key), new_topics.get(key)
        topic = new or old
        assert topic is not None
        previous = {}
        if old is not None:
            assert before is not None
            previous = _topic_inputs(old, before)
        current = {} if new is None else _topic_inputs(new, after)
        reasons = []
        if old != new:
            reasons.append({"kind": "mapping-changed" if old else "initial-review"})
        for dep_key in sorted(previous.keys() | current.keys()):
            left, right = previous.get(dep_key), current.get(dep_key)
            if left != right:
                reasons.append(
                    {"kind": "dependency-changed", "before": left, "after": right}
                )
        target = after["targets"].get(key, {"state": "not-evaluated", "hash": None})
        if target["state"] in {"missing", "unresolved-anchor"}:
            reasons.append({"kind": "target-" + target["state"]})
        if before and before["targets"].get(key) != target:
            reasons.append({"kind": "target-changed"})
        missing = [
            value["dependency"] for value in current.values() if value["hash"] is None
        ]
        if missing:
            reasons.append({"kind": "evidence-unavailable", "dependencies": missing})
        if reasons:
            findings.append(
                _finding(
                    "topic",
                    key,
                    {
                        "status": "incomplete"
                        if missing or target["state"] == "unresolved-anchor"
                        else "needs-review",
                        "owner": topic["owner"],
                        "wiki_page": topic["wiki_page"],
                        "anchor": topic.get("anchor"),
                        "edit_at": topic["edit_at"],
                        "target": target,
                        "reasons": reasons,
                        # Current commitments make a decision reopen after any covered
                        # input changes, independently of transient report/run identity.
                        "review_basis": hash_json(
                            {
                                "topic": topic,
                                "inputs": current,
                                "target": target,
                                "source_policy": after["config"]["source_policy"],
                                "destination": after["config"]["target"],
                            }
                        ),
                    },
                )
            )
    return findings


def compare_publication_impact(
    candidate: Mapping[str, Any],
    baseline: Mapping[str, Any] | None = None,
    *,
    reviews: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Compare complete bases through the union of previous/current bindings.

    The caller supplies an accepted baseline and review ledger under its own
    repository review policy. This function authenticates neither Git identities
    nor hosting permissions. All output is deterministic and has no side effects.
    """
    after = deepcopy(dict(candidate))
    before = None if baseline is None else deepcopy(dict(baseline))
    validate_publication_basis(after)
    if before is not None:
        validate_publication_basis(before)
        if before["config"]["target"] != after["config"]["target"]:
            raise PublicationImpactError(
                "Target changed; explicitly establish a new baseline"
            )
        if before["config"]["source_policy"] != after["config"]["source_policy"]:
            raise PublicationImpactError(
                "Source policy changed; explicitly establish a new baseline"
            )
    findings = _topic_findings(before, after)
    pages = {p["canonical_path"] for p in after["architecture"]["pages"]}
    mapped = {
        d["architecture_page"]
        for t in after["config"]["topics"]
        for d in t["depends_on"]
        if "architecture_page" in d
    }
    exclusions = after["config"]["exclusions"]
    excluded = {
        p for p in pages if any(fnmatchcase(p, e["pattern"]) for e in exclusions)
    }
    for path in sorted(pages - mapped - excluded):
        findings.append(
            _finding(
                "coverage",
                path,
                {
                    "status": "unmapped",
                    "reasons": [
                        {
                            "kind": "architecture-page-unmapped",
                            "action": "Map a public topic or record a scoped exclusion",
                        }
                    ],
                },
            )
        )
    decisions = validate_publication_reviews(reviews)
    for finding in findings:
        if (
            finding["kind"] != "topic"
            or finding["status"] == "incomplete"
            or finding["target"]["state"] != "available"
        ):
            continue
        if any(
            record["topic"] == finding["subject"]
            and record["review_basis"] == finding["review_basis"]
            and record["owner"] == finding["owner"]
            for record in decisions
        ):
            finding["status"] = "reviewed-current"
    complete = not any(f["status"] == "incomplete" for f in findings)
    pending = any(
        f["status"] in {"needs-review", "unmapped", "incomplete"} for f in findings
    )
    report = {
        "schema_version": IMPACT_SCHEMA,
        "complete": complete,
        "review_required": pending,
        "changed": before is None or before["basis_id"] != after["basis_id"],
        "ready": complete
        and not pending
        and all(
            after["targets"].get(t["id"], {}).get("state") == "available"
            for t in after["config"]["topics"]
        ),
        "config_hash": hash_json(after["config"]),
        "enforcement": after["config"]["enforcement"],
        "basis": {
            "baseline": None if before is None else before["basis_id"],
            "candidate": after["basis_id"],
        },
        "coverage": {
            "total": len(pages),
            "mapped": len(pages & mapped),
            "excluded": len(excluded - mapped),
            "unmapped": len(pages - mapped - excluded),
        },
        "findings": findings,
        "limitations": [
            "Native source freshness is snapshot-only; run the owning native integrity workflow.",
            "Target anchors use unique ATX headings; map legacy pages as whole pages.",
            "Review ledger acceptance is controlled by the calling repository.",
        ],
    }
    return _seal(report, "report_id")


def resolve_publication_finding(
    report: Mapping[str, Any],
    candidate: Mapping[str, Any],
    *,
    finding_id: str,
    reviewer: str,
    reason: str,
    reviews: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Prepare an exact-basis no-edit decision for normal repository review."""
    validate_publication_report(report)
    validate_publication_basis(candidate)
    if report["basis"]["candidate"] != candidate["basis_id"]:
        raise PublicationImpactError(
            "Impact report is stale; rerun against current inputs"
        )
    finding = next((f for f in report["findings"] if f["id"] == finding_id), None)
    if (
        finding is None
        or finding["kind"] != "topic"
        or finding["status"] == "incomplete"
    ):
        raise PublicationImpactError("Only a complete topic finding can be reviewed")
    if finding["target"]["state"] != "available":
        raise PublicationImpactError(
            "Review requires the exact available target page/section"
        )
    if any(
        r["kind"] in {"target-missing", "evidence-unavailable"}
        for r in finding["reasons"]
    ):
        raise PublicationImpactError(
            "Missing evidence or target cannot be accepted as still current"
        )
    if not reviewer.strip() or not reason.strip():
        raise PublicationImpactError("Reviewer and rationale are required")
    records = deepcopy(validate_publication_reviews(reviews))
    record = {
        "topic": finding["subject"],
        "owner": finding["owner"],
        "reviewer": reviewer,
        "reason": reason,
        "decision": "still-current",
        "review_basis": finding["review_basis"],
    }
    records = [
        r
        for r in records
        if not (
            r["topic"] == record["topic"]
            and r["review_basis"] == record["review_basis"]
        )
    ]
    records.append(record)
    return {
        "schema_version": REVIEWS_SCHEMA,
        "records": sorted(records, key=lambda r: (r["topic"], r["review_basis"])),
    }


def render_publication_impact(report: Mapping[str, Any]) -> str:
    """Render inert Markdown for CI summaries, including unresolved coverage."""

    def safe(value):
        return (
            str(value)
            .replace("|", "\\|")
            .replace("\n", " ")
            .replace("\r", " ")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
        )

    counts = Counter(f["status"] for f in report["findings"])
    lines = [
        "# Sibling wiki impact",
        "",
        f"Complete: {str(report['complete']).lower()}",
        f"Review required: {str(report['review_required']).lower()}",
        "",
        "| Status | Topic or architecture page | Public target | Reasons |",
        "| --- | --- | --- | --- |",
    ]
    for finding in report["findings"]:
        target = finding.get("wiki_page", "") + (
            "#" + finding["anchor"] if finding.get("anchor") else ""
        )
        reasons = ", ".join(r["kind"] for r in finding["reasons"])
        lines.append(
            "| "
            + " | ".join(
                safe(v)
                for v in (finding["status"], finding["subject"], target, reasons)
            )
            + " |"
        )
    lines.extend(["", "Findings: " + safe(dict(sorted(counts.items()))), ""])
    lines.extend("- " + safe(value) for value in report["limitations"])
    return "\n".join(lines) + "\n"
