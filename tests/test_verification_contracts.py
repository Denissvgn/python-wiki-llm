from __future__ import annotations

import json
from dataclasses import replace
from types import MappingProxyType

import pytest

from llm_wiki_cli.services.knowledge_evidence import sha256_bytes
from llm_wiki_cli.services.knowledge_model import parse_knowledge_index
from llm_wiki_cli.services import verification_contracts as verification
from llm_wiki_cli.services.verification_contracts import (
    ARTIFACT_INTEGRITY_CHECKER_ID,
    INTERNAL_LINKS_CHECKER_ID,
    MAX_DIAGNOSTICS_PER_CHECK,
    MAX_RECEIPT_BYTES,
    VERIFICATION_RECEIPT_FILENAME,
    CheckerContract,
    UnknownVerificationCheckerError,
    VerificationCheckResult,
    VerificationContext,
    VerificationDiagnostic,
    VerificationInvalidationReason,
    VerificationReceiptError,
    VerificationResult,
    checker_contract,
    checker_registry,
    deserialize_verification_receipt,
    evaluate_verification_receipt,
    load_and_evaluate_verification_receipt,
    load_verification_receipt,
    run_verification,
    serialize_verification_receipt,
    validate_verification_receipt,
    verification_receipt_to_payload,
    verify,
    verify_and_write_receipt,
    write_verification_receipt,
)
from tests.knowledge_fixtures import fixture_hash, one_module_two_entities_fixture


@pytest.fixture(scope="module")
def fixture_knowledge():
    fixture = one_module_two_entities_fixture()
    return fixture, parse_knowledge_index(fixture.knowledge_payload)


def _context(
    fixture_knowledge,
    *,
    scope_locator: str | None = None,
    artifact_integrity: bool = True,
    artifact_diagnostics: tuple[VerificationDiagnostic, ...] = (),
) -> VerificationContext:
    fixture, knowledge = fixture_knowledge
    knowledge_hash = sha256_bytes(fixture.knowledge_bytes)
    if scope_locator is None:
        scope_uid = "bundle-fixture"
        scope_hash = knowledge_hash
    else:
        concept = next(
            item for item in knowledge.concepts if item.locator == scope_locator
        )
        scope_uid = f"uid-{concept.document.page_id}"
        scope_hash = concept.facets.semantics.page_hash
    snapshot = knowledge.bundle.snapshot
    return VerificationContext(
        knowledge=knowledge,
        knowledge_hash=knowledge_hash,
        scope_uid=scope_uid,
        scope_hash=scope_hash,
        scope_locator=scope_locator,
        evidence={
            "knowledge": knowledge_hash,
            "observations": fixture_hash("verification:evidence"),
        },
        evaluated_snapshot={
            "generation-options": snapshot.generation_options_hash,
            "markdown": snapshot.markdown_snapshot_hash,
            "source": snapshot.source_snapshot_hash,
            "surface": snapshot.surface_index_hash,
        },
        artifact_integrity=artifact_integrity,
        artifact_diagnostics=artifact_diagnostics,
    )


def test_registry_is_static_application_owned_and_exact():
    registry = checker_registry()

    assert isinstance(registry, MappingProxyType)
    assert set(registry) == {
        ARTIFACT_INTEGRITY_CHECKER_ID,
        INTERNAL_LINKS_CHECKER_ID,
    }
    assert checker_contract(ARTIFACT_INTEGRITY_CHECKER_ID) is (
        registry[ARTIFACT_INTEGRITY_CHECKER_ID]
    )
    assert all(
        contract._runner.__module__ == verification.__name__  # noqa: SLF001
        for contract in registry.values()
    )
    with pytest.raises(TypeError):
        registry["document-selected"] = registry[ARTIFACT_INTEGRITY_CHECKER_ID]


def test_unknown_checker_fails_closed():
    with pytest.raises(UnknownVerificationCheckerError):
        checker_contract("document-selected")


