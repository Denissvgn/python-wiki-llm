"""Verify consumer inputs and retain the exact public wiki candidate checked by CI."""

import difflib
import json
import os
from pathlib import Path
import subprocess
import sys
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

from llm_wiki_cli.services.knowledge_evidence import sha256_bytes
from llm_wiki_cli.services.publication_candidate import _read_tree, validate_publication_receipt
from llm_wiki_cli.services.publication_impact import read_publication_document


ACTION = Path(__file__).resolve().parent
ACCEPTED = ("baseline", "reviews", "previous-receipt", "candidate-review")


def action_input(name: str, default: str = "") -> str:
    value = os.environ.get("INPUT_" + name.upper().replace("-", "_"), default)
    if "\n" in value or "\r" in value:
        raise ValueError(f"{name} must be a single line")
    return value


def run_cli(action, options, consumer, evidence):
    with (evidence / f"{action}.log").open("wb") as errors:
        result = subprocess.run(
            [sys.executable, "-I", "-m", "llm_wiki_cli.cli", "docs", "wiki", action, *options],
            cwd=consumer, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=errors,
            timeout=1800,
        )
    if result.returncode not in {0, 1}:
        raise ValueError(f"Candidate {action} failed; inspect {action}.log")
    return result.returncode


def write_diff(stream, path: str, before: bytes | None, after: bytes | None, operation: dict):
    stream.write(f"\n{operation['kind']} {path}\n")
    stream.write(f"before {operation['before']}\nafter  {operation['after']}\n")
    if before == after:
        return
    # Long lines and binary attachments are reviewed in the exact archive.
    # Limit the line diff cost on PR-controlled text, independently of file bounds.
    old, new = before or b"", after or b""
    if max(len(old), len(new)) <= 256 * 1024 and b"\0" not in old + new:
        try:
            left, right = old.decode("utf-8").splitlines(), new.decode("utf-8").splitlines()
        except UnicodeDecodeError:
            pass
        else:
            if len(left) + len(right) <= 4000:
                for line in difflib.unified_diff(
                    left, right, fromfile="/dev/null" if before is None else f"a/{path}",
                    tofile="/dev/null" if after is None else f"b/{path}", lineterm="",
                ):
                    stream.write(line + "\n")
                return
    stream.write("Inspect the target and candidate bytes for this attachment.\n")


