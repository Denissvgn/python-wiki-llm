"""Read-only admission before expensive release verification.

An observation of a local capability or an available interpreter download is
not native execution evidence, policy approval, qualification or publication.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import importlib.util
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys
import urllib.parse
import urllib.request

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).absolute().parent.parent))

SCHEMA = "agent-wiki-release-readiness/v1"
CONTRACT = "release/runtime-policy.json"
MANIFEST_URL = "https://raw.githubusercontent.com/actions/python-versions/main/versions-manifest.json"
MAX_MANIFEST = 2 * 1024 * 1024
LOCAL_STAGES = ("contracts", "static", "freeze", "host-core", "builds", "artifacts")
LANGUAGES = ("typescript", "go", "rust", "haskell")
# Local static checks use the project launcher directly. These top-level
# packages cover its explicit environment guard and the declared Pyright
# surface (including examples); their presence establishes no SDK/native proof.
STATIC_MODULES = {
    "pytest",
    "tokenizers",
    "mcp",
    "fastapi",
    "tomli",
    "markdown_it",
    "jsonschema",
    "pyright",
    "ruff",
    "bandit",
    "pip_audit",
}
QUALIFICATION_WORKFLOW = ".github/workflows/release-qualification.yml"
# Role locations are independent coverage expectations. Interpreter versions
# live only in the runtime policy; that policy cannot relabel a different job
# as an existing owner and silently leave the real consumer unchecked.
REQUIRED_CONSUMERS = {
    "capture": ("knowledge-linux", ".github/workflows/reviewed-wiki-capture.yml", "capture", "setup-python"),
    "integrity": ("knowledge-linux", "integrations/wiki-integrity/action.yml", None, "setup-python"),
    "rd10": ("knowledge-linux", QUALIFICATION_WORKFLOW, "action", "setup-python"),
    "artifact-smoke": ("knowledge-linux", QUALIFICATION_WORKFLOW, "artifact-smoke", "setup-python"),
    "readiness": ("knowledge-linux", QUALIFICATION_WORKFLOW, "readiness", "setup-python"),
    "windows-plan": ("windows-core", QUALIFICATION_WORKFLOW, "core-windows-plan", "setup-python"),
    "windows-canary": ("windows-core", QUALIFICATION_WORKFLOW, "windows-canary", "setup-python"),
    "windows-native": ("windows-core", QUALIFICATION_WORKFLOW, "windows-native", "setup-python"),
    "windows-probe": ("windows-probe", ".github/workflows/windows-measurement.yml", "measurement", "matrix-python"),
}
RUNNER_PROFILES = {
    "ubuntu-24.04": ("linux", "x64", "24.04"),
    "windows-2025": ("win32", "x64", None),
}


class ReadinessError(ValueError):
    """A required capability or declaration cannot be established."""


def literal_false(value) -> bool:
    # The bounded YAML observer preserves scalar lexemes as strings.
    return value is False or isinstance(value, str) and value.strip().lower() == "false"


def strict_json(raw: bytes):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ReadinessError("Duplicate JSON field: " + key)
            result[key] = value
        return result

    def invalid(value):
        raise ReadinessError("Nonfinite JSON value: " + value)

    try:
        return json.loads(
            raw.decode("utf-8"), object_pairs_hook=pairs, parse_constant=invalid
        )
    except RecursionError as error:
        raise ReadinessError("Readiness document exceeds its nesting bound") from error


def safe_path(path: Path) -> Path:
    # Inputs may be in an ignored review folder, but no symlink/reparse alias
    # may choose a different contract, cache or availability document.
    path = Path(os.path.abspath(path))
    for p in (*reversed(path.parents), path):
        if p.is_symlink() or (
            p.exists() and getattr(p.lstat(), "st_file_attributes", 0) & 0x400
        ):
            raise ReadinessError("Redirected readiness input: " + str(p))
    return path


def bounded_read(path: Path, limit: int) -> bytes:
    path = safe_path(path)
    before = path.lstat()
    if not path.is_file() or before.st_nlink != 1 or before.st_size > limit:
        raise ReadinessError("Readiness input is absent or oversized: " + str(path))
    with path.open("rb") as stream:
        raw = stream.read(limit + 1)
    if len(raw) > limit:
        raise ReadinessError("Readiness input exceeds byte bound")
    after = path.lstat()
    if (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns) != (
        after.st_dev,
        after.st_ino,
        after.st_size,
        after.st_mtime_ns,
    ):
        raise ReadinessError("Readiness input changed during read")
    return raw


def helper_cache_base(root: Path) -> Path:
    """Use the same base as native test consumers; application adds its suffix."""
    configured = os.environ.get("LLM_WIKI_CACHE_DIR")
    return safe_path(
        Path(os.path.abspath(Path(configured).expanduser()))
        if configured
        else root / ".git/llm-wiki-extractors"
    )


def python_manifest(path: Path | None = None):
    if path is not None:
        raw = bounded_read(path, MAX_MANIFEST)
        origin = "provided-official-manifest"
    else:
        request = urllib.request.Request(
            MANIFEST_URL, headers={"User-Agent": "agent-wiki-release-readiness"}
        )
        with urllib.request.urlopen(request, timeout=20) as response:
            if response.geturl() != MANIFEST_URL:
                raise ReadinessError("Unexpected Python manifest redirect")
            raw = response.read(MAX_MANIFEST + 1)
        origin = MANIFEST_URL
    if len(raw) > MAX_MANIFEST:
        raise ReadinessError("Python manifest exceeds byte bound")
    rows = strict_json(raw)
    if not isinstance(rows, list) or not 0 < len(rows) <= 10000:
        raise ReadinessError("Python manifest must be a bounded nonempty array")
    return rows, {
        "origin": origin,
        "sha256": hashlib.sha256(raw).hexdigest(),
        "bytes": len(raw),
    }


def availability(profiles: dict, rows: list) -> list[dict]:
    result = []
    for name, profile in sorted(profiles.items()):
        for version in profile["python"]:
            releases = [
                r for r in rows if isinstance(r, dict) and r.get("version") == version
            ]
            files = releases[0].get("files") if len(releases) == 1 else None
            matching = []
            if isinstance(files, list) and releases[0].get("stable") is True:
                for item in files:
                    if not isinstance(item, dict) or (
                        item.get("platform"),
                        item.get("arch"),
                    ) != (profile["platform"], profile["arch"]):
                        continue
                    if (
                        profile["platform_version"] is not None
                        and item.get("platform_version") != profile["platform_version"]
                    ):
                        continue
                    url = urllib.parse.urlsplit(str(item.get("download_url", "")))
                    if (
                        url.scheme == "https"
                        and url.netloc == "github.com"
                        and url.path.startswith(
                            "/actions/python-versions/releases/download/"
                        )
                    ):
                        matching.append(item)
            result.append(
                {
                    "profile": name,
                    "python": version,
                    "platform": profile["platform"],
                    "arch": profile["arch"],
                    "status": "available" if matching else "unavailable",
                    "downloads": matching,
                }
            )
    return result


def provider_observation(root: Path) -> dict:
    """Same-version stale installations must not supply preparation evidence."""
    import llm_wiki_cli
    from release.measurement_canary import provider_files

    expected = provider_files(root)
    package = safe_path(Path(llm_wiki_cli.__file__).absolute().parent)
    allowed = package == root / "src/llm_wiki_cli" or package.is_relative_to(
        Path(sys.prefix).resolve()
    )
    if not allowed:
        raise ReadinessError(
            "Provider origin is outside the candidate or project environment"
        )
    observed = {}
    total = 0
    for path in sorted(package.rglob("*")):
        safe_path(path)
        if (
            path.is_file()
            and "__pycache__" not in path.relative_to(package).parts
            and path.suffix != ".pyc"
        ):
            raw = bounded_read(path, 64 * 1024 * 1024)
            total += len(raw)
            if total > 256 * 1024 * 1024 or len(observed) >= 10000:
                raise ReadinessError("Provider namespace exceeds bound")
            observed[path.relative_to(package).as_posix()] = hashlib.sha256(
                raw
            ).hexdigest()
    version = importlib.metadata.version("agent-wiki-cli")
    if observed != expected["files"] or version != expected["version"]:
        raise ReadinessError(
            "Installed provider version or complete namespace differs from candidate source"
        )
    return {
        "origin": str(package),
        "version": version,
        "files": len(observed),
        "namespace_sha256": hashlib.sha256(
            json.dumps(observed, sort_keys=True).encode()
        ).hexdigest(),
    }


def runtime_contract(
    root: Path, *, check_availability=False, manifest: Path | None = None
) -> dict:
    from llm_wiki_cli.services.yaml_syntax import load_yaml_documents

    blockers, pending, inputs, observed = [], [], {}, []
    raw = bounded_read(root / CONTRACT, 1024 * 1024)
    contract = strict_json(raw)
    if (
        not isinstance(contract, dict)
        or set(contract) != {"schema_version", "profiles", "consumers"}
        or contract["schema_version"] != "agent-wiki-runtime-contract/v1"
    ):
        raise ReadinessError("Unsupported runtime contract")
    profiles, consumers = contract["profiles"], contract["consumers"]
    if (
        not isinstance(profiles, dict)
        or set(profiles) != {"knowledge-linux", "windows-core", "windows-probe"}
        or not isinstance(consumers, list)
    ):
        raise ReadinessError("Invalid runtime profiles/consumers")
    for name, p in profiles.items():
        if (
            not isinstance(name, str)
            or not isinstance(p, dict)
            or set(p) != {"platform", "arch", "platform_version", "python"}
            or p["platform"] not in {"linux", "win32", "darwin"}
            or p["arch"] not in {"x64", "arm64"}
            or p["platform_version"] is not None
            and not isinstance(p["platform_version"], str)
            or not isinstance(p["python"], list)
            or not 0 < len(p["python"]) <= 3
            or len(set(p["python"])) != len(p["python"])
            or any(
                not isinstance(v, str) or not re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", v)
                for v in p["python"]
            )
        ):
            raise ReadinessError(
                "Runtime profile requires exact platform/interpreter versions"
            )
    if (
        len(profiles["knowledge-linux"]["python"]) != 1
        or len(profiles["windows-core"]["python"]) != 1
        or not set(profiles["windows-core"]["python"])
        <= set(profiles["windows-probe"]["python"])
    ):
        raise ReadinessError(
            "Single execution runtimes and their native probe coverage must agree"
        )
    ids = [c.get("id") for c in consumers if isinstance(c, dict)]
    if (
        len(ids) != len(consumers)
        or len(ids) != len(set(ids))
        or set(ids) != set(REQUIRED_CONSUMERS)
    ):
        raise ReadinessError("Runtime contract omits or duplicates a required consumer")
    documents, bindings = {}, set()
    for consumer in consumers:
        if (
            set(consumer) != {"id", "profile", "path", "job", "selection"}
            or tuple(consumer[field] for field in ("profile", "path", "job", "selection"))
            != REQUIRED_CONSUMERS[consumer["id"]]
        ):
            raise ReadinessError("Runtime consumer binding differs from its canonical owner: " + str(consumer.get("id")))
        binding = (consumer["path"], consumer["job"], consumer["selection"])
        if binding in bindings:
            raise ReadinessError("Runtime consumers duplicate a physical owner")
        bindings.add(binding)
        name = consumer["path"]
        path = PurePosixPath(name)
        if (
            path.is_absolute()
            or path.as_posix() != name
            or ".." in path.parts
            or "\\" in name
            or not name.endswith(".yml")
        ):
            raise ReadinessError("Invalid runtime declaration path")
        try:
            if name not in documents:
                data = bounded_read(root / name, 1024 * 1024)
                inputs[name] = hashlib.sha256(data).hexdigest()
                values, issues = load_yaml_documents(data.decode("utf-8"))
                if issues or len(values) != 1 or not isinstance(values[0], dict):
                    raise ReadinessError("Invalid runtime declaration YAML")
                documents[name] = values[0]
            document = documents[name]
            job = (
                document.get("jobs", {}).get(consumer["job"])
                if consumer["job"] is not None
                else document.get("runs")
            )
            if not isinstance(job, dict):
                raise ReadinessError("Runtime owner is missing")
            if "if" in job:
                condition = job["if"]
                token = condition.strip() if isinstance(condition, str) else None
                if token is not None and token.startswith("${{") and token.endswith("}}"):
                    token = token[3:-2].strip()
                if condition is False or not isinstance(condition, (str, bool)) or (
                    isinstance(condition, str)
                    and (
                        not token
                        or token.lower() in {"false", "null", "0"}
                        or token in {"''", '""'}
                    )
                ):
                    raise ReadinessError("Required runtime owner has a disabled or unsupported job predicate")
            if not literal_false(job.get("continue-on-error", False)):
                raise ReadinessError("Required runtime owner cannot soft-fail")
            expected_profile = profiles[consumer["profile"]]
            if consumer["job"] is not None:
                declared_runner = job.get("runs-on")
                runner = RUNNER_PROFILES.get(
                    declared_runner if isinstance(declared_runner, str) else ""
                )
                if runner != (
                    expected_profile["platform"],
                    expected_profile["arch"],
                    expected_profile["platform_version"],
                ):
                    raise ReadinessError(
                        "Runtime owner runner differs from its OS/release/architecture profile"
                    )
            setups = [
                s
                for s in job.get("steps", [])
                if isinstance(s, dict)
                and str(s.get("uses", "")).startswith("actions/setup-python@")
            ]
            if len(setups) != 1 or "if" in setups[0]:
                raise ReadinessError(
                    "Runtime owner needs one unconditional interpreter setup"
                )
            if not literal_false(setups[0].get("continue-on-error", False)):
                raise ReadinessError("Required interpreter setup cannot soft-fail")
            architecture = setups[0].get("with", {}).get("architecture")
            if architecture is not None and architecture != expected_profile["arch"]:
                raise ReadinessError(
                    "Interpreter architecture differs from runtime profile"
                )
            if consumer["selection"] == "matrix-python":
                matrix = job.get("strategy", {}).get("matrix")
                if not isinstance(matrix, dict) or set(matrix) != {"python"}:
                    raise ReadinessError(
                        "Runtime Python matrix must contain only its declared axis without include/exclude"
                    )
                actual = matrix["python"]
                if (
                    setups[0].get("with", {}).get("python-version")
                    != "${{ matrix.python }}"
                ):
                    raise ReadinessError(
                        "Runtime setup does not consume the declared Python matrix"
                    )
            elif consumer["selection"] == "setup-python":
                actual = [setups[0].get("with", {}).get("python-version")]
            else:
                raise ReadinessError("Unsupported runtime selection")
            expected = profiles[consumer["profile"]]["python"]
            if actual != expected:
                raise ReadinessError(
                    "Interpreter declaration differs from purpose/platform contract"
                )
            observed.append(
                {
                    "id": consumer["id"],
                    "profile": consumer["profile"],
                    "status": "ready",
                    "python": actual,
                }
            )
        except (ValueError, OSError, AttributeError, TypeError) as error:
            blockers.append(
                {
                    "id": "runtime-owner:" + consumer["id"],
                    "reason": str(error),
                    "path": name,
                }
            )
    availability_rows, manifest_identity = [], None
    if check_availability or manifest is not None:
        try:
            rows, manifest_identity = python_manifest(manifest)
            availability_rows = availability(profiles, rows)
            blockers.extend(
                {
                    "id": "python-download:" + r["profile"] + ":" + r["python"],
                    "reason": "Exact interpreter is unavailable for the selected OS/architecture",
                }
                for r in availability_rows
                if r["status"] != "available"
            )
        except (OSError, ValueError, TimeoutError) as error:
            blockers.append({"id": "python-availability", "reason": str(error)[:500]})
    else:
        pending.append(
            {
                "id": "python-availability",
                "reason": "Interpreter download availability has not been observed; use --check-availability or a retained official manifest",
            }
        )
    return {
        "contract_sha256": hashlib.sha256(raw).hexdigest(),
        "inputs": inputs,
        "profiles": profiles,
        "consumers": observed,
        "availability": availability_rows,
        "manifest": manifest_identity,
        "blockers": blockers,
        "hosted_pending": pending,
    }


def capabilities(
    root: Path,
    *,
    stages=LOCAL_STAGES,
    environment=None,
    helper=None,
    native_languages=None,
) -> dict:
    from release import preflight
    from llm_wiki_cli.services import extractor_helpers as helpers

    stages = tuple(stages)
    if (
        not stages
        or any(s not in LOCAL_STAGES for s in stages)
        or len(stages) != len(set(stages))
    ):
        raise ReadinessError("Invalid selected local stages")
    environment = (
        environment if environment is not None else preflight._environment(root)
    )
    helper = helper if helper is not None else preflight._helper(root, environment)
    rows, blockers, pending = [], [], []
    if native_languages is None:
        declared = {
            n.strip()
            for n in os.environ.get("LLM_WIKI_REQUIRED_NATIVE_LANGUAGES", "").split(",")
            if n.strip()
        }
        native_languages = (
            (declared or set(LANGUAGES))
            if os.environ.get("LLM_WIKI_REQUIRE_NATIVE_DIAGNOSTICS") == "1"
            else set()
        )
    else:
        native_languages = set(native_languages)
    if set(native_languages) - set(LANGUAGES):
        raise ReadinessError("Unsupported required native language")
    required = (
        set(native_languages) if set(stages) & {"contracts", "host-core"} else set()
    )
    if "contracts" in stages:
        required.add("typescript")
    required_tools = (
        {"node", "npm"} if set(stages) & {"contracts", "host-core"} else set()
    )
    required_tools.update({"go"} if "go" in required else set())
    required_tools.update({"rust", "cargo"} if "rust" in required else set())
    required_tools.update({"haskell"} if "haskell" in required else set())
    if "static" in stages:
        required_tools.add("actionlint")
    if set(stages) & {"contracts", "static", "host-core"}:
        try:
            observation = provider_observation(root)
            rows.append(
                {"id": "provider", "status": "ready", "required": True, **observation}
            )
        except (ImportError, OSError, ValueError, KeyError) as error:
            blockers.append(
                {
                    "id": "provider",
                    "reason": str(error)[:500],
                    "remedy": "Install the exact candidate into the project virtual environment before preparing helpers or rehearsing",
                }
            )
    lock = strict_json(bounded_read(root / "release/toolchain-lock.json", 1024 * 1024))
    if not isinstance(lock, dict) or not isinstance(lock.get("toolchains"), dict):
        raise ReadinessError("Toolchain lock is unavailable")
    locked = lock["toolchains"]
    for tool in sorted(required_tools):
        observation = environment.get("tools", {}).get(tool, {})
        declaration = locked.get("rust" if tool == "cargo" else tool, {})
        if tool == "actionlint":
            declaration = lock.get("qualification_tools", {}).get("actionlint", {})
        expected = (
            "rustc " + locked["rust"]["version"]
            if tool == "rust"
            else declaration.get("version_output")
        )
        actual = observation.get("version")
        observed = (
            actual.splitlines()[0] if isinstance(actual, str) and actual else None
        )
        ready = (
            observation.get("status") == "observed"
            and expected is not None
            and (
                observed == expected
                or tool in {"go", "rust"}
                and isinstance(observed, str)
                and observed.startswith(expected + " ")
            )
        )
        row = {
            "id": "tool:" + tool,
            "status": "ready" if ready else "unavailable",
            "required": True,
            "observed": observation.get("version"),
            "expected": expected,
            "path": observation.get("path"),
        }
        rows.append(row)
        if not ready:
            blockers.append(
                {
                    "id": row["id"],
                    "reason": "Required tool is missing or differs from the lock",
                    "remedy": "Prepare/select the declared tool before rehearsal",
                }
            )
    modules = (
        {"pytest", "tokenizers"} if set(stages) & {"contracts", "host-core"} else set()
    )
    if "static" in stages:
        modules.update(STATIC_MODULES)
    for module in sorted(modules):
        ready = importlib.util.find_spec(module) is not None
        rows.append(
            {
                "id": "module:" + module,
                "status": "ready" if ready else "unavailable",
                "required": True,
            }
        )
        if not ready:
            blockers.append(
                {
                    "id": "module:" + module,
                    "reason": "Selected-stage Python dependency is unavailable",
                    "remedy": "Install the maintained development/validation dependency profile into the project virtual environment",
                }
            )
    base = helper_cache_base(root)
    cache = helpers.resolve_helper_cache_root(root, str(base))
    for language in LANGUAGES:
        if language == "typescript":
            ready = helper.get("status") == "ready"
        else:
            ready = helpers.get_prepared_binary(language, root, str(base)) is not None
        row = {
            "id": "helper:" + language,
            "status": "ready" if ready else "unavailable",
            "required": language in required,
            "cache_base": str(base),
            "cache_root": str(cache) if cache else None,
        }
        rows.append(row)
        if not ready:
            issue = {
                "id": row["id"],
                "reason": "Prepared source/platform-matching helper is unavailable in the selected cache base",
                "remedy": "Run explicit prepare-extractors for this language with --cache-dir "
                + str(base),
            }
            (blockers if row["required"] else pending).append(issue)
    return {
        "selected_stages": list(stages),
        "cache_base": str(base),
        "capabilities": rows,
        "blockers": blockers,
        "hosted_pending": pending,
    }


def inspect(
    root: Path,
    *,
    stages=LOCAL_STAGES,
    check_availability=False,
    python_manifest=None,
    runtime_only=False,
    environment=None,
    helper=None,
    native_languages=None,
) -> dict:
    root = Path(os.path.abspath(root))
    result = {
        "schema_version": SCHEMA,
        "root": str(root),
        "status": "blocked",
        "blockers": [],
        "hosted_pending": [],
        "runtime_contract": None,
        "capabilities": None,
        "target_execution_verified": False,
        "publication_authority": False,
    }
    try:
        runtime = runtime_contract(
            root, check_availability=check_availability, manifest=python_manifest
        )
        result["runtime_contract"] = runtime
        result["blockers"].extend(runtime["blockers"])
        result["hosted_pending"].extend(runtime["hosted_pending"])
    except (ImportError, OSError, ValueError, TypeError) as error:
        result["blockers"].append(
            {"id": "runtime-contract", "reason": str(error)[:500]}
        )
    if not runtime_only:
        try:
            local = capabilities(
                root,
                stages=stages,
                environment=environment,
                helper=helper,
                native_languages=native_languages,
            )
            result["capabilities"] = local
            result["blockers"].extend(local["blockers"])
            result["hosted_pending"].extend(local["hosted_pending"])
        except (ImportError, OSError, ValueError, TypeError) as error:
            result["blockers"].append(
                {"id": "local-capabilities", "reason": str(error)[:500]}
            )
    result["status"] = (
        "blocked"
        if result["blockers"]
        else "hosted-required"
        if result["hosted_pending"]
        else "ready"
    )
    return result


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    probe = commands.add_parser("inspect")
    probe.add_argument("--root", type=Path, default=Path.cwd())
    probe.add_argument("--output", type=Path, required=True)
    probe.add_argument("--stage", action="append", choices=LOCAL_STAGES)
    probe.add_argument("--runtime-only", action="store_true")
    availability_options = probe.add_mutually_exclusive_group()
    availability_options.add_argument("--check-availability", action="store_true")
    availability_options.add_argument("--python-manifest", type=Path)
    args = parser.parse_args(argv)
    result = inspect(
        args.root,
        stages=tuple(args.stage or LOCAL_STAGES),
        check_availability=args.check_availability,
        python_manifest=args.python_manifest,
        runtime_only=args.runtime_only,
    )
    try:
        write_report(args.output, result, root=args.root)
    except (OSError, ValueError) as error:
        print(str(error), file=sys.stderr)
        return 2
    print(
        json.dumps(
            {
                "status": result["status"],
                "blockers": result["blockers"],
                "hosted_pending": result["hosted_pending"],
            },
            sort_keys=True,
        )
    )
    return 0 if result["status"] == "ready" else 2 if result["blockers"] else 3


def write_report(path: Path, result: dict, *, root: Path) -> None:
    path, root = safe_path(path), Path(os.path.abspath(root))
    if path.is_relative_to(root):
        checked = subprocess.run(
            ["git", "check-ignore", "--quiet", "--", str(path)],
            cwd=root,
            stdin=subprocess.DEVNULL,
            capture_output=True,
        )
        if checked.returncode != 0:
            raise ReadinessError("Readiness output inside source must be ignored")
    data = (
        json.dumps(result, indent=2, sort_keys=True, allow_nan=False).encode("utf-8")
        + b"\n"
    )
    if len(data) > MAX_MANIFEST:
        raise ReadinessError("Readiness report exceeds byte bound")
    path.parent.mkdir(parents=True, exist_ok=True)
    safe_path(path)
    with path.open("xb") as stream:
        stream.write(data)


if __name__ == "__main__":
    raise SystemExit(main())