def test_artifact_integrity_checker_uses_only_supplied_result(fixture_knowledge):
    diagnostics = (
        VerificationDiagnostic(
            code="manifest-hash-mismatch",
            subject="artifact_hashes.knowledge_index_hash",
        ),
    )
    context = _context(
        fixture_knowledge,
        artifact_integrity=False,
        artifact_diagnostics=diagnostics,
    )

    (result,) = run_verification(
        context,
        [ARTIFACT_INTEGRITY_CHECKER_ID],
    )

    assert result.result is VerificationResult.FAILED
    assert result.diagnostics == diagnostics
    assert result.diagnostic_coverage.to_payload() == {
        "observed": 1,
        "emitted": 1,
        "omitted": 0,
        "limit": MAX_DIAGNOSTICS_PER_CHECK,
        "truncated": False,
    }


def test_internal_links_checker_is_scope_aware(fixture_knowledge):
    bundle_context = _context(fixture_knowledge)
    bundle_result = run_verification(
        bundle_context,
        [INTERNAL_LINKS_CHECKER_ID],
    )[0]
    entity_context = _context(
        fixture_knowledge,
        scope_locator="llm-wiki://entities/User",
    )
    entity_result = run_verification(
        entity_context,
        [INTERNAL_LINKS_CHECKER_ID],
    )[0]

    assert bundle_result.result is VerificationResult.FAILED
    assert [item.code for item in bundle_result.diagnostics] == [
        "malformed-internal-link",
        "unresolved-internal-link",
    ]
    assert {
        item.subject for item in bundle_result.diagnostics
    } == {"llm-wiki://modules/accounts"}
    assert entity_result.result is VerificationResult.PASSED
    assert entity_result.diagnostics == ()


def test_checkers_do_not_call_the_receipt_writer(fixture_knowledge, monkeypatch):
    def unexpected_write(*_args, **_kwargs):
        raise AssertionError("pure checker attempted filesystem output")

    monkeypatch.setattr(verification, "write_bytes_atomic", unexpected_write)

    results = run_verification(_context(fixture_knowledge))

    assert {item.checker_id for item in results} == {
        ARTIFACT_INTEGRITY_CHECKER_ID,
        INTERNAL_LINKS_CHECKER_ID,
    }


def test_receipt_is_deterministic_and_diagnostics_are_bounded(fixture_knowledge):
    diagnostics = tuple(
        VerificationDiagnostic(
            code="artifact-integrity-failed",
            subject=f"artifact.field-{index:03d}",
        )
        for index in range(MAX_DIAGNOSTICS_PER_CHECK + 7)
    )
    context = _context(
        fixture_knowledge,
        artifact_integrity=False,
        artifact_diagnostics=diagnostics,
    )

    first = verify(context, [ARTIFACT_INTEGRITY_CHECKER_ID])
    second = verify(context, [ARTIFACT_INTEGRITY_CHECKER_ID])
    first_bytes = serialize_verification_receipt(first)
    second_bytes = serialize_verification_receipt(second)
    check = first.checks[0]

    assert first == second
    assert first_bytes == second_bytes
    assert len(check.diagnostics) == MAX_DIAGNOSTICS_PER_CHECK
    assert check.diagnostic_coverage.observed == (
        MAX_DIAGNOSTICS_PER_CHECK + 7
    )
    assert check.diagnostic_coverage.omitted == 7
    assert check.diagnostic_coverage.truncated is True
    assert b"evaluated_at" not in first_bytes
    assert b"timestamp" not in first_bytes
    assert b"checked_at" not in first_bytes


def test_fixed_path_atomic_write_and_load_round_trip(
    tmp_path,
    fixture_knowledge,
):
    receipt = verify(
        _context(
            fixture_knowledge,
            scope_locator="llm-wiki://entities/User",
        )
    )

    path = write_verification_receipt(tmp_path, receipt)
    first_bytes = path.read_bytes()
    write_verification_receipt(tmp_path, receipt)

    assert path == tmp_path / VERIFICATION_RECEIPT_FILENAME
    assert path.read_bytes() == first_bytes
    assert load_verification_receipt(tmp_path) == receipt
    evaluation = load_and_evaluate_verification_receipt(
        tmp_path,
        _context(
            fixture_knowledge,
            scope_locator="llm-wiki://entities/User",
        ),
    )
    assert evaluation is not None
    assert evaluation.valid is True


