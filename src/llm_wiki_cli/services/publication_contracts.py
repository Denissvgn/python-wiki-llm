"""Strict portable validators for captured publication evidence and decisions."""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping
from copy import deepcopy
import math
import re
from typing import Any, NoReturn

from .concept_identity import validate_concept_uid
from .knowledge_evidence import hash_json
from .markdown_sections import SECTION_ORDER_DOMAIN, section_locator
from .publication_config import (
    PUBLICATION_CONFIG_SCHEMA_VERSION,
    validate_publication_config,
)
from .sync_manifest import ManifestPageSource
from .validation import (
    portable_path_key,
    require_repository_relative_path,
    require_sha256,
)
from .wiki_surface import PageKind, canonical_path, iter_page_kinds, mcp_uri


_MAX_ITEMS = 65_536
_MAX_REFERENCES = 128
_MAX_JSON_NODES = 5_000_000
_BASIS_SCHEMA = "llm-wiki-publication-basis/v1"
_SNAPSHOT_SCHEMA = "llm-wiki-publication-snapshot/v1"
_REPORT_SCHEMA = "llm-wiki-publication-impact/v1"
_REVIEWS_SCHEMA = "llm-wiki-publication-reviews/v1"
_TOPIC_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}\Z")


class PublicationProtocolError(ValueError):
    """An imported publication document violates its versioned contract."""


def _fail(field: str, message: str) -> NoReturn:
    raise PublicationProtocolError(f"{field}: {message}")


def _record(
    value: object, field: str, required: set[str], optional: set[str] | None = None
) -> Mapping[str, Any]:
    if not isinstance(value, Mapping) or any(type(key) is not str for key in value):
        _fail(field, "must be an object with string keys")
    if set(value) - required - (optional or set()) or required - set(value):
        _fail(field, "has missing or unknown fields")
    return value


def _array(value: object, field: str, maximum: int = _MAX_ITEMS) -> list[Any]:
    if type(value) is not list or len(value) > maximum:
        _fail(field, f"must be an array of at most {maximum} entries")
    return value


def _text(
    value: object, field: str, *, empty: bool = False, maximum: int = 4096
) -> str:
    if type(value) is not str or (not empty and not value.strip()):
        _fail(field, "must be text" if empty else "must be nonempty text")
    if len(value.encode("utf-8")) > maximum or "\x00" in value:
        _fail(field, "exceeds the text limit or contains a NUL")
    return value


def _integer(
    value: object, field: str, minimum: int = 0, maximum: int = 2**63 - 1
) -> int:
    if type(value) is not int or not minimum <= value <= maximum:
        _fail(field, "must be an integer in the permitted range")
    return value


def _hash(value: object, field: str, *, nullable: bool = False) -> None:
    if value is None and nullable:
        return
    require_sha256(
        value,
        digest_error=PublicationProtocolError(
            f"{field}: must be a canonical SHA-256 commitment"
        ),
    )


def _path(value: object, field: str) -> str:
    error = PublicationProtocolError(
        f"{field}: must be a canonical portable relative path"
    )
    return require_repository_relative_path(
        value,
        text_error=error,
        posix_error=error,
        normalized_error=error,
        absolute_error=error,
        separator_error=error,
        control_error=error,
        portability_error=error,
        reject_delete_character=True,
        leading_backslash_is_absolute=True,
    )


def _topic_id(value: object, field: str) -> str:
    text = _text(value, field, maximum=128)
    if not _TOPIC_ID.fullmatch(text):
        _fail(field, "must be a portable topic identifier")
    return text


def _path_spelling(
    path: str, field: str, seen: dict[tuple[str, ...], tuple[str, ...]]
) -> None:
    parts = path.split("/")
    for length in range(1, len(parts) + 1):
        exact = tuple(parts[:length])
        key = tuple(portable_path_key(part) for part in exact)
        previous = seen.setdefault(key, exact)
        if previous != exact:
            _fail(
                field,
                "contains inconsistent path spelling across supported filesystems",
            )


