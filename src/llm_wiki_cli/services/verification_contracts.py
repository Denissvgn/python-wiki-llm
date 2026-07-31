"""Pure, application-owned machine-verification contracts.

Verification is deliberately separate from semantic authorship and human
review.  Checkers consume only an already validated :class:`KnowledgeIndex`
and explicit, pre-evaluated anchors supplied by the caller.  They never read
files, discover source, load plugins, import document-selected code, or invoke
helpers, subprocesses, networks, containers, or language models.

The only filesystem operations in this module are the fixed-name receipt
loader and atomic writer.  Loading a receipt validates recorded evidence but
never executes a checker.  Receipt validity is evaluated against live anchors;
it is not stored as a timeless boolean.
"""

from __future__ import annotations

import json
import os
import re
import stat
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from types import MappingProxyType

from .contracts import VERIFICATION_RECEIPT_SCHEMA_VERSION
from .io import first_unsafe_path_component, write_bytes_atomic
from .knowledge_evidence import (
    formatted_json_bytes,
    hash_json,
)
from .knowledge_model import (
    KnowledgeIndex,
    RelationshipKind,
    Resolution,
    TargetClass,
    knowledge_index_to_payload,
    parse_knowledge_index,
)
from .validation import (
    require_exact_fields as require_shared_exact_fields,
    require_bounded_text,
    require_list,
    require_mapping,
    require_nonnegative_int,
    require_sha256,
    require_string,
)

VERIFICATION_RECEIPT_FILENAME = ".llm-wiki-verification.json"

ARTIFACT_INTEGRITY_CHECKER_ID = "artifact-integrity"
INTERNAL_LINKS_CHECKER_ID = "internal-links"

MAX_CHECKS_PER_RECEIPT = 32
MAX_DIAGNOSTICS_PER_CHECK = 50
MAX_INPUT_DIAGNOSTICS = 10_000
MAX_DIAGNOSTIC_SUBJECT_LENGTH = 320
MAX_ANCHORS = 512
MAX_RECEIPT_BYTES = 1024 * 1024

_CHECKER_ID_RE = re.compile(r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$")
_CHECKER_VERSION_RE = re.compile(r"^[0-9]+(?:\.[0-9]+)*$")
_MACHINE_CODE_RE = re.compile(r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$")
_ANCHOR_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/-]{0,255}$")
_SCOPE_UID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._~:@/-]{0,255}$")
_WINDOWS_ABSOLUTE_RE = re.compile(r"^[A-Za-z]:[/\\]")
_DIAGNOSTIC_SUBJECT_RE = re.compile(
    rf"^[A-Za-z0-9][A-Za-z0-9._~:/?#@%+=-]"
    rf"{{0,{MAX_DIAGNOSTIC_SUBJECT_LENGTH - 1}}}$"
)


class VerificationContractError(ValueError):
    """Base error for verification inputs, checkers, and receipts."""


class UnknownVerificationCheckerError(VerificationContractError):
    """Raised before execution when a requested checker is not registered."""

    def __init__(self, checker_id: object):
        self.checker_id = checker_id
        super().__init__(f"unknown verification checker: {checker_id!r}")


class VerificationReceiptError(VerificationContractError):
    """Field-specific failure for a verification receipt."""

    def __init__(self, field: str, message: str):
        self.field = field
        self.message = message
        super().__init__(f"{field}: {message}")


class VerificationResult(str, Enum):
    """A recorded checker result at one evaluated snapshot."""

    PASSED = "passed"
    FAILED = "failed"


class VerificationInvalidationReason(str, Enum):
    """Reasons a syntactically valid receipt is not current."""

    KNOWLEDGE_CHANGED = "knowledge-changed"
    SCOPE_CHANGED = "scope-changed"
    EVIDENCE_CHANGED = "evidence-changed"
    SNAPSHOT_CHANGED = "snapshot-changed"
    UNKNOWN_CHECKER = "unknown-checker"
    CHECKER_VERSION_CHANGED = "checker-version-changed"


@dataclass(frozen=True)
class VerificationDiagnostic:
    """One bounded, path-safe machine diagnostic.

    Diagnostics intentionally carry no free-form message or source snippet.
    ``subject`` is an optional portable identifier such as a knowledge locator
    or artifact field.
    """

    code: str
    subject: str | None = None

    def __post_init__(self) -> None:
        _machine_code(self.code, "diagnostic.code")
        if self.subject is not None:
            _diagnostic_subject(self.subject, "diagnostic.subject")

    def to_payload(self) -> dict[str, str]:
        payload = {"code": self.code}
        if self.subject is not None:
            payload["subject"] = self.subject
        return payload


@dataclass(frozen=True)
class DiagnosticCoverage:
    """Disclosure for deterministic diagnostic truncation."""

    observed: int
    emitted: int
    omitted: int
    limit: int = MAX_DIAGNOSTICS_PER_CHECK
    truncated: bool = False

    def __post_init__(self) -> None:
        for name, value in (
            ("observed", self.observed),
            ("emitted", self.emitted),
            ("omitted", self.omitted),
            ("limit", self.limit),
        ):
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise VerificationContractError(
                    f"diagnostic coverage {name} must be a non-negative integer"
                )
        if self.limit != MAX_DIAGNOSTICS_PER_CHECK:
            raise VerificationContractError(
                "diagnostic coverage limit does not match the receipt contract"
            )
        if self.emitted > self.limit:
            raise VerificationContractError(
                "diagnostic coverage emitted exceeds its limit"
            )
        if self.observed != self.emitted + self.omitted:
            raise VerificationContractError(
                "diagnostic coverage totals are inconsistent"
            )
        if self.truncated != (self.omitted > 0):
            raise VerificationContractError(
                "diagnostic coverage truncated does not match omitted"
            )

    def to_payload(self) -> dict[str, int | bool]:
        return {
            "observed": self.observed,
            "emitted": self.emitted,
            "omitted": self.omitted,
            "limit": self.limit,
            "truncated": self.truncated,
        }