def test_unknown_checker_fails_before_write_and_preserves_prior_receipt(
    tmp_path,
    fixture_knowledge,
    monkeypatch,
):
    path = tmp_path / VERIFICATION_RECEIPT_FILENAME
    path.write_bytes(b"prior receipt bytes\n")
    runner_calls: list[VerificationContext] = []

    def trap_runner(context: VerificationContext) -> VerificationCheckResult:
        runner_calls.append(context)
        raise AssertionError("checker ran before the complete selection was resolved")

    monkeypatch.setattr(
        verification,
        "_CHECKER_REGISTRY",
        MappingProxyType(
            {
                ARTIFACT_INTEGRITY_CHECKER_ID: CheckerContract(
                    checker_id=ARTIFACT_INTEGRITY_CHECKER_ID,
                    version="1",
                    description="Trap checker for selection-order coverage.",
                    _runner=trap_runner,
                )
            }
        ),
    )

    with pytest.raises(UnknownVerificationCheckerError):
        verify_and_write_receipt(
            tmp_path,
            _context(fixture_knowledge),
            [ARTIFACT_INTEGRITY_CHECKER_ID, "unknown-checker"],
        )

    assert runner_calls == []
    assert path.read_bytes() == b"prior receipt bytes\n"


def test_receipt_loader_rejects_duplicate_keys(tmp_path, fixture_knowledge):
    receipt = verify(
        _context(
            fixture_knowledge,
            scope_locator="llm-wiki://entities/User",
        ),
        [ARTIFACT_INTEGRITY_CHECKER_ID],
    )
    content = serialize_verification_receipt(receipt).decode("utf-8")
    duplicate = content.replace(
        '  "knowledge_hash":',
        f'  "knowledge_hash": "{fixture_hash("duplicate")}",\n'
        '  "knowledge_hash":',
        1,
    )
    (tmp_path / VERIFICATION_RECEIPT_FILENAME).write_text(
        duplicate,
        encoding="utf-8",
    )

    with pytest.raises(VerificationReceiptError, match="duplicate JSON key"):
        load_verification_receipt(tmp_path)


def test_receipt_loader_rejects_noncanonical_json(tmp_path, fixture_knowledge):
    receipt = verify(
        _context(
            fixture_knowledge,
            scope_locator="llm-wiki://entities/User",
        ),
        [ARTIFACT_INTEGRITY_CHECKER_ID],
    )
    payload = verification_receipt_to_payload(receipt)
    (tmp_path / VERIFICATION_RECEIPT_FILENAME).write_text(
        json.dumps(payload, sort_keys=True),
        encoding="utf-8",
    )

    with pytest.raises(
        VerificationReceiptError,
        match="deterministic receipt encoding",
    ):
        load_verification_receipt(tmp_path)


def test_receipt_loader_rejects_symlink(tmp_path, fixture_knowledge):
    receipt = verify(
        _context(
            fixture_knowledge,
            scope_locator="llm-wiki://entities/User",
        ),
        [ARTIFACT_INTEGRITY_CHECKER_ID],
    )
    target = tmp_path / "outside-receipt.json"
    target.write_bytes(serialize_verification_receipt(receipt))
    receipt_path = tmp_path / VERIFICATION_RECEIPT_FILENAME
    try:
        receipt_path.symlink_to(target)
    except (NotImplementedError, OSError):
        pytest.skip("symbolic links are unavailable on this platform")

    with pytest.raises(VerificationReceiptError, match="symbolic link"):
        load_verification_receipt(tmp_path)
    with pytest.raises(VerificationReceiptError, match="symbolic link"):
        write_verification_receipt(tmp_path, receipt)


