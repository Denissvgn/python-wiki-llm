"""Owned synthetic acceptance cases; no production answers or source imports."""

from copy import deepcopy
import hashlib

import pytest

from tests.developer_value.guide_review import (
    GUIDE_NAMES, QUESTIONS, REVIEW_SCOPE, commitment, validate_guide_phase,
)


def write(root, path, text):
    target = root / path
    target.parent.mkdir(parents=True, exist_ok=True)
    content = text.encode()
    target.write_bytes(content)
    return {"path": path, "sha256": hashlib.sha256(content).hexdigest()}


def tree(root):
    return {path.relative_to(root).as_posix(): path.read_bytes()
            for path in root.rglob("*") if path.is_file()}


def packet(root, phase="author"):
    # Importing inspected source would fail; the helper only reads byte slices.
    source = write(root, "selected/owner.py",
                   "raise RuntimeError('inspected source was imported')\n"
                   "def reader():\n    return 'cobalt'\n")
    raw = (root / source["path"]).read_bytes()
    ref = {
        "path": source["path"], "whole_file_sha256": source["sha256"],
        "start_line": 2, "end_line": 3,
        "slice_sha256": hashlib.sha256(b"".join(raw.splitlines(keepends=True)[1:3])).hexdigest(),
        "quote": "def reader():\n    return 'cobalt'\n",
    }
    bundle = {
        "schema_version": "af14-guide-phase/v1", "phase": phase, "author_id": "owned-author",
        "runtime_acceptance": "unestablished", "source_hashes": {source["path"]: source["sha256"]},
        "guides": {}, "material_claims": [], "answers": {}, "examples": [],
    }
    for index, name in enumerate(GUIDE_NAMES):
        text = "Owned reader returns cobalt."
        bundle["guides"][name] = write(
            root, f"guides/{name}.md",
            f"# Guide\n\n{text}\n\n[Source](../selected/owner.py#L2-L3)\n",
        )
        bundle["material_claims"].append({
            "id": name, "guide": name, "text": text, "refs": [deepcopy(ref)],
        })
        for question in QUESTIONS[index * 2:index * 2 + 2]:
            bundle["answers"][question] = {
                "guide": name, "text": text, "claim_ids": [name],
            }
    bundle["examples"] = [
        {"id": "success", "guide": "making-a-change", "argv": ["owned-reader"],
         "exit_code": 0, "stdout": "cobalt\n", "stderr": ""},
        {"id": "expected-failure", "guide": "symptom-investigation",
         "argv": ["owned-reader", "--invalid"], "exit_code": 2,
         "stdout": "", "stderr": "unknown argument\n"},
    ]
    review = {
        "status": "accepted", "phase": phase, "author_id": bundle["author_id"],
        "reviewer_id": "owned-independent-reviewer", "runtime_acceptance": "unestablished",
        "material_claim_scope": REVIEW_SCOPE, "source_hashes": deepcopy(bundle["source_hashes"]),
        "answer_verdicts": dict.fromkeys(QUESTIONS, "accepted"),
        "reference_artifact": write(root, "receipts/review.json", '{"owned": "review"}\n'),
    }
    window = {
        "phase": phase, "started_monotonic_ns": 100 * 10**9,
        "ended_monotonic_ns": 101 * 10**9, "revision_rounds": 0,
        "source_hashes": deepcopy(bundle["source_hashes"]),
        "evidence_receipt": write(root, "receipts/window.json", '{"owned": "window"}\n'),
    }
    context = {
        "root": root, "source_hashes": deepcopy(bundle["source_hashes"]),
        "review": review, "phase_window": window,
        "expected_examples": {item["id"]: deepcopy(item) for item in bundle["examples"]},
    }
    pin(bundle, context)
    return bundle, context


def pin(bundle, context):
    review = context["review"]
    review.update(
        bundle_sha256=commitment(bundle), guide_artifacts=deepcopy(bundle["guides"]),
        material_claims_sha256=commitment(bundle["material_claims"]),
        answers_sha256=commitment(bundle["answers"]),
    )
    context["phase_window"]["bundle_sha256"] = commitment(bundle)