@dataclass(frozen=True)
class VerificationCheckResult:
    """Normalized output from one application-owned checker."""

    checker_id: str
    checker_version: str
    result: VerificationResult
    diagnostics: tuple[VerificationDiagnostic, ...] = ()
    diagnostic_coverage: DiagnosticCoverage = field(
        default_factory=lambda: DiagnosticCoverage(
            observed=0,
            emitted=0,
            omitted=0,
        )
    )

    def __post_init__(self) -> None:
        _checker_id(self.checker_id, "check.checker.id")
        _checker_version(self.checker_version, "check.checker.version")
        if not isinstance(self.result, VerificationResult):
            try:
                object.__setattr__(self, "result", VerificationResult(self.result))
            except (TypeError, ValueError) as exc:
                raise VerificationContractError(
                    "check result must be 'passed' or 'failed'"
                ) from exc
        diagnostics = tuple(self.diagnostics)
        if any(not isinstance(item, VerificationDiagnostic) for item in diagnostics):
            raise VerificationContractError(
                "check diagnostics must be VerificationDiagnostic values"
            )
        if len(diagnostics) > MAX_DIAGNOSTICS_PER_CHECK:
            raise VerificationContractError(
                "check diagnostics exceed the receipt limit"
            )
        object.__setattr__(self, "diagnostics", diagnostics)
        if not isinstance(self.diagnostic_coverage, DiagnosticCoverage):
            raise VerificationContractError(
                "check diagnostic_coverage must be DiagnosticCoverage"
            )
        if self.diagnostic_coverage.emitted != len(diagnostics):
            raise VerificationContractError(
                "check diagnostic coverage does not match emitted diagnostics"
            )

    def to_payload(self) -> dict[str, object]:
        return {
            "checker": {
                "id": self.checker_id,
                "version": self.checker_version,
            },
            "result": self.result.value,
            "diagnostics": [item.to_payload() for item in self.diagnostics],
            "diagnostic_coverage": self.diagnostic_coverage.to_payload(),
        }


@dataclass(frozen=True)
class VerificationContext:
    """All already evaluated inputs available to pure checkers."""

    knowledge: KnowledgeIndex
    knowledge_hash: str
    scope_uid: str
    scope_hash: str
    evidence: Mapping[str, str]
    evaluated_snapshot: Mapping[str, str]
    scope_locator: str | None = None
    artifact_integrity: bool = True
    artifact_diagnostics: tuple[VerificationDiagnostic, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.knowledge, KnowledgeIndex):
            raise VerificationContractError("knowledge must be a KnowledgeIndex")
        try:
            normalized_knowledge = parse_knowledge_index(
                knowledge_index_to_payload(self.knowledge)
            )
        except (TypeError, ValueError) as exc:
            raise VerificationContractError(
                f"knowledge is not a valid supplied index: {exc}"
            ) from exc
        object.__setattr__(self, "knowledge", normalized_knowledge)
        _sha256(self.knowledge_hash, "knowledge_hash")
        _scope_uid(self.scope_uid, "scope_uid")
        _sha256(self.scope_hash, "scope_hash")
        object.__setattr__(
            self,
            "evidence",
            _normalized_anchor_mapping(self.evidence, "evidence"),
        )
        object.__setattr__(
            self,
            "evaluated_snapshot",
            _normalized_anchor_mapping(
                self.evaluated_snapshot,
                "evaluated_snapshot",
            ),
        )
        if self.scope_locator is not None:
            _diagnostic_subject(self.scope_locator, "scope_locator")
            if not any(
                concept.locator == self.scope_locator
                for concept in normalized_knowledge.concepts
            ):
                raise VerificationContractError(
                    "scope_locator must identify a supplied knowledge concept"
                )
        if not isinstance(self.artifact_integrity, bool):
            raise VerificationContractError(
                "artifact_integrity must be a boolean"
            )
        diagnostics = tuple(self.artifact_diagnostics)
        if len(diagnostics) > MAX_INPUT_DIAGNOSTICS:
            raise VerificationContractError(
                "artifact_diagnostics exceed the supplied-input limit"
            )
        if any(not isinstance(item, VerificationDiagnostic) for item in diagnostics):
            raise VerificationContractError(
                "artifact_diagnostics must be VerificationDiagnostic values"
            )
        object.__setattr__(self, "artifact_diagnostics", diagnostics)

    @property
    def evidence_hash(self) -> str:
        return hash_json(dict(self.evidence))

    @property
    def snapshot_hash(self) -> str:
        return hash_json(dict(self.evaluated_snapshot))


def build_artifact_verification_context(
    knowledge: KnowledgeIndex,
    *,
    knowledge_hash: str,
    surface_index_hash: str,
    evaluated_envelope_hash: str,
    governance_hash: str | None = None,
    scope_locator: str | None = None,
    artifact_integrity: bool = True,
    artifact_diagnostics: Sequence[VerificationDiagnostic] = (),
) -> VerificationContext:
    """Build the canonical receipt context for one committed artifact set.

    The context is intentionally assembled only from already evaluated,
    application-owned inputs.  Bundle checks bind to the complete knowledge
    artifact.  A concept-scoped check additionally binds to the canonical
    concept record and uses its durable projected UID when governance exists.
    Locator-only projects receive an explicitly disposable locator digest
    rather than a misleading stable identifier.
    """

    if not isinstance(knowledge, KnowledgeIndex):
        raise TypeError("knowledge must be a KnowledgeIndex")
    _sha256(knowledge_hash, "knowledge_hash")
    _sha256(surface_index_hash, "surface_index_hash")
    _sha256(evaluated_envelope_hash, "evaluated_envelope_hash")
    if governance_hash is not None:
        _sha256(governance_hash, "governance_hash")

    payload = knowledge_index_to_payload(knowledge)
    governance_key = "llm-wiki/governance-v1"
    if scope_locator is None:
        projected = knowledge.extensions.get(governance_key)
        bundle_id = (
            projected.get("bundle_id")
            if isinstance(projected, Mapping)
            else None
        )
        scope_uid = (
            f"bundle:{bundle_id}"
            if isinstance(bundle_id, str)
            else "bundle:locator-only"
        )
        scope_hash = knowledge_hash
    else:
        selected = next(
            (
                concept
                for concept in knowledge.concepts
                if concept.locator == scope_locator
            ),
            None,
        )
        if selected is None:
            raise VerificationContractError(
                "scope_locator must identify a supplied knowledge concept"
            )
        concept_payload = next(
            item
            for item in payload["concepts"]
            if item["locator"] == scope_locator
        )
        summary = selected.extensions.get(governance_key)
        projected_uid = (
            summary.get("uid") if isinstance(summary, Mapping) else None
        )
        scope_uid = (
            projected_uid
            if isinstance(projected_uid, str)
            else "locator:" + hash_json(scope_locator).removeprefix("sha256:")
        )
        scope_hash = hash_json(concept_payload)

    evidence = {"surface-index": surface_index_hash}
    evaluated_snapshot = {
        "evaluated-envelope": evaluated_envelope_hash,
        "knowledge-index": knowledge_hash,
        "surface-index": surface_index_hash,
    }
    if governance_hash is not None:
        evidence["governance-input"] = governance_hash
        evaluated_snapshot["governance-input"] = governance_hash
    return VerificationContext(
        knowledge=knowledge,
        knowledge_hash=knowledge_hash,
        scope_uid=scope_uid,
        scope_hash=scope_hash,
        evidence=evidence,
        evaluated_snapshot=evaluated_snapshot,
        scope_locator=scope_locator,
        artifact_integrity=artifact_integrity,
        artifact_diagnostics=tuple(artifact_diagnostics),
    )