def _json_tree(value: object) -> None:
    pending = [(value, 0)]
    count = 0
    while pending:
        item, depth = pending.pop()
        count += 1
        if depth > 64 or count > _MAX_JSON_NODES:
            _fail("document", "exceeds JSON structural bounds")
        if isinstance(item, Mapping):
            if any(type(key) is not str for key in item):
                _fail("document", "object keys must be strings")
            pending.extend((child, depth + 1) for child in item.values())
        elif type(item) is list:
            pending.extend((child, depth + 1) for child in item)
        elif type(item) is float:
            if not math.isfinite(item):
                _fail("document", "contains a non-finite number")
        elif item is not None and type(item) not in {str, int, bool}:
            _fail("document", "contains a non-JSON value")


def _seal(value: Mapping[str, Any], schema: str, key: str) -> None:
    if value.get("schema_version") != schema:
        _fail("schema_version", f"must be {schema}")
    _hash(value.get(key), key)
    if value[key] != hash_json(
        {name: item for name, item in value.items() if name != key}
    ):
        _fail(key, "does not commit the supplied document")


def _source_basis(value: object, field: str) -> None:
    if value is None:
        return
    data = _record(
        value,
        field,
        {
            "scope",
            "source_path",
            "extractor_ref",
            "source_content_hash",
            "concept_observation_hash",
            "aggregate_input_hash",
            "extensions",
        },
    )
    if data["scope"] not in {
        "unknown",
        "module",
        "entity",
        "infrastructure",
        "aggregate",
    }:
        _fail(field, "has an unknown source scope")
    if data["source_path"] is not None:
        _path(data["source_path"], field + ".source_path")
    if data["extractor_ref"] is not None:
        _text(data["extractor_ref"], field + ".extractor_ref")
    for key in (
        "source_content_hash",
        "concept_observation_hash",
        "aggregate_input_hash",
    ):
        _hash(data[key], field + "." + key, nullable=True)
    if not isinstance(data["extensions"], Mapping):
        _fail(field + ".extensions", "must be an object")


def _owned_hashes(data: Mapping[str, Any], field: str) -> None:
    _hash(data["exact_hash"], field + ".exact_hash")
    ownership = data["ownership"]
    if ownership not in {"generated", "semantic", "mixed", "unknown"}:
        _fail(field + ".ownership", "has an unknown ownership state")
    for facet in ("structural_hash", "semantic_hash"):
        if facet in data:
            _hash(data[facet], field + "." + facet)
    expected_facets = {
        "generated": {"structural_hash"},
        "semantic": {"semantic_hash"},
        "mixed": {"structural_hash", "semantic_hash"},
        "unknown": set(),
    }[ownership]
    if ({"structural_hash", "semantic_hash"} & set(data)) != expected_facets:
        _fail(field, "facet commitments do not match declared section ownership")
    if ownership in {"generated", "semantic"} and any(
        data[key] != data["exact_hash"] for key in expected_facets
    ):
        _fail(
            field, "single-owner facet commitment does not match exact section content"
        )


def _preamble(value: object, page: Mapping[str, Any], field: str) -> None:
    data = _record(
        value,
        field,
        {"locator", "page_locator", "exact_hash", "ownership"},
        {"structural_hash", "semantic_hash"},
    )
    if (
        data["page_locator"] != page["locator"]
        or data["locator"] != page["locator"] + "#section/@preamble"
    ):
        _fail(field, "must identify its containing page's native preamble")
    _owned_hashes(data, field)


