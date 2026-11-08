"""Protected GitHub Actions entry point for reviewed wiki delivery."""

from __future__ import annotations

import importlib
from io import BytesIO
import json
import os
from pathlib import Path
import stat
import sys
from zipfile import ZIP_DEFLATED, ZIP_STORED, ZipFile

from llm_wiki_cli.services.knowledge_evidence import hash_json, sha256_bytes
from llm_wiki_cli.services.knowledge_storage_io import read_guarded
from llm_wiki_cli.services.publication_candidate import (
    MAX_FILE_BYTES,
    MAX_FILES,
    MAX_TREE_BYTES,
    _provider,
    validate_publication_receipt,
)
from llm_wiki_cli.services.publication_config import (
    publication_ref_name,
    read_publication_json,
    validate_publication_config,
)
from llm_wiki_cli.services.publication_delivery import validate_rollback_review
from llm_wiki_cli.services.publication_impact import (
    MAX_JSON_BYTES,
    compare_publication_impact,
    read_publication_document,
)
from llm_wiki_cli.services.validation import require_portable_relative_path

# Both directories are from the pinned action. -I keeps caller code off sys.path.
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))
checkout = importlib.import_module("checkout")
git_transport = importlib.import_module("git_transport")


def hosted_context(operation: str) -> dict[str, str]:
    if operation not in {"qualify", "deliver", "plan-rollback", "rollback"}:
        raise ValueError("Unknown delivery operation")
    if (
        os.environ.get("GITHUB_ACTIONS") != "true"
        or os.environ.get("GITHUB_SERVER_URL") != "https://github.com"
    ):
        raise ValueError("The publisher requires a GitHub.com Actions run")
    if os.environ["GITHUB_EVENT_NAME"] not in {"push", "workflow_dispatch"}:
        raise ValueError("Delivery requires a trusted push or manual dispatch")
    if os.environ.get("GITHUB_REF_PROTECTED") != "true":
        raise ValueError("Run the publisher from a protected source branch or tag")
    checkout._revision(os.environ["ACTION_REVISION"])
    return {
        "repository": os.environ["GITHUB_REPOSITORY"],
        "run_id": os.environ["GITHUB_RUN_ID"],
        "run_attempt": os.environ["GITHUB_RUN_ATTEMPT"],
        "event": os.environ["GITHUB_EVENT_NAME"],
        "ref": os.environ["GITHUB_REF"],
        "source_sha": checkout._revision(os.environ["GITHUB_SHA"]),
    }


def artifact_files(
    incoming: Path, receipt: dict, archive_hash: str
) -> dict[str, bytes]:
    # The archive stays data throughout delivery. Only declared blobs enter Git.
    raw = read_guarded(
        incoming / "candidate.zip", MAX_TREE_BYTES + 16 * 1024**2
    ).content
    if sha256_bytes(raw) != archive_hash:
        raise ValueError("Candidate archive hash differs from the preparation handoff")
    files: dict[str, bytes] = {}
    total = 0
    with ZipFile(BytesIO(raw)) as archive:
        entries = archive.infolist()
        if len(entries) != len(receipt["files"]) or len(entries) > MAX_FILES:
            raise ValueError("Archive inventory differs from the checked receipt")
        for entry in entries:
            name = entry.orig_filename
            if (
                name != entry.filename
                or name not in receipt["files"]
                or name in files
                or not stat.S_ISREG(entry.external_attr >> 16)
                or entry.compress_type not in {ZIP_DEFLATED, ZIP_STORED}
                or entry.flag_bits & 1
                or entry.file_size > MAX_FILE_BYTES
            ):
                raise ValueError("Unexpected archive entry or unsupported file type")
            total += entry.file_size
            if total > MAX_TREE_BYTES:
                raise ValueError("Candidate exceeds its public byte budget")
            with archive.open(entry) as member:
                data = member.read(MAX_FILE_BYTES + 1)
            if (
                len(data) != entry.file_size
                or sha256_bytes(data) != receipt["files"][name]
            ):
                raise ValueError("Candidate file differs from its reviewed bytes")
            files[name] = data
    return files