CheckerRunner = Callable[[VerificationContext], VerificationCheckResult]


@dataclass(frozen=True)
class CheckerContract:
    """One immutable application-owned checker registration."""

    checker_id: str
    version: str
    description: str
    _runner: CheckerRunner = field(repr=False, compare=False)

    def __post_init__(self) -> None:
        _checker_id(self.checker_id, "checker.id")
        _checker_version(self.version, "checker.version")
        _portable_text(self.description, "checker.description", maximum=160)
        if not callable(self._runner):
            raise VerificationContractError("checker runner must be callable")

    def run(self, context: VerificationContext) -> VerificationCheckResult:
        """Run this exact application-owned checker over supplied inputs."""

        if not isinstance(context, VerificationContext):
            raise TypeError("context must be a VerificationContext")
        result = self._runner(context)
        if not isinstance(result, VerificationCheckResult):
            raise VerificationContractError(
                f"checker {self.checker_id!r} returned an invalid result"
            )
        if (
            result.checker_id != self.checker_id
            or result.checker_version != self.version
        ):
            raise VerificationContractError(
                f"checker {self.checker_id!r} changed its declared identity"
            )
        return result


@dataclass(frozen=True)
class VerificationReceipt:
    """Deterministic recorded evidence from one explicit verification run."""

    knowledge_hash: str
    scope_uid: str
    scope_hash: str
    evidence: Mapping[str, str]
    evidence_hash: str
    evaluated_snapshot: Mapping[str, str]
    snapshot_hash: str
    result: VerificationResult
    checks: tuple[VerificationCheckResult, ...]
    schema_version: str = VERIFICATION_RECEIPT_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.schema_version != VERIFICATION_RECEIPT_SCHEMA_VERSION:
            raise VerificationReceiptError(
                "schema_version",
                f"must be {VERIFICATION_RECEIPT_SCHEMA_VERSION!r}",
            )
        _sha256(self.knowledge_hash, "knowledge_hash")
        _scope_uid(self.scope_uid, "scope.uid")
        _sha256(self.scope_hash, "scope.hash")
        evidence = _normalized_anchor_mapping(self.evidence, "evidence")
        snapshot = _normalized_anchor_mapping(
            self.evaluated_snapshot,
            "evaluated_snapshot",
        )
        object.__setattr__(self, "evidence", evidence)
        object.__setattr__(self, "evaluated_snapshot", snapshot)
        _sha256(self.evidence_hash, "evidence_hash")
        _sha256(self.snapshot_hash, "snapshot_hash")
        if self.evidence_hash != hash_json(dict(evidence)):
            raise VerificationReceiptError(
                "evidence_hash",
                "does not match the canonical evidence object",
            )
        if self.snapshot_hash != hash_json(dict(snapshot)):
            raise VerificationReceiptError(
                "snapshot_hash",
                "does not match the canonical evaluated snapshot",
            )
        if not isinstance(self.result, VerificationResult):
            try:
                object.__setattr__(self, "result", VerificationResult(self.result))
            except (TypeError, ValueError) as exc:
                raise VerificationReceiptError(
                    "result",
                    "must be 'passed' or 'failed'",
                ) from exc
        checks = tuple(self.checks)
        if not checks:
            raise VerificationReceiptError("checks", "must not be empty")
        if len(checks) > MAX_CHECKS_PER_RECEIPT:
            raise VerificationReceiptError("checks", "contains too many checkers")
        if any(not isinstance(item, VerificationCheckResult) for item in checks):
            raise VerificationReceiptError(
                "checks",
                "must contain VerificationCheckResult values",
            )
        checks = tuple(sorted(checks, key=lambda item: item.checker_id))
        ids = [item.checker_id for item in checks]
        if len(ids) != len(set(ids)):
            raise VerificationReceiptError(
                "checks",
                "contains a duplicate checker id",
            )
        object.__setattr__(self, "checks", checks)
        expected_result = (
            VerificationResult.PASSED
            if all(item.result is VerificationResult.PASSED for item in checks)
            else VerificationResult.FAILED
        )
        if self.result is not expected_result:
            raise VerificationReceiptError(
                "result",
                "does not match the recorded checker results",
            )

    def to_payload(self) -> dict[str, object]:
        return _receipt_to_payload(self)