def replace_guide(bundle, context, text):
    name = "orientation"
    bundle["guides"][name] = write(context["root"], bundle["guides"][name]["path"], text)
    pin(bundle, context)


@pytest.mark.parametrize("phase", ["author", "update"])
def test_controller_pinned_four_guides_accept_without_writes_or_source_execution(tmp_path, phase):
    bundle, context = packet(tmp_path, phase)
    before = tree(tmp_path), deepcopy((bundle, context))
    result = validate_guide_phase(bundle, **context)
    assert result == {
        "valid_phase": True, "phase": phase, "word_counts": dict.fromkeys(GUIDE_NAMES, 6),
        "elapsed_seconds": 1.0, "revision_rounds": 0, "runtime_acceptance": "unestablished",
        "actual_tokens": None, "actual_dollars": None,
        "acceptance": "externally-reviewed-source-and-comprehension",
    }
    assert (tree(tmp_path), (bundle, context)) == before
    assert bundle["examples"][1]["exit_code"] == 2


@pytest.mark.parametrize("elapsed,rounds,valid", [
    (0, 0, True), (7200 * 10**9, 2, True), (7200 * 10**9 + 1, 2, False),
    (-1, 0, False), (10**9, 3, False), (10**9, -1, False),
    (True, 0, False), (10**9, True, False),
])
def test_external_elapsed_and_revision_boundaries(tmp_path, elapsed, rounds, valid):
    bundle, context = packet(tmp_path)
    window = context["phase_window"]
    window["ended_monotonic_ns"] = window["started_monotonic_ns"] + elapsed
    window["revision_rounds"] = rounds
    if elapsed is True:
        window["ended_monotonic_ns"] = True
    if valid:
        assert validate_guide_phase(bundle, **context)["valid_phase"]
    else:
        with pytest.raises(ValueError):
            validate_guide_phase(bundle, **context)


@pytest.mark.parametrize("count,valid", [(999, True), (1000, True), (1001, False)])
@pytest.mark.parametrize("fenced", [False, True])
def test_word_limit_counts_visible_prose_and_code(tmp_path, count, valid, fenced):
    bundle, context = packet(tmp_path)
    text = (tmp_path / bundle["guides"]["orientation"]["path"]).read_text()
    addition = " ".join(["word"] * (count - 6))
    text += "\n\x60\x60\x60\n" + addition + "\n\x60\x60\x60\n" if fenced else "\n" + addition + "\n"
    replace_guide(bundle, context, text)
    if valid:
        assert validate_guide_phase(bundle, **context)["word_counts"]["orientation"] == count
    else:
        with pytest.raises(ValueError, match="1000 words"):
            validate_guide_phase(bundle, **context)