def _sections(value: object, page: Mapping[str, Any], field: str) -> None:
    sections = _array(value, field)
    seen: dict[str, Mapping[str, Any]] = {}
    counts: Counter[tuple[str | None, str]] = Counter()
    children: dict[str, list[str]] = {}
    last_start = -1
    for index, raw in enumerate(sections):
        at = f"{field}[{index}]"
        data = _record(
            raw,
            at,
            {
                "locator",
                "page_locator",
                "ordinal",
                "level",
                "title",
                "heading_path",
                "occurrence_path",
                "sibling_occurrence",
                "parent_locator",
                "child_locators",
                "start",
                "body_start",
                "end",
                "exact_hash",
                "ownership",
            },
            {"structural_hash", "semantic_hash"},
        )
        if data["page_locator"] != page["locator"]:
            _fail(at, "section page does not match its containing page")
        title = _text(data["title"], at + ".title", empty=True)
        headings = [
            _text(item, at + ".heading_path", empty=True)
            for item in _array(data["heading_path"], at, 6)
        ]
        occurrences = [
            _integer(item, at + ".occurrence_path", 1)
            for item in _array(data["occurrence_path"], at, 6)
        ]
        if not headings or len(headings) != len(occurrences) or headings[-1] != title:
            _fail(at, "heading and occurrence paths must be matching nonempty paths")
        locator = section_locator(page["locator"], headings, occurrences)
        if (
            data["locator"] != locator
            or locator in seen
            or data["ordinal"] != index
            or type(data["ordinal"]) is not int
        ):
            _fail(at, "has a duplicate or inconsistent native section coordinate")
        parent = (
            None
            if len(headings) == 1
            else section_locator(page["locator"], headings[:-1], occurrences[:-1])
        )
        if data["parent_locator"] != parent or (
            parent is not None and parent not in seen
        ):
            _fail(at, "has an invalid section parent")
        counts[(parent, title)] += 1
        if (
            type(data["sibling_occurrence"]) is not int
            or occurrences[-1] != counts[(parent, title)]
            or data["sibling_occurrence"] != occurrences[-1]
        ):
            _fail(at, "has an inconsistent sibling occurrence")
        level = _integer(data["level"], at + ".level", 1, 6)
        if len(headings) > level or (
            parent is not None and seen[parent]["level"] >= level
        ):
            _fail(at, "has an inconsistent heading level")
        start = _integer(data["start"], at + ".start")
        body_start = _integer(data["body_start"], at + ".body_start", start)
        end = _integer(data["end"], at + ".end", body_start)
        if start <= last_start or (parent is not None and end > seen[parent]["end"]):
            _fail(at, "has inconsistent section extents")
        last_start = start
        _owned_hashes(data, at)
        for child in _array(data["child_locators"], at + ".child_locators"):
            _text(child, at + ".child_locators")
        if parent is not None:
            children.setdefault(parent, []).append(locator)
        seen[locator] = data
    for locator, data in seen.items():
        if data["child_locators"] != children.get(locator, []):
            _fail(
                field, "child coordinates do not match the complete section hierarchy"
            )
    order = {
        "domain": SECTION_ORDER_DOMAIN,
        "page_locator": page["locator"],
        "sections": [
            {
                key: item[key]
                for key in ("locator", "ordinal", "parent_locator", "child_locators")
            }
            for item in sections
        ],
    }
    if page["section_ordering_hash"] != hash_json(order):
        _fail(field, "section ordering commitment does not match")


