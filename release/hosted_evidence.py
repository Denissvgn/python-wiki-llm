"""Authenticate release evidence against the exact hosted producer artifacts.

Only standard-library modules are used. Marker sidecars are not an authority:
GitHub run/job records and SHA-256-verified artifact ZIPs provide the binding.
"""

from __future__ import annotations

from datetime import datetime
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
from typing import Any
import urllib.error
import urllib.parse
import urllib.request
import zipfile

SCHEMA = "agent-wiki-hosted-evidence/v1"
MAX_ARCHIVE = 64 * 1024 * 1024
MAX_EXPANDED = 256 * 1024 * 1024
WORKFLOW = ".github/workflows/release-qualification.yml"


class EvidenceError(ValueError):
    """Producer provenance is unavailable or inconsistent."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise EvidenceError(message)


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _json(raw: bytes) -> Any:
    def unique(pairs):
        result = {}
        for key, value in pairs:
            require(key not in result, f"duplicate JSON key: {key}")
            result[key] = value
        return result

    def invalid(value):
        raise EvidenceError(f"nonfinite JSON value: {value}")

    return json.loads(raw, object_pairs_hook=unique, parse_constant=invalid)


def artifact_contract(layout: str) -> dict[str, tuple[str, str, tuple[str, ...]]]:
    require(layout in {"legacy", "union"}, "unknown qualifying suite layout")

    def core(lane: str) -> str:
        return f"RD-01/RD-02 core ({lane})"

    contract = {
        "RD-00:source": (
            "candidate-source",
            "RD-00 freeze candidate source",
            ("identity.json", "candidate-source.tar", "SHA256SUMS"),
        ),
        "RD-00:harness": (
            "qualification-harnesses",
            "RD-00 freeze candidate source",
            ("qualification-harnesses.tar",),
        ),
        "RD-01:ubuntu": (
            "evidence-core-ubuntu-3.10",
            core("core-ubuntu-3.10"),
            ("core-ubuntu-3.10.xml", "coverage-core-ubuntu-3.10.xml"),
        ),
        "RD-01:windows": (
            "evidence-core-windows-3.13",
            core("core-windows-3.13"),
            ("core-windows-3.13.xml",),
        ),
        "RD-01:macos": (
            "evidence-core-macos-3.14",
            core("core-macos-3.14"),
            ("core-macos-3.14.xml",),
        ),
        "RD-02:owners": (
            "evidence-owner-lanes",
            "Require every allowlisted skip owner to pass",
            ("owner-lane-verification.json",),
        ),
        "RD-04:windows": (
            "evidence-rd-04-windows-2025",
            core("core-windows-3.13"),
            ("security-windows-2025.xml", "security-windows-2025-projection.json"),
        ),
        "RD-04:macos": (
            "evidence-rd-04-macos-15",
            "RD-04 security behavior (macos-15)",
            ("security-macos-15.xml",),
        ),
        "RD-05:windows": (
            "evidence-rd-05-windows-2025",
            core("core-windows-3.13"),
            ("product-windows-2025.xml", "product-windows-2025-projection.json"),
        ),
        "RD-06:python310": (
            "evidence-rd-06-3.10",
            "RD-06 MCP SDK (Python 3.10)",
            ("mcp-3.10.xml",),
        ),
        "RD-06:python313": (
            "evidence-rd-06-3.13",
            "RD-06 MCP SDK (Python 3.13)",
            ("mcp-3.13.xml",),
        ),
        "RD-07:toolchains": (
            "evidence-rd-07",
            "RD-07 prepared extractor toolchains",
            ("toolchains.xml",),
        ),
        "RD-08:oci": ("evidence-rd-08", "RD-08 real OCI isolation", ("oci.xml",)),
    }
    union_job = "RD-03/RD-04/RD-05 Ubuntu suites"
    contract.update(
        {
            "RD-03:slow": (
                "evidence-rd-03",
                union_job
                if layout == "union"
                else "RD-03 slow, scale, bounds, and determinism",
                ("slow.xml", "determinism.xml"),
            ),
            "RD-04:ubuntu": (
                "evidence-rd-04-ubuntu-24.04",
                union_job
                if layout == "union"
                else "RD-04 security behavior (ubuntu-24.04)",
                ("security-ubuntu-24.04.xml",),
            ),
            "RD-05:ubuntu": (
                "evidence-rd-05-ubuntu-24.04",
                union_job
                if layout == "union"
                else "RD-05 product vectors (ubuntu-24.04)",
                ("product-ubuntu-24.04.xml",),
            ),
        }
    )
    if layout == "union":
        contract["RD-03:union"] = (
            "evidence-ubuntu-suites",
            union_job,
            (
                "execution.json",
                "identity.json",
                "registry.json",
                "inventory.json",
                "observed.json",
                "started.json",
                "union.xml",
            ),
        )
    return contract


REQUIRED_JOBS = {
    "RD-09 static and dependency security",
    "RD-10 hosted composite Action",
    "RD-11 compare independent build bytes",
    "RD-12 wheel/sdist parity",
}


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def _http(url: str, token: str | None, limit: int) -> tuple[int, dict[str, str], bytes]:
    parsed = urllib.parse.urlsplit(url)
    require(
        parsed.scheme == "https"
        and bool(parsed.hostname)
        and parsed.username is None
        and parsed.password is None,
        "unsafe artifact service URL",
    )
    if token:
        require(
            parsed.hostname == "api.github.com",
            "credentials may only be sent to GitHub's API",
        )
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "agent-wiki-release-evidence",
    }
    if token:
        headers["Authorization"] = "Bearer " + token
    request = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.build_opener(_NoRedirect()).open(
            request, timeout=30
        ) as response:
            raw = response.read(limit + 1)
            require(len(raw) <= limit, "hosted response exceeds byte limit")
            return response.status, dict(response.headers.items()), raw
    except urllib.error.HTTPError as exc:
        if exc.code in {301, 302, 303, 307, 308}:
            return exc.code, dict(exc.headers.items()), b""
        # Do not expose signed download URLs or bearer credentials in logs.
        raise EvidenceError(
            f"hosted evidence service returned HTTP {exc.code}"
        ) from None
    except (urllib.error.URLError, TimeoutError, OSError):
        raise EvidenceError("hosted evidence service is unavailable") from None


class GitHub:
    def __init__(self, repository: str):
        require(
            re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository) is not None,
            "invalid repository",
        )
        self.root = f"https://api.github.com/repos/{repository}"
        self.token = os.environ.get("GITHUB_TOKEN")
        require(
            bool(self.token),
            "GITHUB_TOKEN with Actions read permission is required for producer verification",
        )

    def get(self, path: str) -> Any:
        status, _, raw = _http(self.root + path, self.token, 4 * 1024 * 1024)
        require(status == 200, "unexpected GitHub metadata response")
        return _json(raw)

    def list(self, path: str, key: str) -> list[dict]:
        rows: list[dict] = []
        for page in range(1, 11):
            value = self.get(f"{path}?per_page=100&page={page}")
            require(
                isinstance(value, dict)
                and isinstance(value.get(key), list)
                and type(value.get("total_count")) is int
                and value["total_count"] >= 0,
                "invalid paginated hosted evidence",
            )
            rows.extend(value[key])
            if len(rows) == value["total_count"]:
                return rows
            require(
                len(rows) < value["total_count"] and bool(value[key]),
                "inconsistent hosted pagination",
            )
        raise EvidenceError("hosted evidence page bound exceeded")

    def archive(self, artifact_id: int) -> bytes:
        status, headers, raw = _http(
            f"{self.root}/actions/artifacts/{artifact_id}/zip", self.token, MAX_ARCHIVE
        )
        for _ in range(4):
            if status == 200:
                return raw
            require(
                status in {301, 302, 303, 307, 308},
                "invalid artifact download response",
            )
            location = next(
                (v for k, v in headers.items() if k.lower() == "location"), ""
            )
            # Redirects use a signed URL; never forward GitHub credentials.
            status, headers, raw = _http(location, None, MAX_ARCHIVE)
        raise EvidenceError("artifact redirect bound exceeded")


def timestamp(value: Any) -> datetime:
    require(isinstance(value, str), "missing hosted timestamp")
    result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    require(result.tzinfo is not None, "hosted timestamp has no timezone")
    return result


def zip_inventory(raw: bytes) -> dict[str, str]:
    require(len(raw) <= MAX_ARCHIVE, "artifact archive exceeds byte limit")
    result = {}
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        members = archive.infolist()
        require(
            len(members) <= 10000 and sum(m.file_size for m in members) <= MAX_EXPANDED,
            "artifact expansion bound exceeded",
        )
        for member in members:
            # ZipInfo normalizes Windows separators and truncates at NUL.
            # Reject any rewritten header name before interpreting its path.
            require(
                member.orig_filename == member.filename,
                "noncanonical artifact member name",
            )
            name = (
                member.filename.removesuffix("/") if member.is_dir() else member.filename
            )
            path = PurePosixPath(name)
            require(
                bool(name)
                and path.as_posix() == name
                and not path.is_absolute()
                and ".." not in path.parts
                and "\\" not in name
                and ":" not in name,
                "unsafe artifact member",
            )
            require(
                not stat.S_ISLNK(member.external_attr >> 16),
                "artifact symlinks are forbidden",
            )
            if member.is_dir():
                continue
            require(name not in result, "duplicate artifact member")
            with archive.open(member) as stream:
                data = stream.read(MAX_EXPANDED + 1)
            require(len(data) == member.file_size, "artifact member length differs")
            result[name] = sha256(data)
    return dict(sorted(result.items()))


def verify(root: Path, identity: dict, context: dict, run_id: int) -> dict:
    """Recompute a provenance ledger from authenticated remote originals."""
    require(type(run_id) is int and run_id > 0, "invalid workflow run ID")
    require(
        isinstance(context, dict)
        and set(context) == {"run_attempt", "harness_sha256", "suite_layout"},
        "invalid qualification context",
    )
    attempt = context["run_attempt"]
    require(type(attempt) is int and attempt > 0, "invalid workflow attempt")
    require(
        isinstance(context["harness_sha256"], str)
        and re.fullmatch(r"[0-9a-f]{64}", context["harness_sha256"]) is not None,
        "invalid harness commitment",
    )
    contract = artifact_contract(context["suite_layout"])
    repository, candidate = identity["repository"], identity["source"]["sha"]
    client = GitHub(repository)
    run = client.get(f"/actions/runs/{run_id}")
    require(
        run.get("id") == run_id
        and run.get("run_attempt") == attempt
        and run.get("head_sha") == candidate
        and run.get("event") == "workflow_dispatch"
        and run.get("path", "").partition("@")[0] == WORKFLOW
        and run.get("repository", {}).get("full_name") == repository
        and run.get("head_repository", {}).get("full_name") == repository,
        "hosted run identity differs",
    )
    require(
        run.get("status") == "in_progress"
        or (run.get("status") == "completed" and run.get("conclusion") == "success"),
        "hosted run failed or is not executing qualification",
    )
    jobs = client.list(f"/actions/runs/{run_id}/attempts/{attempt}/jobs", "jobs")
    expected_jobs = {row[1] for row in contract.values()} | REQUIRED_JOBS
    producers = {}
    for name in sorted(expected_jobs):
        matches = [j for j in jobs if j.get("name") == name]
        require(len(matches) == 1, f"missing or ambiguous hosted producer: {name}")
        job = matches[0]
        require(
            job.get("status") == "completed"
            and job.get("conclusion") == "success"
            and job.get("run_id") == run_id
            and job.get("run_attempt") == attempt
            and job.get("head_sha") == candidate
            and type(job.get("id")) is int,
            f"hosted producer did not succeed for this attempt: {name}",
        )
        producers[name] = job
    artifacts = client.list(f"/actions/runs/{run_id}/artifacts", "artifacts")
    bindings = {}
    covered: set[Path] = set()
    for binding, (artifact_name, producer_name, required) in sorted(contract.items()):
        matches = [item for item in artifacts if item.get("name") == artifact_name]
        require(
            len(matches) == 1,
            f"missing or ambiguous producer artifact: {artifact_name}",
        )
        artifact, job = matches[0], producers[producer_name]
        workflow = artifact.get("workflow_run", {})
        require(
            artifact.get("expired") is False
            and type(artifact.get("id")) is int
            and workflow.get("id") == run_id
            and workflow.get("head_sha") == candidate
            and workflow.get("repository_id") == run["repository"]["id"]
            and workflow.get("head_repository_id") == run["head_repository"]["id"],
            f"artifact is expired or belongs to another candidate: {artifact_name}",
        )
        require(
            timestamp(job["started_at"])
            <= timestamp(artifact.get("created_at"))
            <= timestamp(job["completed_at"])
            and timestamp(job["started_at"])
            <= timestamp(artifact.get("updated_at"))
            <= timestamp(job["completed_at"]),
            f"artifact is outside its producer attempt: {artifact_name}",
        )
        digest = artifact.get("digest")
        require(
            isinstance(digest, str)
            and re.fullmatch(r"sha256:[0-9a-f]{64}", digest) is not None,
            "GitHub artifact digest is absent or invalid",
        )
        raw = client.archive(artifact["id"])
        require(
            "sha256:" + sha256(raw) == digest,
            f"GitHub artifact archive digest mismatch: {artifact_name}",
        )
        inventory = zip_inventory(raw)
        require(
            set(required) <= inventory.keys(),
            f"producer artifact is incomplete: {artifact_name}",
        )
        gate, label = binding.split(":")
        directory = root / "evidence" / gate / label
        require(
            directory.is_dir() and not directory.is_symlink(),
            f"missing bound evidence directory: {binding}",
        )
        files = [p for p in directory.rglob("*") if p.is_file()]
        require(
            not any(
                p.is_symlink() or any(parent.is_symlink() for parent in p.parents)
                for p in files
            ),
            "redirected evidence file",
        )
        local = {
            p.relative_to(directory).as_posix(): sha256(p.read_bytes()) for p in files
        }
        require(
            local == inventory,
            f"evidence differs from hosted artifact (including sidecars): {binding}",
        )
        covered.update(p.resolve() for p in files)
        bindings[binding] = {
            "artifact_id": artifact["id"],
            "artifact": artifact_name,
            "artifact_digest": digest,
            "producer_job_id": job["id"],
            "producer": producer_name,
            "files": inventory,
        }
    # An extra XML path cannot qualify under an unrelated generic gate label.
    for path in (root / "evidence").rglob("*"):
        if path.is_file() and path.suffix.lower() == ".xml":
            require(
                path.resolve() in covered,
                f"unbound XML evidence: {path.relative_to(root)}",
            )
    harness = root / "evidence/RD-00/harness/qualification-harnesses.tar"
    require(
        sha256(harness.read_bytes()) == context["harness_sha256"],
        "hosted harness digest differs from context",
    )
    source = root / "evidence/RD-00/source/candidate-source.tar"
    require(
        sha256(source.read_bytes()) == identity["source"]["archive_sha256"],
        "hosted source archive digest differs from identity",
    )
    return {
        "schema_version": SCHEMA,
        "repository": repository,
        "candidate_sha": candidate,
        "workflow_run_id": run_id,
        "context": context,
        "bindings": bindings,
    }