@pytest.mark.parametrize("change", [
    "missing-guide", "extra-guide", "duplicate-guide", "guide-hash", "source-bytes",
    "source-selection", "unselected-ref", "whole-hash", "slice-hash", "quote",
    "coordinates", "boolean-coordinates", "empty-claims", "duplicate-claim",
    "unknown-guide", "empty-refs", "missing-answer", "extra-answer", "unknown-answer-guide",
    "unbound-answer", "cross-guide-answer", "phase", "runtime", "schema",
])
def test_pinned_guide_source_claim_and_answer_drift_rejected(tmp_path, change):
    bundle, context = packet(tmp_path)
    claim = bundle["material_claims"][0]
    ref = claim["refs"][0]
    if change == "missing-guide":
        bundle["guides"].pop("orientation")
    elif change == "extra-guide":
        bundle["guides"]["extra"] = bundle["guides"]["orientation"]
    elif change == "duplicate-guide":
        bundle["guides"]["making-a-change"] = bundle["guides"]["orientation"]
    elif change == "guide-hash":
        bundle["guides"]["orientation"]["sha256"] = "0" * 64
    elif change == "source-bytes":
        (tmp_path / "selected/owner.py").write_text("different source\n")
    elif change == "source-selection":
        bundle["source_hashes"] = {}
    elif change == "unselected-ref":
        ref["path"] = "selected/other.py"
    elif change in {"whole-hash", "slice-hash"}:
        ref["whole_file_sha256" if change == "whole-hash" else "slice_sha256"] = "0" * 64
    elif change == "quote":
        ref["quote"] += "forged"
    elif change == "coordinates":
        ref["end_line"] = 4
    elif change == "boolean-coordinates":
        ref["start_line"] = True
    elif change == "empty-claims":
        bundle["material_claims"] = []
    elif change == "duplicate-claim":
        bundle["material_claims"].append(deepcopy(claim))
    elif change == "unknown-guide":
        claim["guide"] = "extra"
    elif change == "empty-refs":
        claim["refs"] = []
    elif change == "missing-answer":
        bundle["answers"].pop("Q8")
    elif change == "extra-answer":
        bundle["answers"]["Q9"] = deepcopy(bundle["answers"]["Q1"])
    elif change == "unknown-answer-guide":
        bundle["answers"]["Q1"]["guide"] = "extra"
    elif change == "unbound-answer":
        bundle["answers"]["Q1"]["claim_ids"] = ["absent"]
    elif change == "cross-guide-answer":
        bundle["answers"]["Q1"]["claim_ids"] = ["making-a-change"]
    elif change == "phase":
        bundle["phase"] = "invented"
    elif change == "runtime":
        bundle["runtime_acceptance"] = "established"
    else:
        bundle["schema_version"] = "invented"
    pin(bundle, context)
    with pytest.raises(ValueError):
        validate_guide_phase(bundle, **context)


@pytest.mark.parametrize("change", [
    "self-review", "padded-self-review", "no-reviewer", "wrong-author", "rejected",
    "partial-scope", "review-phase", "review-runtime", "review-bundle", "review-guides",
    "review-source", "review-claims", "review-answers", "wrong-answer", "unknown-verdict",
    "missing-verdict", "reference-hash", "reference-missing", "window-phase",
    "window-bundle", "window-source", "receipt-hash", "receipt-missing",
])
def test_external_review_and_window_authority_is_required(tmp_path, change):
    bundle, context = packet(tmp_path)
    review, window = context["review"], context["phase_window"]
    if change in {"self-review", "padded-self-review"}:
        review["reviewer_id"] = bundle["author_id"] + (" " if change.startswith("padded") else "")
    elif change == "no-reviewer":
        review["reviewer_id"] = ""
    elif change == "wrong-author":
        review["author_id"] = "other"
    elif change == "rejected":
        review["status"] = "rejected"
    elif change == "partial-scope":
        review["material_claim_scope"] = "registered-claims-only"
    elif change == "review-phase":
        review["phase"] = "update"
    elif change == "review-runtime":
        review["runtime_acceptance"] = "established"
    elif change in {"review-bundle", "review-claims", "review-answers"}:
        review[{"review-bundle": "bundle_sha256", "review-claims": "material_claims_sha256",
                "review-answers": "answers_sha256"}[change]] = "0" * 64
    elif change == "review-guides":
        review["guide_artifacts"] = {}
    elif change == "review-source":
        review["source_hashes"] = {}
    elif change == "wrong-answer":
        review["answer_verdicts"]["Q1"] = "rejected"
    elif change == "unknown-verdict":
        review["answer_verdicts"]["Q9"] = "accepted"
    elif change == "missing-verdict":
        review["answer_verdicts"].pop("Q8")
    elif change.startswith("reference"):
        review["reference_artifact"]["sha256" if change.endswith("hash") else "path"] = (
            "0" * 64 if change.endswith("hash") else "receipts/absent.json")
    elif change == "window-phase":
        window["phase"] = "update"
    elif change == "window-bundle":
        window["bundle_sha256"] = "0" * 64
    elif change == "window-source":
        window["source_hashes"] = {}
    else:
        window["evidence_receipt"]["sha256" if change.endswith("hash") else "path"] = (
            "0" * 64 if change.endswith("hash") else "receipts/absent.json")
    with pytest.raises(ValueError):
        validate_guide_phase(bundle, **context)