def _snapshot(value: object) -> None:
    data = _record(
        value,
        "architecture",
        {
            "schema_version",
            "complete",
            "coverage",
            "freshness",
            "commitments",
            "pages",
            "snapshot_id",
        },
    )
    _seal(data, _SNAPSHOT_SCHEMA, "snapshot_id")
    if data["complete"] is not True:
        _fail("architecture.complete", "requires a complete native snapshot")
    coverage = _record(
        data["coverage"],
        "architecture.coverage",
        {"scope", "page_count", "section_model", "source_mapping"},
    )
    if (
        coverage["scope"] != "canonical-native-pages"
        or coverage["section_model"] != "native-atx/v1"
        or coverage["source_mapping"] != "non-exhaustive"
    ):
        _fail("architecture.coverage", "has unsupported scope qualifications")
    if data["freshness"] != {"scope": "snapshot-only", "state": "not-evaluated"}:
        _fail("architecture.freshness", "must retain snapshot-only qualification")
    commitments = _record(
        data["commitments"],
        "architecture.commitments",
        {
            "source_snapshot_hash",
            "markdown_snapshot_hash",
            "generation_options_hash",
            "producer_hash",
            "surface_index_hash",
            "knowledge_index_hash",
            "evaluated_envelope_hash",
            "governance_hash",
            "manifest_hash",
            "manifest_storage_version",
        },
    )
    for key, item in commitments.items():
        if key != "manifest_storage_version":
            _hash(
                item,
                "architecture.commitments." + key,
                nullable=key in {"evaluated_envelope_hash", "governance_hash"},
            )
    _integer(
        commitments["manifest_storage_version"],
        "architecture.commitments.manifest_storage_version",
        1,
        8,
    )
    pages = _array(data["pages"], "architecture.pages")
    if type(coverage["page_count"]) is not int or coverage["page_count"] != len(pages):
        _fail(
            "architecture.coverage.page_count", "does not match complete page inventory"
        )
    paths: set[str] = set()
    uids: set[str] = set()
    kinds = {entry.kind.value: entry for entry in iter_page_kinds()}
    for index, raw in enumerate(pages):
        field = f"architecture.pages[{index}]"
        page = _record(
            raw,
            field,
            {
                "canonical_path",
                "kind",
                "id",
                "locator",
                "mcp_uri",
                "uid",
                "role",
                "raw_hash",
                "normalized_hash",
                "source_basis",
                "source_mapping",
                "section_ordering_hash",
                "sections",
            },
            {"preamble"},
        )
        kind = PageKind(page["kind"])
        entry = kinds[kind.value]
        coordinate_id = page["id"] if entry.requires_page_id else None
        if not entry.requires_page_id and page["id"] != kind.value:
            _fail(field + ".id", "singleton page identity must match its page kind")
        path = _path(page["canonical_path"], field + ".canonical_path")
        if (
            path != canonical_path(kind, coordinate_id)
            or portable_path_key(path) in paths
        ):
            _fail(
                field, "has a duplicate, colliding or inconsistent canonical page path"
            )
        paths.add(portable_path_key(path))
        if (
            page["locator"] != mcp_uri(kind, coordinate_id)
            or page["mcp_uri"] != page["locator"]
            or page["role"] != entry.role.value
        ):
            _fail(field, "page kind, role and native coordinates disagree")
        if page["uid"] is not None:
            uid = validate_concept_uid(page["uid"])
            if uid in uids:
                _fail(field + ".uid", "duplicates a native identity")
            uids.add(uid)
        for key in ("raw_hash", "normalized_hash", "section_ordering_hash"):
            _hash(page[key], field + "." + key)
        _source_basis(page["source_basis"], field + ".source_basis")
        if page["source_mapping"] is not None:
            mapping = ManifestPageSource.from_payload(
                page["source_mapping"], field + ".source_mapping"
            )
            if mapping.to_payload() != page["source_mapping"]:
                _fail(
                    field + ".source_mapping", "must have a canonical source coordinate"
                )
            _path(mapping.source_path, field + ".source_mapping.source_path")
        _sections(page["sections"], page, field + ".sections")
        if "preamble" in page:
            _preamble(page["preamble"], page, field + ".preamble")


def _target(value: object, field: str, *, unevaluated: bool = False) -> None:
    data = _record(value, field, {"state", "hash"})
    states = {"available", "missing", "unresolved-anchor"} | (
        {"not-evaluated"} if unevaluated else set()
    )
    if type(data["state"]) is not str or data["state"] not in states:
        _fail(field + ".state", "has an invalid target state")
    if data["state"] == "available":
        _hash(data["hash"], field + ".hash")
    elif data["state"] == "unresolved-anchor":
        _hash(data["hash"], field + ".hash", nullable=True)
    elif data["hash"] is not None:
        _fail(field + ".hash", "must be null for unavailable target content")


def _provider_configuration(
    value: object, provider: str, field: str
) -> Mapping[str, Any]:
    config = {
        "schema_version": PUBLICATION_CONFIG_SCHEMA_VERSION,
        "architecture": {"baseline": "existing-wiki", "root": "."},
        "target": {"kind": "github-wiki", "repository": "self"},
        "enforcement": "advisory",
        "publish": False,
        "topics": [],
        "reference_providers": {provider: value},
    }
    normalized = validate_publication_config(config, consumer_root=None)[
        "reference_providers"
    ][provider]
    if normalized != value:
        _fail(field, "must be normalized provider configuration")
    return normalized