@dataclass(frozen=True)
class VerificationReceiptEvaluation:
    """Live validity of one recorded receipt against current anchors."""

    receipt: VerificationReceipt
    valid: bool
    reasons: tuple[VerificationInvalidationReason, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.receipt, VerificationReceipt):
            raise TypeError("receipt must be a VerificationReceipt")
        reasons = tuple(self.reasons)
        if any(
            not isinstance(reason, VerificationInvalidationReason)
            for reason in reasons
        ):
            raise TypeError(
                "reasons must contain VerificationInvalidationReason values"
            )
        if len(reasons) != len(set(reasons)):
            raise ValueError("receipt evaluation reasons must be unique")
        if self.valid != (not reasons):
            raise ValueError("receipt evaluation validity does not match reasons")
        object.__setattr__(self, "reasons", reasons)

    @property
    def recorded_result(self) -> VerificationResult:
        return self.receipt.result


def _bounded_result(
    checker_id: str,
    checker_version: str,
    *,
    passed: bool,
    diagnostics: Sequence[VerificationDiagnostic],
) -> VerificationCheckResult:
    ordered = tuple(
        sorted(
            diagnostics,
            key=lambda item: (item.code, item.subject or ""),
        )
    )
    observed = len(ordered)
    emitted_diagnostics = ordered[:MAX_DIAGNOSTICS_PER_CHECK]
    emitted = len(emitted_diagnostics)
    return VerificationCheckResult(
        checker_id=checker_id,
        checker_version=checker_version,
        result=(
            VerificationResult.PASSED
            if passed
            else VerificationResult.FAILED
        ),
        diagnostics=emitted_diagnostics,
        diagnostic_coverage=DiagnosticCoverage(
            observed=observed,
            emitted=emitted,
            omitted=observed - emitted,
            truncated=observed > emitted,
        ),
    )


def _artifact_integrity_checker(
    context: VerificationContext,
) -> VerificationCheckResult:
    diagnostics = list(context.artifact_diagnostics)
    if not context.artifact_integrity and not diagnostics:
        diagnostics.append(
            VerificationDiagnostic(code="artifact-integrity-failed")
        )
    passed = context.artifact_integrity and not diagnostics
    return _bounded_result(
        ARTIFACT_INTEGRITY_CHECKER_ID,
        "1",
        passed=passed,
        diagnostics=diagnostics,
    )


def _internal_links_checker(
    context: VerificationContext,
) -> VerificationCheckResult:
    diagnostics: list[VerificationDiagnostic] = []
    for relationship in context.knowledge.relationships:
        kind = (
            relationship.kind.value
            if isinstance(relationship.kind, RelationshipKind)
            else relationship.kind
        )
        if kind != RelationshipKind.LINKS_TO.value:
            continue
        if (
            context.scope_locator is not None
            and relationship.source_locator != context.scope_locator
        ):
            continue
        target_class = relationship.target.target_class
        resolution = relationship.resolution
        if target_class in {TargetClass.EXTERNAL, TargetClass.MAIL}:
            continue
        if resolution is Resolution.RESOLVED:
            continue
        if resolution is Resolution.AMBIGUOUS:
            code = "ambiguous-internal-link"
        elif target_class is TargetClass.MALFORMED:
            code = "malformed-internal-link"
        elif target_class is TargetClass.ASSET:
            code = "unresolved-internal-asset"
        else:
            code = "unresolved-internal-link"
        diagnostics.append(
            VerificationDiagnostic(
                code=code,
                subject=relationship.source_locator,
            )
        )
    return _bounded_result(
        INTERNAL_LINKS_CHECKER_ID,
        "1",
        passed=not diagnostics,
        diagnostics=diagnostics,
    )


def checker_registry() -> Mapping[str, CheckerContract]:
    """Return the immutable application-owned checker registry."""

    return _CHECKER_REGISTRY


def checker_contract(checker_id: str) -> CheckerContract:
    """Return one registered checker or fail closed."""

    _checker_id(checker_id, "checker_id")
    try:
        return _CHECKER_REGISTRY[checker_id]
    except KeyError as exc:
        raise UnknownVerificationCheckerError(checker_id) from exc


def _selected_contracts(
    checker_ids: Sequence[str] | None,
) -> tuple[CheckerContract, ...]:
    if isinstance(checker_ids, (str, bytes)):
        raise VerificationContractError(
            "checker_ids must be a sequence of checker ids, not text"
        )
    selected = (
        tuple(sorted(_CHECKER_REGISTRY))
        if checker_ids is None
        else tuple(checker_ids)
    )
    if not selected:
        raise VerificationContractError("at least one checker must be selected")
    if len(selected) > MAX_CHECKS_PER_RECEIPT:
        raise VerificationContractError("too many checkers were selected")
    if len(selected) != len(set(selected)):
        raise VerificationContractError("checker selection contains duplicates")

    # Resolve the complete selection before any checker can execute.
    contracts: list[CheckerContract] = []
    for checker_id in selected:
        if not isinstance(checker_id, str):
            raise UnknownVerificationCheckerError(checker_id)
        try:
            _checker_id(checker_id, "checker_id")
        except VerificationContractError as exc:
            raise UnknownVerificationCheckerError(checker_id) from exc
        try:
            contracts.append(_CHECKER_REGISTRY[checker_id])
        except KeyError as exc:
            raise UnknownVerificationCheckerError(checker_id) from exc
    return tuple(sorted(contracts, key=lambda item: item.checker_id))


def run_verification(
    context: VerificationContext,
    checker_ids: Sequence[str] | None = None,
) -> tuple[VerificationCheckResult, ...]:
    """Explicitly run selected pure checkers over supplied inputs."""

    if not isinstance(context, VerificationContext):
        raise TypeError("context must be a VerificationContext")
    contracts = _selected_contracts(checker_ids)
    return tuple(contract.run(context) for contract in contracts)