@pytest.mark.parametrize("replacement", [
    "<!-- Owned reader returns cobalt. -->",
    "\x60\x60\x60\nOwned reader returns cobalt.\n\x60\x60\x60",
    '[Metadata](https://example.invalid "Owned reader returns cobalt.")',
    "![Owned reader returns cobalt.](https://example.invalid/image.png)",
    '<span style="display:none">Owned reader returns cobalt.</span>',
])
def test_hidden_or_nonprose_material_claim_cannot_supply_visible_text(tmp_path, replacement):
    bundle, context = packet(tmp_path)
    markdown = (tmp_path / bundle["guides"]["orientation"]["path"]).read_text()
    replace_guide(bundle, context, markdown.replace("Owned reader returns cobalt.", replacement))
    with pytest.raises(ValueError):
        validate_guide_phase(bundle, **context)


@pytest.mark.parametrize("replacement", [
    "<!-- [Source](../selected/owner.py#L2-L3) -->",
    "\x60\x60\x60\n[Source](../selected/owner.py#L2-L3)\n\x60\x60\x60",
    "[Source](../selected/owner.py#L1-L3)",
    "[Source](../../outside.py#L2-L3)",
    "[Source](https://example.invalid/owner.py#L2-L3)",
    "[Source](../selected/owner.py?download=1#L2-L3)",
    '<a href="../selected/owner.py#L2-L3">Source</a>',
])
def test_missing_hidden_external_or_drifting_source_citation_rejected(tmp_path, replacement):
    bundle, context = packet(tmp_path)
    markdown = (tmp_path / bundle["guides"]["orientation"]["path"]).read_text()
    replace_guide(bundle, context, markdown.replace("[Source](../selected/owner.py#L2-L3)", replacement))
    with pytest.raises(ValueError):
        validate_guide_phase(bundle, **context)


def test_commonmark_reference_link_and_inline_formatting_are_visible(tmp_path):
    bundle, context = packet(tmp_path)
    markdown = (tmp_path / bundle["guides"]["orientation"]["path"]).read_text()
    markdown = markdown.replace("reader returns", "**reader** returns")
    markdown = markdown.replace("[Source](../selected/owner.py#L2-L3)", "[Source][source]")
    replace_guide(bundle, context, markdown + "\n[source]: <../selected/owner.py#L2-L3>\n")
    assert validate_guide_phase(bundle, **context)["valid_phase"]


def test_unregistered_prose_still_requires_review_of_changed_entire_guide(tmp_path):
    bundle, context = packet(tmp_path)
    descriptor = bundle["guides"]["orientation"]
    text = (tmp_path / descriptor["path"]).read_text() + "\nAn unregistered assertion.\n"
    bundle["guides"]["orientation"] = write(tmp_path, descriptor["path"], text)
    with pytest.raises(ValueError, match="review binding"):
        validate_guide_phase(bundle, **context)
    pin(bundle, context)
    context["review"]["status"] = "rejected"
    with pytest.raises(ValueError, match="whole-guide"):
        validate_guide_phase(bundle, **context)


@pytest.mark.parametrize("change", ["drop-failure", "exit-code", "stdout", "stderr", "argv", "duplicate"])
def test_frozen_example_outcomes_preserve_failures_and_reject_drift(tmp_path, change):
    bundle, context = packet(tmp_path)
    if change == "drop-failure":
        bundle["examples"].pop()
    elif change == "duplicate":
        bundle["examples"].append(deepcopy(bundle["examples"][0]))
    else:
        bundle["examples"][1][change.replace("-", "_")] = (
            0 if change == "exit-code" else ["other"] if change == "argv" else "forged")
    pin(bundle, context)
    with pytest.raises(ValueError):
        validate_guide_phase(bundle, **context)