def _references(value: object, config: Mapping[str, Any]) -> None:
    references = _record(
        value, "references", set(), set(value) if isinstance(value, Mapping) else set()
    )
    if len(references) > _MAX_REFERENCES:
        _fail("references", "exceeds reference input bounds")
    for identity, raw in references.items():
        field = "references." + identity
        _hash(identity, field)
        reference = _record(raw, field, {"provider", "configuration", "contract"})
        provider = _topic_id(reference["provider"], field + ".provider")
        configuration = _provider_configuration(
            reference["configuration"], provider, field + ".configuration"
        )
        if identity != hash_json(
            {"provider": provider, "configuration": configuration}
        ):
            _fail(
                field,
                "reference identity does not match its provider and configuration",
            )
        if reference["contract"] is None:
            if configuration["kind"] != "contract-file":
                _fail(
                    field + ".contract",
                    "only a contract-file provider may record known missing input",
                )
        else:
            from .cli_reference import validate_cli_contract

            validate_cli_contract(reference["contract"])
            if configuration["kind"] == "llm-wiki-cli" and (
                reference["contract"]["program"] != "llm-wiki"
                or reference["contract"]["package"]["name"] != "agent-wiki-cli"
            ):
                _fail(
                    field + ".contract",
                    "built-in provider identity must be agent-wiki-cli/llm-wiki",
                )
    for provider, configuration in config.get("reference_providers", {}).items():
        identity = hash_json({"provider": provider, "configuration": configuration})
        if identity not in references:
            _fail(
                "references",
                "requires a captured record for every declared current provider",
            )


def _basis(value: object) -> None:
    data = _record(
        value,
        "basis",
        {"schema_version", "config", "architecture", "files", "targets", "basis_id"},
        {"references"},
    )
    _seal(data, _BASIS_SCHEMA, "basis_id")
    if (
        validate_publication_config(data["config"], consumer_root=None)
        != data["config"]
    ):
        _fail("config", "must be normalized publication policy")
    _snapshot(data["architecture"])
    files = _record(
        data["files"],
        "files",
        set(),
        set(data["files"]) if isinstance(data["files"], Mapping) else set(),
    )
    targets = _record(
        data["targets"],
        "targets",
        set(),
        set(data["targets"]) if isinstance(data["targets"], Mapping) else set(),
    )
    if len(files) > _MAX_ITEMS or len(targets) > _MAX_ITEMS:
        _fail("basis", "exceeds external input bounds")
    spellings: dict[tuple[str, ...], tuple[str, ...]] = {}
    for path, commitment in files.items():
        _path(path, "files.path")
        _path_spelling(path, "files", spellings)
        _hash(commitment, "files." + path, nullable=True)
    for asset in data["config"].get("content", {}).get("assets", []):
        if asset["source_document"] not in files:
            _fail(
                "files", "requires a captured record for every declared current asset"
            )
    for topic, observation in targets.items():
        _topic_id(topic, "targets.topic")
        _target(observation, "targets." + topic)
    _references(data.get("references", {}), data["config"])


def _reviews(value: object) -> list[dict[str, Any]]:
    if value is None:
        return []
    data = _record(value, "reviews", {"schema_version", "records"})
    if data["schema_version"] != _REVIEWS_SCHEMA:
        _fail("reviews.schema_version", f"must be {_REVIEWS_SCHEMA}")
    records = _array(data["records"], "reviews.records")
    seen = set()
    for index, raw in enumerate(records):
        field = f"reviews.records[{index}]"
        record = _record(
            raw,
            field,
            {"topic", "owner", "reviewer", "reason", "decision", "review_basis"},
        )
        if record["decision"] not in {"still-current", "retired"}:
            _fail(field + ".decision", "must be still-current or retired")
        for key in ("topic", "owner", "reviewer", "reason"):
            _text(record[key], field + "." + key)
        _topic_id(record["topic"], field + ".topic")
        _hash(record["review_basis"], field + ".review_basis")
        key = (record["topic"], record["review_basis"])
        if key in seen:
            _fail(field, "duplicates a topic review for the same basis")
        seen.add(key)
    return deepcopy(records)


def _dependency(value: object, field: str) -> Mapping[str, Any]:
    config = {
        "schema_version": PUBLICATION_CONFIG_SCHEMA_VERSION,
        "architecture": {"baseline": "existing-wiki", "root": "wiki"},
        "target": {"kind": "github-wiki", "repository": "self"},
        "enforcement": "advisory",
        "publish": False,
        "topics": [
            {
                "id": "dependency",
                "owner": "reviewer",
                "wiki_page": "Page.md",
                "edit_at": "wiki",
                "depends_on": [value],
            }
        ],
    }
    if isinstance(value, Mapping) and "reference" in value:
        provider = _topic_id(value["reference"], field + ".reference")
        config["reference_providers"] = {provider: {"kind": "llm-wiki-cli"}}
    dependency = validate_publication_config(config, consumer_root=None)["topics"][0][
        "depends_on"
    ][0]
    if dependency != value:
        _fail(field, "dependency must have normalized fields")
    return dependency