def checked_artifact(
    incoming: Path,
    runtime: Path,
    context: dict,
    policy: dict,
    expected_receipt: str,
    accepted_pin: str,
) -> tuple[dict, dict[str, bytes]]:
    receipt = read_publication_document(incoming / "receipt.json")
    validate_publication_receipt(receipt)
    if (
        not receipt["ready"]
        or receipt["receipt_id"] != expected_receipt
        or receipt["basis"]["config"] != policy
        or receipt["context"]["source_revision"] != context["source_sha"]
    ):
        raise ValueError(
            "Reviewed receipt does not match the successful preparation and eligible source"
        )
    handoff = read_publication_json(incoming / "delivery-handoff.json")
    required = {
        **context,
        "schema_version": "llm-wiki-delivery-handoff/v1",
        "receipt_id": expected_receipt,
        "accepted_state_revision": accepted_pin,
    }
    if any(handoff.get(key) != value for key, value in required.items()):
        raise ValueError(
            "Handoff belongs to a different run, attempt, ref or accepted review revision"
        )
    installed = read_publication_json(runtime / "evidence/provider.json")
    prepared = read_publication_json(incoming / "provider.json")
    if installed.get("installed") is not True or prepared.get("installed") is not True:
        raise ValueError("Missing installed provider attestation")
    for key in (
        "action_ref",
        "action_repository",
        "provider_revision",
        "version",
        "package_sha256",
        "parser_version",
    ):
        if prepared[key] != installed[key]:
            raise ValueError("Publisher and preparation provider identities differ")
    if (
        installed["provider_revision"] != os.environ["ACTION_REVISION"]
        or installed["action_repository"] != os.environ["ACTION_REPOSITORY"]
        or receipt["provider"] != _provider()
    ):
        raise ValueError("Receipt is not from the pinned installed provider")
    return receipt, artifact_files(incoming, receipt, handoff["archive_hash"])


def committed_record(
    root: Path,
    prefix: Path,
    pin: str,
    path: str,
    runtime: Path,
    name: str,
    limit: int = MAX_JSON_BYTES,
) -> dict:
    relative = (prefix / require_portable_relative_path(path)).as_posix()
    _, data = checkout.committed_blob(root, pin, relative, limit)
    local = runtime / (name + ".json")
    with local.open("xb") as stream:
        stream.write(data)
    return read_publication_json(local, max_bytes=limit)


def accepted_reviews(root, prefix, pin, runtime, receipt, paths):
    records = {
        key: committed_record(root, prefix, pin, path, runtime, key) if path else None
        for key, path in paths.items()
    }
    if (
        records["candidate-review"] != receipt["review"]["decision"]
        or not receipt["review"]["accepted"]
    ):
        raise ValueError("The accepted approval does not match this exact candidate")
    reviews, previous, baseline = (
        records[k] for k in ("reviews", "previous-receipt", "baseline")
    )
    if previous is not None:
        validate_publication_receipt(previous)
        if not previous["ready"]:
            raise ValueError("Prior ownership receipt requires accepted reviews")
    if (
        receipt["inputs"]
        != {
            "reviews_hash": hash_json(reviews) if reviews is not None else None,
            "baseline_id": baseline["basis_id"] if baseline is not None else None,
            "previous_receipt_id": previous["receipt_id"]
            if previous is not None
            else None,
        }
        or compare_publication_impact(receipt["basis"], baseline, reviews=reviews)
        != receipt["impact"]
    ):
        raise ValueError(
            "Topic review or ownership differs from the accepted Git records"
        )