def build_verification_receipt(
    context: VerificationContext,
    checks: Sequence[VerificationCheckResult],
) -> VerificationReceipt:
    """Build a deterministic receipt without reading or writing files."""

    if not isinstance(context, VerificationContext):
        raise TypeError("context must be a VerificationContext")
    normalized_checks = tuple(checks)
    if not normalized_checks:
        raise VerificationContractError("checks must not be empty")
    if any(
        not isinstance(check, VerificationCheckResult)
        for check in normalized_checks
    ):
        raise VerificationContractError(
            "checks must contain VerificationCheckResult values"
        )
    result = (
        VerificationResult.PASSED
        if all(
            check.result is VerificationResult.PASSED
            for check in normalized_checks
        )
        else VerificationResult.FAILED
    )
    return VerificationReceipt(
        knowledge_hash=context.knowledge_hash,
        scope_uid=context.scope_uid,
        scope_hash=context.scope_hash,
        evidence=context.evidence,
        evidence_hash=context.evidence_hash,
        evaluated_snapshot=context.evaluated_snapshot,
        snapshot_hash=context.snapshot_hash,
        result=result,
        checks=normalized_checks,
    )


def verify(
    context: VerificationContext,
    checker_ids: Sequence[str] | None = None,
) -> VerificationReceipt:
    """Run selected checkers and return their deterministic in-memory receipt."""

    return build_verification_receipt(
        context,
        run_verification(context, checker_ids),
    )


def verification_receipt_to_payload(
    value: VerificationReceipt | object,
) -> dict[str, object]:
    """Validate and return a normalized JSON-compatible receipt payload."""

    receipt = validate_verification_receipt(value)
    return _receipt_to_payload(receipt)


def serialize_verification_receipt(
    value: VerificationReceipt | object,
) -> bytes:
    """Serialize one receipt deterministically with a trailing newline."""

    content = formatted_json_bytes(verification_receipt_to_payload(value))
    if len(content) > MAX_RECEIPT_BYTES:
        raise VerificationReceiptError(
            "receipt",
            "serialized receipt exceeds the byte limit",
        )
    return content


def validate_verification_receipt(
    value: VerificationReceipt | object,
) -> VerificationReceipt:
    """Strictly validate a receipt model or decoded JSON object."""

    payload = (
        _receipt_to_payload(value)
        if isinstance(value, VerificationReceipt)
        else value
    )
    root = _object(payload, "receipt")
    _exact_fields(
        root,
        "receipt",
        {
            "schema_version",
            "knowledge_hash",
            "scope",
            "evidence",
            "evidence_hash",
            "evaluated_snapshot",
            "snapshot_hash",
            "result",
            "checks",
        },
    )
    schema_version = _string(root["schema_version"], "schema_version")
    if schema_version != VERIFICATION_RECEIPT_SCHEMA_VERSION:
        raise VerificationReceiptError(
            "schema_version",
            f"must be {VERIFICATION_RECEIPT_SCHEMA_VERSION!r}",
        )
    knowledge_hash = _receipt_hash(root["knowledge_hash"], "knowledge_hash")

    scope = _object(root["scope"], "scope")
    _exact_fields(scope, "scope", {"uid", "hash"})
    scope_uid = _string(scope["uid"], "scope.uid")
    try:
        _scope_uid(scope_uid, "scope.uid")
    except VerificationContractError as exc:
        raise VerificationReceiptError("scope.uid", str(exc)) from exc
    scope_hash = _receipt_hash(scope["hash"], "scope.hash")

    evidence = _receipt_anchor_mapping(root["evidence"], "evidence")
    evidence_hash = _receipt_hash(root["evidence_hash"], "evidence_hash")
    if evidence_hash != hash_json(dict(evidence)):
        raise VerificationReceiptError(
            "evidence_hash",
            "does not match the canonical evidence object",
        )
    evaluated_snapshot = _receipt_anchor_mapping(
        root["evaluated_snapshot"],
        "evaluated_snapshot",
    )
    snapshot_hash = _receipt_hash(root["snapshot_hash"], "snapshot_hash")
    if snapshot_hash != hash_json(dict(evaluated_snapshot)):
        raise VerificationReceiptError(
            "snapshot_hash",
            "does not match the canonical evaluated snapshot",
        )

    try:
        result = VerificationResult(root["result"])
    except (TypeError, ValueError) as exc:
        raise VerificationReceiptError(
            "result",
            "must be 'passed' or 'failed'",
        ) from exc

    raw_checks = _object(root["checks"], "checks")
    if not raw_checks:
        raise VerificationReceiptError("checks", "must not be empty")
    if len(raw_checks) > MAX_CHECKS_PER_RECEIPT:
        raise VerificationReceiptError("checks", "contains too many checkers")
    checks = tuple(
        _parse_check(checker_id, raw_check, f"checks.{checker_id}")
        for checker_id, raw_check in sorted(raw_checks.items())
    )
    return VerificationReceipt(
        schema_version=schema_version,
        knowledge_hash=knowledge_hash,
        scope_uid=scope_uid,
        scope_hash=scope_hash,
        evidence=evidence,
        evidence_hash=evidence_hash,
        evaluated_snapshot=evaluated_snapshot,
        snapshot_hash=snapshot_hash,
        result=result,
        checks=checks,
    )


def deserialize_verification_receipt(content: bytes) -> VerificationReceipt:
    """Decode canonical UTF-8 JSON while rejecting duplicate object keys."""

    if not isinstance(content, bytes):
        raise TypeError("content must be bytes")
    if len(content) > MAX_RECEIPT_BYTES:
        raise VerificationReceiptError("receipt", "exceeds the byte limit")
    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise VerificationReceiptError("receipt", "must be valid UTF-8") from exc

    def unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
        result: dict[str, object] = {}
        for key, item in pairs:
            if key in result:
                raise VerificationReceiptError(
                    "receipt",
                    f"contains duplicate JSON key {key!r}",
                )
            result[key] = item
        return result

    def reject_constant(value: str) -> None:
        raise VerificationReceiptError(
            "receipt",
            f"contains non-finite number {value!r}",
        )

    try:
        payload = json.loads(
            text,
            object_pairs_hook=unique_object,
            parse_constant=reject_constant,
        )
    except VerificationReceiptError:
        raise
    except (RecursionError, TypeError, ValueError) as exc:
        raise VerificationReceiptError(
            "receipt",
            f"must contain valid JSON: {exc}",
        ) from exc
    receipt = validate_verification_receipt(payload)
    expected = serialize_verification_receipt(receipt)
    if content != expected:
        raise VerificationReceiptError(
            "receipt",
            "must use the deterministic receipt encoding",
        )
    return receipt