def _input(value: object, field: str) -> None:
    if value is None:
        return
    data = _record(value, field, {"dependency", "hash"})
    dependency = _dependency(data["dependency"], field + ".dependency")
    if "source_file" in dependency or data["hash"] is None:
        _hash(data["hash"], field + ".hash", nullable=True)
        return
    if "reference" in dependency:
        evidence = _record(data["hash"], field + ".hash", {"provider", "contract"})
        _provider_configuration(
            evidence["provider"], dependency["reference"], field + ".hash.provider"
        )
        _hash(evidence["contract"], field + ".hash.contract")
        return
    evidence = _record(
        data["hash"],
        field + ".hash",
        {"content", "source_basis", "generation_options", "producer"},
    )
    facets = dependency.get("facets", ["whole"])
    if facets == ["whole"]:
        _hash(evidence["content"], field + ".hash.content")
    else:
        content = _record(evidence["content"], field + ".hash.content", set(facets))
        for facet in facets:
            _hash(content[facet], field + ".hash.content." + facet)
    _source_basis(evidence["source_basis"], field + ".hash.source_basis")
    _hash(evidence["generation_options"], field + ".hash.generation_options")
    _hash(evidence["producer"], field + ".hash.producer")


def _reasons(value: object, field: str, *, coverage: bool) -> None:
    reasons = _array(value, field)
    if not reasons:
        _fail(field, "must identify at least one reason")
    for reason in reasons:
        data = _record(
            reason, field, {"kind"}, {"before", "after", "dependencies", "action"}
        )
        kind = data["kind"]
        if coverage:
            _record(data, field, {"kind", "action"})
            if kind != "architecture-page-unmapped":
                _fail(field, "coverage finding has an invalid reason")
            _text(data["action"], field + ".action")
        elif kind == "dependency-changed":
            _record(data, field, {"kind", "before", "after"})
            _input(data["before"], field + ".before")
            _input(data["after"], field + ".after")
        elif kind == "evidence-unavailable":
            _record(data, field, {"kind", "dependencies"})
            for dependency in _array(data["dependencies"], field + ".dependencies"):
                _dependency(dependency, field + ".dependencies")
        elif kind in {
            "initial-review",
            "mapping-changed",
            "mapping-retired",
            "target-missing",
            "target-unresolved-anchor",
            "target-changed",
        }:
            _record(data, field, {"kind"})
        else:
            _fail(field, "has an unknown topic reason")