@pytest.mark.parametrize("path", ["../outside.md", "/absolute.md", "guides/../other.md"])
def test_artifact_paths_cannot_escape_or_alias(tmp_path, path):
    bundle, context = packet(tmp_path)
    bundle["guides"]["orientation"]["path"] = path
    pin(bundle, context)
    with pytest.raises(ValueError):
        validate_guide_phase(bundle, **context)


def test_symlinked_source_cannot_supply_selected_identity(tmp_path):
    bundle, context = packet(tmp_path)
    source = tmp_path / "selected/owner.py"
    content = source.read_bytes()
    source.unlink()
    (tmp_path / "selected/alternate.py").write_bytes(content)
    source.symlink_to("alternate.py")
    with pytest.raises(ValueError, match="symlink"):
        validate_guide_phase(bundle, **context)


def test_stale_author_source_cannot_pass_update_phase(tmp_path):
    bundle, context = packet(tmp_path, "update")
    source = write(tmp_path, "selected/owner.py", "def reader():\n    return 'indigo'\n")
    context["source_hashes"] = {source["path"]: source["sha256"]}
    with pytest.raises(ValueError, match="source identity"):
        validate_guide_phase(bundle, **context)


def test_empty_or_hidden_claim_register_text_is_rejected(tmp_path):
    bundle, context = packet(tmp_path)
    bundle["material_claims"][0]["text"] = "<!-- Owned reader returns cobalt. -->"
    pin(bundle, context)
    with pytest.raises(ValueError, match="visible prose"):
        validate_guide_phase(bundle, **context)


def test_claim_and_answer_markdown_render_symmetrically(tmp_path):
    bundle, context = packet(tmp_path)
    suffix = " [Source](../selected/owner.py#L2-L3)"
    bundle["material_claims"][0]["text"] += suffix
    for question in ("Q1", "Q2"):
        bundle["answers"][question]["text"] += suffix
    # Link label and claim are rendered on consecutive Markdown prose lines.
    descriptor = bundle["guides"]["orientation"]
    markdown = (tmp_path / descriptor["path"]).read_text()
    replace_guide(bundle, context, markdown.replace(
        "Owned reader returns cobalt.\n\n[Source]",
        "Owned reader returns cobalt. [Source]",
    ))
    assert validate_guide_phase(bundle, **context)["valid_phase"]


def test_minimal_external_outcome_mapping_pins_success_and_failure(tmp_path):
    bundle, context = packet(tmp_path)
    context["expected_examples"] = {
        item["id"]: {key: item[key] for key in ("exit_code", "stdout", "stderr")}
        for item in bundle["examples"]
    }
    assert validate_guide_phase(bundle, **context)["valid_phase"]
    context["expected_examples"]["expected-failure"]["exit_code"] = 0
    with pytest.raises(ValueError, match="example outcome"):
        validate_guide_phase(bundle, **context)


def test_exact_unicode_crlf_source_slices_preserve_byte_terminators(tmp_path):
    bundle, context = packet(tmp_path)
    source = write(tmp_path, "selected/owner.py", "def reader():\r\n    return 'cóbolt'\r\n")
    raw = (tmp_path / source["path"]).read_bytes()
    bundle["source_hashes"] = {source["path"]: source["sha256"]}
    for claim in bundle["material_claims"]:
        claim["refs"] = [{
            "path": source["path"], "whole_file_sha256": source["sha256"],
            "start_line": 1, "end_line": 2, "slice_sha256": hashlib.sha256(raw).hexdigest(),
            "quote": raw.decode(),
        }]
    for name, descriptor in list(bundle["guides"].items()):
        text = (tmp_path / descriptor["path"]).read_text().replace("#L2-L3", "#L1-L2")
        bundle["guides"][name] = write(tmp_path, descriptor["path"], text)
    for value in (context, context["review"], context["phase_window"]):
        value["source_hashes"] = deepcopy(bundle["source_hashes"])
    pin(bundle, context)
    assert validate_guide_phase(bundle, **context)["valid_phase"]
    bundle["material_claims"][0]["refs"][0]["quote"] = raw.decode().replace("\r\n", "\n")
    pin(bundle, context)
    with pytest.raises(ValueError, match="slice byte"):
        validate_guide_phase(bundle, **context)