def test_receipt_loader_rejects_oversized_input(tmp_path):
    (tmp_path / VERIFICATION_RECEIPT_FILENAME).write_bytes(
        b"{" + (b" " * MAX_RECEIPT_BYTES) + b"}"
    )

    with pytest.raises(VerificationReceiptError, match="byte limit"):
        load_verification_receipt(tmp_path)


def test_receipt_decoder_wraps_excessive_json_nesting():
    content = (
        ("[" * 100_000) + "0" + ("]" * 100_000)
    ).encode("utf-8")
    assert len(content) < MAX_RECEIPT_BYTES

    with pytest.raises(VerificationReceiptError, match="valid JSON"):
        deserialize_verification_receipt(content)


def test_receipt_read_and_write_reject_symlinked_ancestor(
    tmp_path,
    fixture_knowledge,
):
    checkout = tmp_path / "checkout"
    checkout.mkdir()
    outside = tmp_path / "outside"
    wiki = outside / "wiki"
    wiki.mkdir(parents=True)
    linked_parent = checkout / "docs"
    try:
        linked_parent.symlink_to(outside, target_is_directory=True)
    except (NotImplementedError, OSError):
        pytest.skip("symbolic links are unavailable on this platform")
    escaped_wiki = linked_parent / "wiki"
    receipt = verify(
        _context(fixture_knowledge),
        [ARTIFACT_INTEGRITY_CHECKER_ID],
    )

    with pytest.raises(VerificationReceiptError, match="component"):
        write_verification_receipt(escaped_wiki, receipt)
    with pytest.raises(VerificationReceiptError, match="component"):
        load_verification_receipt(escaped_wiki)
    assert not (wiki / VERIFICATION_RECEIPT_FILENAME).exists()


def test_receipt_path_rejects_symlink_followed_by_parent_traversal(
    tmp_path,
    fixture_knowledge,
):
    checkout = tmp_path / "checkout"
    safe_wiki = checkout / "wiki"
    safe_wiki.mkdir(parents=True)
    outside = tmp_path / "outside"
    (outside / "dir").mkdir(parents=True)
    outside_wiki = outside / "wiki"
    outside_wiki.mkdir()
    link = checkout / "link"
    try:
        link.symlink_to(outside / "dir", target_is_directory=True)
    except (NotImplementedError, OSError):
        pytest.skip("symbolic links are unavailable on this platform")
    escaped_wiki = checkout / "link" / ".." / "wiki"
    receipt = verify(
        _context(fixture_knowledge),
        [ARTIFACT_INTEGRITY_CHECKER_ID],
    )

    with pytest.raises(VerificationReceiptError, match="traversal"):
        write_verification_receipt(escaped_wiki, receipt)
    assert not (outside_wiki / VERIFICATION_RECEIPT_FILENAME).exists()
    assert not (safe_wiki / VERIFICATION_RECEIPT_FILENAME).exists()


@pytest.mark.parametrize(
    ("change", "reason"),
    [
        (
            lambda context: replace(
                context,
                knowledge_hash=fixture_hash("changed-knowledge"),
            ),
            VerificationInvalidationReason.KNOWLEDGE_CHANGED,
        ),
        (
            lambda context: replace(
                context,
                scope_hash=fixture_hash("changed-scope"),
            ),
            VerificationInvalidationReason.SCOPE_CHANGED,
        ),
        (
            lambda context: replace(
                context,
                evidence={
                    **dict(context.evidence),
                    "observations": fixture_hash("changed-evidence"),
                },
            ),
            VerificationInvalidationReason.EVIDENCE_CHANGED,
        ),
        (
            lambda context: replace(
                context,
                evaluated_snapshot={
                    **dict(context.evaluated_snapshot),
                    "source": fixture_hash("changed-snapshot"),
                },
            ),
            VerificationInvalidationReason.SNAPSHOT_CHANGED,
        ),
    ],
)
def test_live_validity_reacts_to_each_anchor(
    fixture_knowledge,
    change,
    reason,
):
    context = _context(
        fixture_knowledge,
        scope_locator="llm-wiki://entities/User",
    )
    receipt = verify(context, [ARTIFACT_INTEGRITY_CHECKER_ID])

    current = evaluate_verification_receipt(receipt, context)
    changed = evaluate_verification_receipt(receipt, change(context))

    assert current.valid is True
    assert current.reasons == ()
    assert changed.valid is False
    assert reason in changed.reasons