def verification_receipt_path(wiki_dir: str | Path) -> Path:
    """Return the fixed disposable receipt path."""

    return Path(wiki_dir) / VERIFICATION_RECEIPT_FILENAME


def load_verification_receipt(
    wiki_dir: str | Path,
    *,
    missing_ok: bool = True,
) -> VerificationReceipt | None:
    """Load the fixed receipt without following a receipt symlink."""

    root = Path(wiki_dir)
    escaped = first_unsafe_path_component(root)
    if escaped is not None:
        raise VerificationReceiptError(
            "wiki_dir",
            "must not contain traversal, symbolic-link, or reparse-point components",
        )
    if root.is_symlink():
        raise VerificationReceiptError(
            "wiki_dir",
            "must not be a symbolic link",
        )
    path = verification_receipt_path(root)
    content = _read_regular_receipt(path, missing_ok=missing_ok)
    if content is None:
        return None
    return deserialize_verification_receipt(content)


def write_verification_receipt(
    wiki_dir: str | Path,
    receipt: VerificationReceipt | object,
) -> Path:
    """Atomically replace the fixed receipt with deterministic bytes."""

    content = serialize_verification_receipt(receipt)
    root = Path(wiki_dir)
    escaped = first_unsafe_path_component(root)
    if escaped is not None:
        raise VerificationReceiptError(
            "wiki_dir",
            "must not contain traversal, symbolic-link, or reparse-point components",
        )
    if root.is_symlink():
        raise VerificationReceiptError(
            "wiki_dir",
            "must not be a symbolic link",
        )
    if not root.is_dir():
        raise VerificationReceiptError(
            "wiki_dir",
            "must be an existing directory",
        )
    path = verification_receipt_path(root)
    if path.is_symlink():
        raise VerificationReceiptError(
            VERIFICATION_RECEIPT_FILENAME,
            "must not be a symbolic link",
        )
    if path.exists() and not path.is_file():
        raise VerificationReceiptError(
            VERIFICATION_RECEIPT_FILENAME,
            "must be a regular file",
        )
    write_bytes_atomic(path, content)
    return path


def verify_and_write_receipt(
    wiki_dir: str | Path,
    context: VerificationContext,
    checker_ids: Sequence[str] | None = None,
) -> VerificationReceipt:
    """Run, fully build, then atomically write one receipt.

    The complete checker selection is resolved before any checker executes.
    Checker failures and unknown IDs therefore leave an existing receipt
    untouched.
    """

    receipt = verify(context, checker_ids)
    write_verification_receipt(wiki_dir, receipt)
    return receipt


def evaluate_verification_receipt(
    receipt: VerificationReceipt | object,
    context: VerificationContext,
) -> VerificationReceiptEvaluation:
    """Compute live validity without executing any checker."""

    current_receipt = validate_verification_receipt(receipt)
    if not isinstance(context, VerificationContext):
        raise TypeError("context must be a VerificationContext")

    reasons: list[VerificationInvalidationReason] = []

    def add(reason: VerificationInvalidationReason) -> None:
        if reason not in reasons:
            reasons.append(reason)

    if current_receipt.knowledge_hash != context.knowledge_hash:
        add(VerificationInvalidationReason.KNOWLEDGE_CHANGED)
    if (
        current_receipt.scope_uid != context.scope_uid
        or current_receipt.scope_hash != context.scope_hash
    ):
        add(VerificationInvalidationReason.SCOPE_CHANGED)
    if (
        dict(current_receipt.evidence) != dict(context.evidence)
        or current_receipt.evidence_hash != context.evidence_hash
    ):
        add(VerificationInvalidationReason.EVIDENCE_CHANGED)
    if (
        dict(current_receipt.evaluated_snapshot)
        != dict(context.evaluated_snapshot)
        or current_receipt.snapshot_hash != context.snapshot_hash
    ):
        add(VerificationInvalidationReason.SNAPSHOT_CHANGED)
    for check in current_receipt.checks:
        contract = _CHECKER_REGISTRY.get(check.checker_id)
        if contract is None:
            add(VerificationInvalidationReason.UNKNOWN_CHECKER)
        elif contract.version != check.checker_version:
            add(VerificationInvalidationReason.CHECKER_VERSION_CHANGED)

    return VerificationReceiptEvaluation(
        receipt=current_receipt,
        valid=not reasons,
        reasons=tuple(reasons),
    )


def load_and_evaluate_verification_receipt(
    wiki_dir: str | Path,
    context: VerificationContext,
    *,
    missing_ok: bool = True,
) -> VerificationReceiptEvaluation | None:
    """Load and evaluate a receipt without running its recorded checkers."""

    receipt = load_verification_receipt(wiki_dir, missing_ok=missing_ok)
    if receipt is None:
        return None
    return evaluate_verification_receipt(receipt, context)


def _receipt_to_payload(receipt: VerificationReceipt) -> dict[str, object]:
    return {
        "schema_version": receipt.schema_version,
        "knowledge_hash": receipt.knowledge_hash,
        "scope": {
            "uid": receipt.scope_uid,
            "hash": receipt.scope_hash,
        },
        "evidence": dict(receipt.evidence),
        "evidence_hash": receipt.evidence_hash,
        "evaluated_snapshot": dict(receipt.evaluated_snapshot),
        "snapshot_hash": receipt.snapshot_hash,
        "result": receipt.result.value,
        "checks": {
            check.checker_id: check.to_payload() for check in receipt.checks
        },
    }