def sidecar_packet(root):
    bundle, context = packet(root)
    supplemental = [
        write(root, "claims.json", '{"claims": "retained authored bytes"}\n'),
        write(root, "answers.json", '{"answers": "retained authored bytes"}\n'),
        write(root, "examples.json", '{"examples": "retained failed and successful outcomes"}\n'),
    ]
    bundle["supplemental_artifacts"] = supplemental
    descriptor = bundle["guides"]["documentation-maintenance"]
    text = (root / descriptor["path"]).read_text()
    text += "\n" + "\n".join(
        f"[Retained {item['path']}](../{item['path']})" for item in supplemental
    ) + "\n"
    bundle["guides"]["documentation-maintenance"] = write(root, descriptor["path"], text)
    pin(bundle, context)
    return bundle, context


def test_bound_authored_json_sidecars_resolve_without_replacing_source_citations(tmp_path):
    bundle, context = sidecar_packet(tmp_path)
    before = tree(tmp_path), deepcopy((bundle, context))
    assert validate_guide_phase(bundle, **context)["valid_phase"]
    assert (tree(tmp_path), (bundle, context)) == before


@pytest.mark.parametrize("change", [
    "drift", "hash", "duplicate", "python-target", "python-disguised-as-json",
    "selected-json-source", "external-descriptor", "external-link", "unbound",
    "fragment", "source-citation-removed", "review-unpinned",
])
def test_supplemental_sidecars_reject_unbound_source_and_byte_bypasses(tmp_path, change):
    bundle, context = sidecar_packet(tmp_path)
    descriptor = bundle["supplemental_artifacts"][0]
    guide = bundle["guides"]["documentation-maintenance"]
    text = (tmp_path / guide["path"]).read_text()
    if change == "drift":
        (tmp_path / descriptor["path"]).write_text('{"changed": true}\n')
    elif change == "hash":
        descriptor["sha256"] = "0" * 64
    elif change == "duplicate":
        bundle["supplemental_artifacts"].append(deepcopy(descriptor))
    elif change == "python-target":
        replacement = write(tmp_path, "unselected.py", "def reader():\n    return 1\n")
        bundle["supplemental_artifacts"][0] = replacement
        text = text.replace("../claims.json", "../unselected.py")
    elif change == "python-disguised-as-json":
        bundle["supplemental_artifacts"][0] = write(tmp_path, "claims.json", "print('source')\n")
    elif change == "selected-json-source":
        for value in (bundle, context, context["review"], context["phase_window"]):
            value["source_hashes"][descriptor["path"]] = descriptor["sha256"]
    elif change == "external-descriptor":
        descriptor["path"] = "../outside.json"
    elif change == "external-link":
        text = text.replace("../claims.json", "../../outside.json")
    elif change == "unbound":
        bundle["supplemental_artifacts"].pop(0)
    elif change == "fragment":
        text = text.replace("../claims.json", "../claims.json#claims")
    elif change == "source-citation-removed":
        text = text.replace("[Source](../selected/owner.py#L2-L3)", "[Retained](../claims.json)")
    elif change == "review-unpinned":
        bundle["supplemental_artifacts"].append(write(tmp_path, "extra.json", "{}\n"))
        with pytest.raises(ValueError, match="review binding"):
            validate_guide_phase(bundle, **context)
        return
    bundle["guides"]["documentation-maintenance"] = write(tmp_path, guide["path"], text)
    pin(bundle, context)
    with pytest.raises(ValueError):
        validate_guide_phase(bundle, **context)