def retain(receipt, candidate, target, evidence):
    """Build the upload from the same validated bytes used in the diff."""
    validate_publication_receipt(receipt)
    after = _read_tree(candidate)
    before = {} if target is None else _read_tree(target, target_snapshot=True)
    for files, expected in ((after, receipt["files"]), (before, receipt["target"]["files"])):
        if {name: sha256_bytes(raw) for name, raw in files.items()} != expected:
            raise ValueError("Public files changed after the independent candidate check")
    # Nest a ZIP inside the Actions artifact so valid hidden files, empty files
    # and exact path spellings survive upload-artifact's filesystem globbing.
    with ZipFile(evidence / "candidate.zip", "x") as archive:
        for path, raw in sorted(after.items()):
            info = ZipInfo(path)
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            archive.writestr(info, raw, compress_type=ZIP_DEFLATED)
    with (evidence / "candidate.diff").open("x", encoding="utf-8", newline="\n") as stream:
        stream.write("Wiki candidate " + receipt["candidate_id"] + "\n")
        for operation in receipt["operations"]:
            if operation["kind"] != "unchanged":
                path = operation["path"]
                write_diff(stream, path, before.get(path), after.get(path), operation)
    (evidence / "impact.json").write_text(
        json.dumps(receipt["impact"], ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def run(mode: str) -> None:
    # -I removes the script directory as well as the current directory. Only
    # the pinned action's own integration helpers may be imported from disk.
    sys.path.insert(0, str(ACTION))
    from checkout import accepted_inputs, verified_checkout, verified_target

    consumer = Path(os.environ["WIKI_CONSUMER"])
    runtime = Path(os.environ["WIKI_RUNTIME"])
    evidence = runtime / "evidence"
    helpers = runtime / "helpers"
    os.environ["LLM_WIKI_CACHE_DIR"] = str(helpers)
    config = action_input("config", ".llm-wiki/publication.json")
    source_dir = action_input("src-dir")
    source_revision = action_input("source-revision")
    target_dir, target_revision = action_input("target-dir"), action_input("target-revision")
    accepted = {name: action_input(name) for name in ACCEPTED if action_input(name)}
    fail_on = action_input("fail-on", "error")
    if fail_on not in {"error", "review-required"}:
        raise ValueError("fail-on must be error or review-required")
    if mode not in {"toolchains", "candidate"}:
        raise ValueError("Unknown candidate action step")
    source_sha = verified_checkout(consumer, source_revision, target_dir, accepted)
    target_sha = verified_target(consumer, target_dir, target_revision)
    subprocess.run(
        [sys.executable, "-I", str(ACTION / "prepare.py"),
         "toolchains" if mode == "toolchains" else "check",
         str(consumer), config, source_dir, str(evidence), str(helpers)],
        cwd=runtime, check=True, timeout=1800,
    )
    if mode == "toolchains":
        return

    materialized, accepted_pin = accepted_inputs(consumer, accepted, action_input("accepted-state-revision"), runtime)
    common = [f"--config={config}", f"--source-revision={source_sha}"]
    if target_dir:
        common.append(f"--target-dir={target_dir}")
    if target_sha:
        common.append(f"--target-revision={target_sha}")
    common.extend(f"--{option}={path}" for option, path in materialized.items())
    candidate = runtime / "candidate"
    exported = runtime / "export.json"
    checked = runtime / "checked.json"
    export_code = run_cli("export", [*common, "--output-dir", str(candidate),
                                     "--receipt", str(exported)], consumer, evidence)
    check_code = run_cli("check", [*common, "--candidate-dir", str(candidate), "--receipt", str(exported),
                                   "--output", str(checked)], consumer, evidence)
    receipt = read_publication_document(checked)
    if receipt != read_publication_document(exported) or check_code != export_code:
        raise ValueError("Export and check disagree on the candidate")
    if verified_checkout(consumer, source_sha, target_dir, accepted) != source_sha or (
        verified_target(consumer, target_dir, target_revision, receipt_files=receipt["target"]["files"]) != target_sha
    ):
        raise ValueError("The source or target checkout changed during preparation")
    retain(receipt, candidate, consumer / target_dir if target_dir else None, evidence)
    checked.replace(evidence / "receipt.json")
    if receipt["ready"] and receipt["basis"]["config"]["publish"]:
        handoff = {
            "schema_version": "llm-wiki-delivery-handoff/v1",
            "repository": os.environ["GITHUB_REPOSITORY"],
            "run_id": os.environ["GITHUB_RUN_ID"],
            "run_attempt": os.environ["GITHUB_RUN_ATTEMPT"],
            "event": os.environ["GITHUB_EVENT_NAME"],
            "ref": os.environ["GITHUB_REF"],
            "source_sha": source_sha,
            "accepted_state_revision": accepted_pin,
            "receipt_id": receipt["receipt_id"],
            "archive_hash": sha256_bytes((evidence / "candidate.zip").read_bytes()),
        }
        (evidence / "delivery-handoff.json").write_text(
            json.dumps(handoff, sort_keys=True, indent=2) + "\n", encoding="utf-8"
        )
    changed = receipt["files"] != receipt["target"]["files"]
    impact = receipt["impact"]
    values = {
        "receipt-id": receipt["receipt_id"],
        "candidate-dir": candidate.as_posix(), "receipt-path": (evidence / "receipt.json").as_posix(),
        "report-path": (evidence / "impact.json").as_posix(), "diff-path": (evidence / "candidate.diff").as_posix(),
        "changed": str(changed).lower(), "ready": str(receipt["ready"]).lower(),
    }
    with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as output:
        for key, value in values.items():
            output.write(f"{key}={value}\n")
    with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8") as summary:
        summary.write(
            "\n## GitHub wiki candidate\n\n"
            f"Public files: {len(receipt['files'])}. Changed: {values['changed']}. "
            f"Ready for local review policy: {values['ready']}.\n\n"
            f"Structural findings: {len(receipt['checks']['findings'])}. "
            f"Impact findings: {len(impact['findings'])}. "
            "See the candidate archive, diff and checked receipt in the job artifact.\n"
        )
    if check_code or not receipt["checks"]["ok"] or not impact["complete"]:
        raise ValueError("The candidate contains structural errors or incomplete evidence")
    if impact["enforcement"] == "required" and not impact["ready"]:
        raise ValueError("The consumer's required impact review is incomplete")
    if fail_on == "review-required" and not receipt["ready"]:
        raise ValueError("The candidate needs topic review or exact artifact approval")


if __name__ == "__main__":
    try:
        run(sys.argv[1])
    except (ValueError, OSError, subprocess.SubprocessError) as exc:
        # A malformed consumer filename should remain inert in a runner log.
        message = str(exc)
        (Path(os.environ["WIKI_RUNTIME"]) / "evidence/error.txt").write_text(message + "\n", encoding="utf-8")
        raise SystemExit("Wiki candidate error: " + repr(message)) from None