def test_live_validity_reports_checker_version_and_unknown_checker(
    fixture_knowledge,
):
    context = _context(
        fixture_knowledge,
        scope_locator="llm-wiki://entities/User",
    )
    receipt = verify(context, [ARTIFACT_INTEGRITY_CHECKER_ID])
    check = receipt.checks[0]
    changed_version = replace(
        receipt,
        checks=(replace(check, checker_version="2"),),
    )
    retired_checker = replace(
        receipt,
        checks=(
            replace(
                check,
                checker_id="retired-checker",
            ),
        ),
    )

    assert evaluate_verification_receipt(
        changed_version,
        context,
    ).reasons == (
        VerificationInvalidationReason.CHECKER_VERSION_CHANGED,
    )
    assert evaluate_verification_receipt(
        retired_checker,
        context,
    ).reasons == (
        VerificationInvalidationReason.UNKNOWN_CHECKER,
    )


def test_receipt_evaluation_never_executes_recorded_checker(
    fixture_knowledge,
    monkeypatch,
):
    context = _context(
        fixture_knowledge,
        scope_locator="llm-wiki://entities/User",
    )
    receipt = verify(context, [ARTIFACT_INTEGRITY_CHECKER_ID])

    def unexpected_execution(_context):
        raise AssertionError("receipt evaluation executed a checker")

    original = checker_registry()[ARTIFACT_INTEGRITY_CHECKER_ID]
    replacement = CheckerContract(
        checker_id=original.checker_id,
        version=original.version,
        description=original.description,
        _runner=unexpected_execution,
    )
    monkeypatch.setattr(
        verification,
        "_CHECKER_REGISTRY",
        MappingProxyType({replacement.checker_id: replacement}),
    )

    evaluation = evaluate_verification_receipt(receipt, context)

    assert evaluation.valid is True


def test_failed_result_remains_valid_recorded_evidence(fixture_knowledge):
    context = _context(fixture_knowledge)
    receipt = verify(context, [INTERNAL_LINKS_CHECKER_ID])

    evaluation = evaluate_verification_receipt(receipt, context)

    assert receipt.result is VerificationResult.FAILED
    assert evaluation.valid is True
    assert evaluation.recorded_result is VerificationResult.FAILED


def test_tampered_evidence_hash_is_rejected(fixture_knowledge):
    receipt = verify(
        _context(
            fixture_knowledge,
            scope_locator="llm-wiki://entities/User",
        ),
        [ARTIFACT_INTEGRITY_CHECKER_ID],
    )
    payload = verification_receipt_to_payload(receipt)
    payload["evidence_hash"] = fixture_hash("tampered")

    with pytest.raises(
        VerificationReceiptError,
        match="canonical evidence object",
    ):
        validate_verification_receipt(payload)


def test_deserializer_rejects_unknown_fields(fixture_knowledge):
    receipt = verify(
        _context(
            fixture_knowledge,
            scope_locator="llm-wiki://entities/User",
        ),
        [ARTIFACT_INTEGRITY_CHECKER_ID],
    )
    payload = verification_receipt_to_payload(receipt)
    payload["command"] = "arbitrary helper --run"
    content = (
        json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    ).encode("utf-8")

    with pytest.raises(VerificationReceiptError, match="command.*not supported"):
        deserialize_verification_receipt(content)


def test_missing_receipt_is_explicitly_optional(tmp_path):
    assert load_verification_receipt(tmp_path) is None
    with pytest.raises(VerificationReceiptError, match="absent"):
        load_verification_receipt(tmp_path, missing_ok=False)