def _report(value: object) -> None:
    data = _record(
        value,
        "report",
        {
            "schema_version",
            "complete",
            "review_required",
            "changed",
            "ready",
            "config_hash",
            "enforcement",
            "basis",
            "coverage",
            "findings",
            "limitations",
            "report_id",
        },
    )
    _seal(data, _REPORT_SCHEMA, "report_id")
    for key in ("complete", "review_required", "changed", "ready"):
        if type(data[key]) is not bool:
            _fail(key, "must be a Boolean")
    _hash(data["config_hash"], "config_hash")
    if data["enforcement"] not in {"advisory", "required"}:
        _fail("enforcement", "has an unknown policy")
    basis = _record(data["basis"], "basis", {"baseline", "candidate"})
    _hash(basis["baseline"], "basis.baseline", nullable=True)
    _hash(basis["candidate"], "basis.candidate")
    coverage = _record(
        data["coverage"], "coverage", {"total", "mapped", "excluded", "unmapped"}
    )
    for key, count in coverage.items():
        _integer(count, "coverage." + key, maximum=_MAX_ITEMS)
    if coverage["total"] != sum(
        coverage[key] for key in ("mapped", "excluded", "unmapped")
    ):
        _fail("coverage", "counts do not partition the page inventory")
    seen = set()
    findings = _array(data["findings"], "findings", 2 * _MAX_ITEMS)
    for index, raw in enumerate(findings):
        field = f"findings[{index}]"
        finding = _record(
            raw,
            field,
            {"kind", "subject", "status", "reasons", "id"},
            {"owner", "wiki_page", "anchor", "edit_at", "target", "review_basis"},
        )
        _hash(finding["id"], field + ".id")
        identity = (finding["kind"], finding["subject"])
        if identity in seen:
            _fail(field, "duplicates a finding subject")
        seen.add(identity)
        canonical = {key: item for key, item in finding.items() if key != "id"}
        if finding["status"] in {"reviewed-current", "reviewed-retired"}:
            canonical["status"] = "needs-review"
        if finding["id"] != hash_json(canonical):
            _fail(field + ".id", "does not match the finding commitment")
        if finding["kind"] == "coverage":
            _record(finding, field, {"kind", "subject", "status", "reasons", "id"})
            _path(finding["subject"], field + ".subject")
            if finding["status"] != "unmapped":
                _fail(field + ".status", "coverage findings must be unmapped")
            _reasons(finding["reasons"], field + ".reasons", coverage=True)
        elif finding["kind"] == "topic":
            _record(
                finding,
                field,
                {
                    "kind",
                    "subject",
                    "status",
                    "reasons",
                    "id",
                    "owner",
                    "wiki_page",
                    "anchor",
                    "edit_at",
                    "target",
                    "review_basis",
                },
            )
            _topic_id(finding["subject"], field + ".subject")
            _text(finding["owner"], field + ".owner", maximum=256)
            page = _path(finding["wiki_page"], field + ".wiki_page")
            if "/" in page or not page.endswith(".md"):
                _fail(field + ".wiki_page", "must be a flat Markdown target")
            if finding["anchor"] is not None:
                _text(finding["anchor"], field + ".anchor", maximum=256)
            if finding["edit_at"] not in {"wiki", "repository"} or finding[
                "status"
            ] not in {
                "incomplete",
                "needs-review",
                "reviewed-current",
                "reviewed-retired",
            }:
                _fail(field, "has an unknown topic ownership or status")
            _hash(finding["review_basis"], field + ".review_basis")
            _target(finding["target"], field + ".target", unevaluated=True)
            _reasons(finding["reasons"], field + ".reasons", coverage=False)
            retirement = any(
                reason["kind"] == "mapping-retired" for reason in finding["reasons"]
            )
            if finding["status"] == "reviewed-current" and (
                retirement or finding["target"]["state"] != "available"
            ):
                _fail(
                    field,
                    "current decisions require an active mapping and available target",
                )
            if finding["status"] == "reviewed-retired" and (
                not retirement
                or finding["target"]["state"]
                not in {"available", "missing", "unresolved-anchor"}
                or (
                    finding["target"]["state"] == "unresolved-anchor"
                    and finding["target"]["hash"] is None
                )
            ):
                _fail(
                    field,
                    "retired decisions require a retired mapping and an observed target",
                )
            if finding["status"] == "reviewed-current" and any(
                reason["kind"] == "evidence-unavailable"
                for reason in finding["reasons"]
            ):
                _fail(
                    field, "unavailable current evidence cannot be reviewed as complete"
                )
        else:
            _fail(field + ".kind", "has an unknown finding kind")
    complete = not any(item["status"] == "incomplete" for item in findings)
    pending = any(
        item["status"] in {"needs-review", "incomplete", "unmapped"}
        for item in findings
    )
    if (
        data["complete"] != complete
        or data["review_required"] != pending
        or (data["ready"] and (not complete or pending))
    ):
        _fail("report", "readiness flags contradict its findings")
    if sum(item["kind"] == "coverage" for item in findings) != coverage["unmapped"]:
        _fail("coverage.unmapped", "does not match coverage findings")
    for limitation in _array(data["limitations"], "limitations", 128):
        _text(limitation, "limitations")


def _guard(callback, value: object):
    try:
        _json_tree(value)
        return callback(value)
    except PublicationProtocolError:
        raise
    except (KeyError, TypeError, ValueError, UnicodeError, RecursionError) as exc:
        raise PublicationProtocolError("Invalid portable publication document") from exc


def validate_publication_basis(value: object) -> None:
    """Require a sealed complete basis with valid portable nested commitments."""
    _guard(_basis, value)


def validate_publication_reviews(value: object) -> list[dict[str, Any]]:
    """Return detached explicit decisions, rejecting duplicates and unknown fields."""
    return _guard(_reviews, value)


def validate_publication_report(value: object) -> None:
    """Require a sealed impact report suitable for selecting an exact finding."""
    _guard(_report, value)