def run() -> None:
    operation = os.environ["OPERATION"]
    context = hosted_context(operation)
    # Only the transport receives tokens, separately scoped to source and target.
    source_token = os.environ.pop("SOURCE_TOKEN", "")
    wiki_token = os.environ.pop("WIKI_TOKEN", "")
    if not wiki_token:
        raise ValueError("A protected wiki Git credential is required")
    runtime = Path(os.environ["WIKI_RUNTIME"])
    consumer = Path(os.environ["WIKI_CONSUMER"])
    root = checkout._repository(consumer)
    prefix = consumer.relative_to(root)
    sha = context["source_sha"]
    if checkout._git(root, "rev-parse", "HEAD").decode().strip() != sha:
        raise ValueError("Publisher checkout differs from the triggering source SHA")
    policy = validate_publication_config(
        committed_record(
            root,
            prefix,
            sha,
            os.environ["CONFIG_PATH"],
            runtime,
            "source-policy",
            256 * 1024,
        ),
        consumer_root=None,
    )
    source = context["repository"]
    target = os.environ["TARGET_REPOSITORY"]
    target = source if target == "self" else target
    configured = policy["target"]["repository"]
    if target.casefold() != (source if configured == "self" else configured).casefold():
        raise ValueError("Publisher target differs from the committed policy")
    if operation != "qualify" and policy["publish"] is not True:
        raise ValueError("Delivery is disabled by the eligible source policy")
    options = dict(
        policy=policy,
        source_repository=source,
        target_repository=target,
        source_remote=f"https://github.com/{source}.git",
        target_remote=f"https://github.com/{target}.wiki.git",
        source_ref=context["ref"],
        source_token=source_token,
        target_token=wiki_token,
    )
    if operation == "qualify":
        result = git_transport.qualify(source_revision=sha, **options)
    else:
        if operation in {"deliver", "rollback"}:
            review_branch = publication_ref_name(
                os.environ["APPROVAL_BRANCH"], "approval-branch"
            )
            approval_pin = checkout._revision(
                checkout._git(
                    root,
                    "rev-parse",
                    "--verify",
                    "refs/remotes/origin/" + review_branch + "^{commit}",
                )
                .decode()
                .strip()
            )
        if operation == "deliver":
            receipt, files = checked_artifact(
                runtime / "incoming",
                runtime,
                context,
                policy,
                os.environ["EXPECTED_RECEIPT"],
                approval_pin,
            )
            accepted_reviews(
                root,
                prefix,
                approval_pin,
                runtime,
                receipt,
                {
                    key: os.environ.get(key.upper().replace("-", "_") + "_PATH", "")
                    for key in (
                        "candidate-review",
                        "reviews",
                        "previous-receipt",
                        "baseline",
                    )
                },
            )
            result = git_transport.deliver(receipt=receipt, files=files, **options)
        else:
            options.update(
                source_revision=sha,
                target_revision=checkout._revision(os.environ["TARGET_REVISION"]),
                restore_revision=checkout._revision(os.environ["RESTORE_REVISION"]),
            )
            if operation == "plan-rollback":
                result = git_transport.preview_rollback(**options)
            else:
                record = committed_record(
                    root,
                    prefix,
                    approval_pin,
                    os.environ["ROLLBACK_REVIEW_PATH"],
                    runtime,
                    "rollback-approval",
                )
                # The transport independently recomputes the approved ID,
                # including when reconciling an already-committed rollback.
                validate_rollback_review(record, rollback_id=record["rollback_id"])
                result = git_transport.rollback(
                    accepted_rollback_id=record["rollback_id"], **options
                )
    path = runtime / "evidence/delivery-result.json"
    path.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as stream:
        stream.write(f"result-path={path.as_posix()}\n")
        stream.write(
            "readback-verified="
            + str(result.get("readback_verified") is True).lower()
            + "\n"
        )


if __name__ == "__main__":
    try:
        run()
    except Exception as exc:
        path = Path(os.environ["WIKI_RUNTIME"]) / "evidence/delivery-result.json"
        path.write_text(
            json.dumps(
                {"status": "unverified", "readback_verified": False, "error": str(exc)},
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        raise SystemExit(
            "Wiki operation did not verify. Inspect the delivery evidence before retrying."
        ) from None