def _parse_check(
    checker_key: str,
    value: object,
    field_name: str,
) -> VerificationCheckResult:
    try:
        _checker_id(checker_key, field_name)
    except VerificationContractError as exc:
        raise VerificationReceiptError(field_name, str(exc)) from exc
    record = _object(value, field_name)
    _exact_fields(
        record,
        field_name,
        {
            "checker",
            "result",
            "diagnostics",
            "diagnostic_coverage",
        },
    )
    checker = _object(record["checker"], f"{field_name}.checker")
    _exact_fields(
        checker,
        f"{field_name}.checker",
        {"id", "version"},
    )
    checker_id = _string(checker["id"], f"{field_name}.checker.id")
    checker_version = _string(
        checker["version"],
        f"{field_name}.checker.version",
    )
    try:
        _checker_id(checker_id, f"{field_name}.checker.id")
        _checker_version(
            checker_version,
            f"{field_name}.checker.version",
        )
    except VerificationContractError as exc:
        raise VerificationReceiptError(field_name, str(exc)) from exc
    if checker_id != checker_key:
        raise VerificationReceiptError(
            f"{field_name}.checker.id",
            "must match its checks object key",
        )
    try:
        result = VerificationResult(record["result"])
    except (TypeError, ValueError) as exc:
        raise VerificationReceiptError(
            f"{field_name}.result",
            "must be 'passed' or 'failed'",
        ) from exc

    raw_diagnostics = _array(
        record["diagnostics"],
        f"{field_name}.diagnostics",
    )
    if len(raw_diagnostics) > MAX_DIAGNOSTICS_PER_CHECK:
        raise VerificationReceiptError(
            f"{field_name}.diagnostics",
            "exceeds the receipt limit",
        )
    diagnostics = tuple(
        _parse_diagnostic(
            item,
            f"{field_name}.diagnostics[{index}]",
        )
        for index, item in enumerate(raw_diagnostics)
    )
    if list(diagnostics) != sorted(
        diagnostics,
        key=lambda item: (item.code, item.subject or ""),
    ):
        raise VerificationReceiptError(
            f"{field_name}.diagnostics",
            "must use deterministic diagnostic ordering",
        )
    coverage = _parse_coverage(
        record["diagnostic_coverage"],
        f"{field_name}.diagnostic_coverage",
    )
    try:
        return VerificationCheckResult(
            checker_id=checker_id,
            checker_version=checker_version,
            result=result,
            diagnostics=diagnostics,
            diagnostic_coverage=coverage,
        )
    except VerificationContractError as exc:
        raise VerificationReceiptError(field_name, str(exc)) from exc


def _parse_diagnostic(
    value: object,
    field_name: str,
) -> VerificationDiagnostic:
    record = _object(value, field_name)
    _exact_fields(
        record,
        field_name,
        {"code"},
        optional={"subject"},
    )
    code = _string(record["code"], f"{field_name}.code")
    subject = (
        _string(record["subject"], f"{field_name}.subject")
        if "subject" in record
        else None
    )
    try:
        return VerificationDiagnostic(code=code, subject=subject)
    except VerificationContractError as exc:
        raise VerificationReceiptError(field_name, str(exc)) from exc


def _parse_coverage(
    value: object,
    field_name: str,
) -> DiagnosticCoverage:
    record = _object(value, field_name)
    _exact_fields(
        record,
        field_name,
        {"observed", "emitted", "omitted", "limit", "truncated"},
    )
    observed = _nonnegative_int(record["observed"], f"{field_name}.observed")
    emitted = _nonnegative_int(record["emitted"], f"{field_name}.emitted")
    omitted = _nonnegative_int(record["omitted"], f"{field_name}.omitted")
    limit = _nonnegative_int(record["limit"], f"{field_name}.limit")
    truncated = record["truncated"]
    if not isinstance(truncated, bool):
        raise VerificationReceiptError(
            f"{field_name}.truncated",
            "must be a boolean",
        )
    try:
        return DiagnosticCoverage(
            observed=observed,
            emitted=emitted,
            omitted=omitted,
            limit=limit,
            truncated=truncated,
        )
    except VerificationContractError as exc:
        raise VerificationReceiptError(field_name, str(exc)) from exc


def _read_regular_receipt(
    path: Path,
    *,
    missing_ok: bool,
) -> bytes | None:
    try:
        metadata = path.lstat()
    except FileNotFoundError:
        if missing_ok:
            return None
        raise VerificationReceiptError(
            VERIFICATION_RECEIPT_FILENAME,
            "is absent",
        )
    except OSError as exc:
        raise VerificationReceiptError(
            VERIFICATION_RECEIPT_FILENAME,
            "could not be inspected",
        ) from exc
    if stat.S_ISLNK(metadata.st_mode):
        raise VerificationReceiptError(
            VERIFICATION_RECEIPT_FILENAME,
            "must not be a symbolic link",
        )
    if not stat.S_ISREG(metadata.st_mode):
        raise VerificationReceiptError(
            VERIFICATION_RECEIPT_FILENAME,
            "must be a regular file",
        )
    flags = os.O_RDONLY
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        descriptor = os.open(path, flags)
    except OSError as exc:
        raise VerificationReceiptError(
            VERIFICATION_RECEIPT_FILENAME,
            "could not be opened without following links",
        ) from exc
    try:
        opened = os.fstat(descriptor)
        if not stat.S_ISREG(opened.st_mode):
            raise VerificationReceiptError(
                VERIFICATION_RECEIPT_FILENAME,
                "must remain a regular file while being read",
            )
        chunks: list[bytes] = []
        remaining = MAX_RECEIPT_BYTES + 1
        while remaining > 0:
            chunk = os.read(descriptor, min(64 * 1024, remaining))
            if not chunk:
                break
            chunks.append(chunk)
            remaining -= len(chunk)
        content = b"".join(chunks)
    finally:
        os.close(descriptor)
    if len(content) > MAX_RECEIPT_BYTES:
        raise VerificationReceiptError(
            "receipt",
            "exceeds the byte limit",
        )
    return content


def _normalized_anchor_mapping(
    value: Mapping[str, str],
    field_name: str,
) -> Mapping[str, str]:
    if not isinstance(value, Mapping):
        raise VerificationContractError(f"{field_name} must be an object")
    if len(value) > MAX_ANCHORS:
        raise VerificationContractError(f"{field_name} contains too many anchors")
    normalized: dict[str, str] = {}
    for key, item in value.items():
        if (
            not isinstance(key, str)
            or _ANCHOR_ID_RE.fullmatch(key) is None
            or _WINDOWS_ABSOLUTE_RE.match(key) is not None
        ):
            raise VerificationContractError(
                f"{field_name} contains an invalid anchor id"
            )
        _sha256(item, f"{field_name}.{key}")
        normalized[key] = item
    return MappingProxyType(dict(sorted(normalized.items())))


def _receipt_anchor_mapping(
    value: object,
    field_name: str,
) -> Mapping[str, str]:
    record = _object(value, field_name)
    try:
        return _normalized_anchor_mapping(record, field_name)  # type: ignore[arg-type]
    except VerificationContractError as exc:
        raise VerificationReceiptError(field_name, str(exc)) from exc


def _checker_id(value: object, field_name: str) -> str:
    if not isinstance(value, str) or _CHECKER_ID_RE.fullmatch(value) is None:
        raise VerificationContractError(
            f"{field_name} must be a lowercase hyphen-separated checker id"
        )
    return value


def _checker_version(value: object, field_name: str) -> str:
    if not isinstance(value, str) or _CHECKER_VERSION_RE.fullmatch(value) is None:
        raise VerificationContractError(
            f"{field_name} must be a numeric dotted version"
        )
    return value


def _machine_code(value: object, field_name: str) -> str:
    if not isinstance(value, str) or _MACHINE_CODE_RE.fullmatch(value) is None:
        raise VerificationContractError(
            f"{field_name} must be a lowercase hyphen-separated machine code"
        )
    return value


def _diagnostic_subject(value: object, field_name: str) -> str:
    if (
        not isinstance(value, str)
        or _DIAGNOSTIC_SUBJECT_RE.fullmatch(value) is None
    ):
        raise VerificationContractError(
            f"{field_name} must be a bounded portable identifier"
        )
    return value


def _scope_uid(value: object, field_name: str) -> str:
    if (
        not isinstance(value, str)
        or _SCOPE_UID_RE.fullmatch(value) is None
        or value.startswith(("/", "\\"))
        or "\\" in value
        or "://" in value
        or _WINDOWS_ABSOLUTE_RE.match(value) is not None
    ):
        raise VerificationContractError(
            f"{field_name} must be a bounded portable stable identifier"
        )
    return value


def _portable_text(
    value: object,
    field_name: str,
    *,
    maximum: int,
) -> str:
    return require_bounded_text(
        value,
        maximum=maximum,
        require_trimmed=True,
        error=VerificationContractError(
            f"{field_name} must be bounded non-control text"
        ),
    )


def _sha256(value: object, field_name: str) -> str:
    return require_sha256(
        value,
        digest_error=VerificationContractError(
            f"{field_name} must be a canonical lowercase SHA-256 value"
        ),
    )


def _receipt_hash(value: object, field_name: str) -> str:
    try:
        return _sha256(value, field_name)
    except VerificationContractError as exc:
        raise VerificationReceiptError(field_name, str(exc)) from exc


def _object(value: object, field_name: str) -> Mapping[str, object]:
    return require_mapping(
        value,
        error=VerificationReceiptError(field_name, "must be an object"),
        require_string_keys=True,
        key_error=VerificationReceiptError(field_name, "must use string keys"),
    )


def _array(value: object, field_name: str) -> list[object]:
    return require_list(
        value,
        error=VerificationReceiptError(field_name, "must be an array"),
    )


def _string(value: object, field_name: str) -> str:
    return require_string(
        value,
        error=VerificationReceiptError(field_name, "must be a string"),
    )


def _nonnegative_int(value: object, field_name: str) -> int:
    return require_nonnegative_int(
        value,
        error=VerificationReceiptError(
            field_name,
            "must be a non-negative integer",
        ),
    )


def _exact_fields(
    value: Mapping[str, object],
    field_name: str,
    required: set[str],
    *,
    optional: set[str] | None = None,
) -> None:
    optional = optional or set()
    return require_shared_exact_fields(
        value,
        allowed=required | optional,
        required=required,
        mapping_error=VerificationReceiptError(field_name, "must be an object"),
        missing_error=lambda fields: VerificationReceiptError(
            f"{field_name}.{fields[0]}", "is required"
        ),
        unknown_error=lambda fields: VerificationReceiptError(
            f"{field_name}.{fields[0]}", "is not supported"
        ),
    )


_CHECKER_REGISTRY: Mapping[str, CheckerContract] = MappingProxyType(
    {
        ARTIFACT_INTEGRITY_CHECKER_ID: CheckerContract(
            checker_id=ARTIFACT_INTEGRITY_CHECKER_ID,
            version="1",
            description="Validate supplied surface, knowledge, and manifest integrity.",
            _runner=_artifact_integrity_checker,
        ),
        INTERNAL_LINKS_CHECKER_ID: CheckerContract(
            checker_id=INTERNAL_LINKS_CHECKER_ID,
            version="1",
            description="Validate already observed internal-link resolutions.",
            _runner=_internal_links_checker,
        ),
    }
)


__all__ = [
    "ARTIFACT_INTEGRITY_CHECKER_ID",
    "INTERNAL_LINKS_CHECKER_ID",
    "MAX_DIAGNOSTICS_PER_CHECK",
    "MAX_RECEIPT_BYTES",
    "VERIFICATION_RECEIPT_FILENAME",
    "VERIFICATION_RECEIPT_SCHEMA_VERSION",
    "CheckerContract",
    "DiagnosticCoverage",
    "UnknownVerificationCheckerError",
    "VerificationCheckResult",
    "VerificationContext",
    "VerificationContractError",
    "VerificationDiagnostic",
    "VerificationInvalidationReason",
    "VerificationReceipt",
    "VerificationReceiptError",
    "VerificationReceiptEvaluation",
    "VerificationResult",
    "build_artifact_verification_context",
    "build_verification_receipt",
    "checker_contract",
    "checker_registry",
    "deserialize_verification_receipt",
    "evaluate_verification_receipt",
    "load_and_evaluate_verification_receipt",
    "load_verification_receipt",
    "run_verification",
    "serialize_verification_receipt",
    "validate_verification_receipt",
    "verification_receipt_path",
    "verification_receipt_to_payload",
    "verify",
    "verify_and_write_receipt",
    "write_verification_receipt",
]
