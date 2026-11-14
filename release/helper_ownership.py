"""Exercise affected TypeScript helper consumers against the release owner declaration."""

from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import shlex
import subprocess
import sys
import tempfile

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from release import contract_canary as contracts
from release import core_shard_runner as runner
from release import core_shards, measurement_canary as canary, pr_ci as ci

LANE = {
    "darwin": "core-macos-3.14",
    "linux": "core-ubuntu-3.11",
    "win32": "core-windows-3.13",
}
WORKFLOW = ".github/workflows/release-qualification.yml"
OWNER_STEP = "Run toolchain owner suites"


def freeze(args):
    """Freeze original Git objects without requiring an unpublished version."""
    checkout = canary.safe(args.checkout)
    output = canary.safe(args.output)
    canary.require(
        not output.is_relative_to(checkout), "Put frozen inputs outside the checkout"
    )
    sha = args.source_sha
    if args.plan:
        canary.require(args.plan_sha256, "Trusted plan digest required")
        plan = ci.verify_plan(args.plan, args.plan_sha256, checkout)
        canary.require(
            plan["policy_sha256"] == ci.policy_identity(Path(ci.__file__).parent),
            "Base policy differs from the reader",
        )
        canary.require(
            plan["mode"] == "pull-request"
            and plan["candidate_sha"] == sha
            and "typescript-ownership" in plan["jobs"],
            "Conditional ownership was not selected",
        )
        canary.require(
            canary.git_output(Path(__file__).resolve().parents[1], "rev-parse", "HEAD")
            .decode()
            .strip()
            == plan["base_sha"],
            "PR ownership reader must come from the trusted base",
        )
        canary.verify_pr_source(
            checkout,
            sha,
            plan["base_sha"],
            plan["head_sha"],
            tree_sha=plan["candidate_tree"],
        )
        families = plan["typescript_families"]
        canary.require(bool(families), "Missing selected TypeScript families")
    else:
        canary.require(
            canary.git_output(checkout, "rev-parse", "HEAD").decode().strip() == sha,
            "Checkout differs from requested source",
        )
        canary.verify_tracked_source(checkout, sha)
        families = []
    output.mkdir(parents=True, exist_ok=False)
    archive = output / "candidate-source.tar"
    subprocess.run(
        [
            "git",
            "--no-replace-objects",
            "archive",
            "--format=tar",
            f"--output={archive}",
            sha,
        ],
        check=True,
        cwd=checkout,
    )
    runner.q.extract_source(
        argparse.Namespace(
            archive=archive, sha256=canary.sha(archive), destination=output / "source"
        )
    )
    version = runner.q._project_version(output / "source")
    identity = {
        "schema_version": runner.q.IDENTITY_SCHEMA,
        "repository": args.repository,
        "source": {
            "sha": sha,
            "tree": canary.git_output(checkout, "rev-parse", sha + "^{tree}")
            .decode()
            .strip(),
            "archive_sha256": canary.sha(archive),
            "commit_epoch": int(
                canary.git_output(checkout, "show", "-s", "--format=%ct", sha)
            ),
        },
        "version": version,
        "tag": "v" + version,
        "mode": "candidate",
    }
    runner.q._validate_identity(identity)
    canary.save(output, "identity.json", identity)
    canary.save(output, "families.json", families)


def owner_selectors(root):
    """Read selectors as data. Unknown collection flags need an explicit review."""
    import yaml

    jobs = yaml.safe_load(ci.bounded_file(root / WORKFLOW, ci.MAX_JSON))["jobs"]
    steps = [s for s in jobs["toolchains"]["steps"] if s.get("name") == OWNER_STEP]
    canary.require(len(steps) == 1, f"Expected one {OWNER_STEP} step")
    step = steps[0]
    canary.require(
        step.get("working-directory") == "candidate", "Owner checkout differs"
    )
    env = step.get("env", {})
    canary.require(
        env.get("LLM_WIKI_REQUIRE_NATIVE_DIAGNOSTICS") == "1"
        and env.get("LLM_WIKI_CACHE_DIR") == "${{ runner.temp }}/extractor-cache"
        and not step.get("continue-on-error")
        and "if" not in step,
        "Review the mandatory prepared toolchain owner declaration",
    )
    required = env.get("LLM_WIKI_REQUIRED_NATIVE_LANGUAGES", "")
    canary.require(
        not required or "typescript" in required.split(","), "Owner excludes TypeScript"
    )
    words = shlex.split(step["run"])
    canary.require(
        words[:3] == ["python", "-m", "pytest"], "Unsupported toolchain owner command"
    )
    options = {
        "-q",
        "--strict-config",
        "--strict-markers",
        "--durations=20",
        "--junitxml=../evidence/toolchains.xml",
    }
    pairs = {"-p": "no:cacheprovider", "-W": "error", "-o": "xfail_strict=true"}
    selectors = []
    index = 3
    while index < len(words):
        word = words[index]
        if word.startswith("tests/"):
            selectors.append(ci.selector(word))
        elif word in pairs:
            index += 1
            canary.require(
                index < len(words) and words[index] == pairs[word],
                f"Review toolchain owner option {word}",
            )
        elif word not in options:
            raise ValueError(
                f"Unrecognized toolchain owner argument {word!r} in {WORKFLOW}"
            )
        index += 1
    canary.require(bool(selectors), "Empty toolchain owner selection")
    return selectors


def collection(folder):
    observed = ci.read_json(folder / "collection.json")
    nodes = core_shards.inventory(observed["collected"])
    canary.require(
        not observed["deselected"] and Counter(observed["selected"]) == Counter(nodes),
        "Conditional family collection was reduced",
    )
    return set(nodes)


def run_cases(root, folder, selectors, env, *, collect=False):
    folder.mkdir()
    canary.save(folder, "selectors.json", sorted(selectors))
    command = [
        sys.executable,
        "-I",
        str(Path(__file__).resolve()),
        "worker",
        "--root",
        str(root),
        "--output",
        str(folder),
    ]
    if collect:
        command.append("--collect-only")
    # Durable reports can live on a Docker Desktop bind mount. Pytest's fd
    # capture truncates an unlinked tempfile, which requires a local scratch FS.
    with tempfile.TemporaryDirectory(prefix="owner-worker-") as temporary:
        scratch = Path(temporary).resolve()
        canary.require(
            not any((p / ".git").exists() for p in (scratch, *scratch.parents)),
            "Put owner worker scratch outside Git checkouts",
        )
        child = dict(
            env,
            TMPDIR=temporary,
            TMP=temporary,
            TEMP=temporary,
            RELEASE_CONTRACT_TEMP=temporary,
        )
        result = runner.invoke(command, root, child, folder / "pytest.log", timeout=600)
    canary.save(folder, "process.json", result)
    canary.require(
        not result.get("error"), f"Ownership worker failed to finish: {folder}"
    )
    nodes = collection(folder)
    canary.require(
        all(any(ci.matches(s, n) for n in nodes) for s in selectors)
        and all(any(ci.matches(s, n) for s in selectors) for n in nodes),
        "Collection differs from the requested selectors",
    )
    if collect:
        canary.require(
            result["exit_code"] == 0 and not (folder / "started.jsonl").exists(),
            "Owner selector collection failed or executed a test",
        )
        return nodes, {}
    cases = core_shards.junit(folder / "junit.xml")
    starts = [
        json.loads(row) for row in (folder / "started.jsonl").read_text().splitlines()
    ]
    canary.require(
        Counter(starts) == Counter(nodes) and set(cases) == nodes,
        "Collection, started nodes and JUnit differ",
    )
    return nodes, cases


def ownership_errors(cases, entries, lanes, owned, families=()):
    problems = []
    for node, case in sorted(cases.items()):
        skipped = case.find("skipped")
        if case.find("failure") is not None or case.find("error") is not None:
            problems.append(f"Unprepared core case failed: {node}")
        for lane in lanes:
            rows = [
                row for row in entries if row["lane"] == lane and row["node_id"] == node
            ]
            expected = (
                [] if skipped is None else [(skipped.get("message"), "toolchains")]
            )
            if [(r["reason"], r["owner_lane"]) for r in rows] != expected:
                problems.append(
                    f"release/skip-allowlist.json: {lane} {node} expected {expected!r}, observed {rows!r}"
                )
        if skipped is not None and node not in owned:
            problems.append(f"{WORKFLOW}: {OWNER_STEP} omits {node}")
    for row in entries:
        if (
            row["lane"] in lanes
            and row["node_id"] not in cases
            and any(ci.matches(s, row["node_id"]) for s in families)
        ):
            problems.append(
                f"Stale conditional node in {row['lane']}: {row['node_id']}"
            )
    return problems


def probe(args):
    root = canary.safe(args.root)
    out = canary.safe(args.output)
    canary.require(
        not out.is_relative_to(root), "Evidence must be outside frozen source"
    )
    identity = runner.q._validate_identity(ci.read_json(args.identity))
    args.root, args.expected_prefix = root, Path(sys.prefix)
    provider = contracts.verify_candidate(args)
    out.mkdir(parents=True, exist_ok=False)
    report = {
        "source_sha": identity["source"]["sha"],
        "source_tree": identity["source"]["tree"],
        "lane": LANE[sys.platform],
        "publication_authority": False,
        "status": "running",
    }
    result_path = out / "result.json"
    ci.write_json(result_path, report)
    try:
        env = runner.child_environment(out / "state", out / "tmp", args.archive)
        env["RELEASE_CONTRACT_TEMP"] = tempfile.gettempdir()
        for name in (
            "LLM_WIKI_GO",
            "LLM_WIKI_REQUIRE_NATIVE_DIAGNOSTICS",
            "LLM_WIKI_REQUIRED_NATIVE_LANGUAGES",
        ):
            env.pop(name, None)
        if args.publication_only:
            selectors = [contracts.PUBLICATION_CASE]
            nodes, cases = run_cases(root, out / "publication", selectors, env)
            canary.require(
                nodes == set(selectors)
                and all(
                    c.find(k) is None
                    for c in cases.values()
                    for k in ("failure", "error", "skipped")
                ),
                "Retained-history publication consumer failed",
            )
            canary.require(
                ci.read_json(out / "publication/process.json")["exit_code"] == 0,
                "Publication worker exited unsuccessfully",
            )
            report["passed"] = sorted(nodes)
        else:
            if args.all_families:
                inventory = {
                    p.relative_to(root).as_posix(): ci.bounded_file(p, ci.MAX_JSON)
                    for p in (root / "tests").rglob("test_*.py")
                }
                inventory["tests/conftest.py"] = ci.bounded_file(
                    root / "tests/conftest.py", ci.MAX_JSON
                )
                families = ci.typescript_families(inventory, {"tests/conftest.py"})
            else:
                families = args.family or ci.read_json(args.families_file)
            canary.require(
                isinstance(families, list) and 0 < len(families) <= ci.MAX_NODES,
                "Invalid affected families",
            )
            families = sorted({ci.selector(s) for s in families})
            files = {s.partition("::")[0] for s in families}
            declarations = owner_selectors(root)
            relevant = [s for s in declarations if s.partition("::")[0] in files]
            owner_nodes = (
                run_cases(root, out / "owner-collection", relevant, env, collect=True)[
                    0
                ]
                if relevant
                else set()
            )
            cold = out / "empty-cache"
            cold.mkdir()
            env["LLM_WIKI_CACHE_DIR"] = str(cold)
            nodes, cases = run_cases(root, out / "cold", families, env)
            owned = nodes & owner_nodes
            skipped = {n for n, c in cases.items() if c.find("skipped") is not None}
            entries = runner.q._load_skip_allowlist(
                root / "release/skip-allowlist.json"
            )
            errors = ownership_errors(
                cases, entries, [LANE[sys.platform]], owned, families
            )
            report.update(
                families=families,
                owner_selectors=relevant,
                collected=len(nodes),
                conditional_skips=sorted(skipped),
                owner_intersection=sorted(owned),
            )
            canary.require(not errors, "\n".join(errors))
            canary.require(
                ci.read_json(out / "cold/process.json")["exit_code"] == 0,
                "Cold worker failed",
            )
            env.update(
                LLM_WIKI_REQUIRE_NATIVE_DIAGNOSTICS="1",
                LLM_WIKI_REQUIRED_NATIVE_LANGUAGES="typescript",
            )
            missing = out / "missing-cache"
            missing.mkdir()
            env["LLM_WIKI_CACHE_DIR"] = str(missing)
            negative_nodes, negative = run_cases(
                root, out / "required-unprepared", families, env
            )
            failures = {
                n: failure.get("message")
                for n, c in negative.items()
                if (failure := c.find("failure")) is not None
            }
            canary.require(
                negative_nodes == nodes
                and set(failures) == skipped
                and all(
                    c.find("error") is None and c.find("skipped") is None
                    for c in negative.values()
                )
                and all(
                    message
                    == "Failed: prepared typescript helper is required in the owner lane"
                    for message in failures.values()
                )
                and ci.read_json(out / "required-unprepared/process.json")["exit_code"]
                == int(bool(skipped)),
                "Missing required helper produced unexpected outcomes",
            )
            if owned and not args.cold_only:
                cache = canary.safe(args.helper_cache_dir or out / "owner-cache")
                canary.require(
                    not cache.is_relative_to(root),
                    "Owner cache must be outside frozen source",
                )
                cache.mkdir(parents=True, exist_ok=True)
                # Readiness observations cannot establish write access under a sandbox.
                with tempfile.NamedTemporaryFile(
                    dir=cache, prefix=".owner-write-probe-"
                ):
                    pass
                env["LLM_WIKI_CACHE_DIR"] = str(cache)
                setup = runner.invoke(
                    [
                        sys.executable,
                        "-I",
                        "-m",
                        "llm_wiki_cli.cli",
                        "prepare-extractors",
                        "--language",
                        "typescript",
                        "--src-dir",
                        str(root),
                        "--cache-dir",
                        str(cache),
                    ],
                    root,
                    env,
                    out / "prepare-typescript.log",
                    timeout=600,
                )
                canary.save(out, "prepare-typescript.json", setup)
                canary.require(setup["exit_code"] == 0, "TypeScript preparation failed")
                warm_nodes, warm = run_cases(
                    root, out / "prepared-owner", sorted(owned), env
                )
                canary.require(
                    warm_nodes == owned
                    and all(
                        c.find(k) is None
                        for c in warm.values()
                        for k in ("failure", "error", "skipped")
                    )
                    and ci.read_json(out / "prepared-owner/process.json")["exit_code"]
                    == 0,
                    "Prepared owner did not pass its exact intersection",
                )
                report["prepared_passes"] = sorted(warm_nodes)
        canary.require(
            contracts.verify_candidate(args) == provider,
            "Provider changed during probe",
        )
        report["status"] = "passed"
    except (OSError, RuntimeError, ValueError, KeyError) as exc:
        report.update(status="failed", reason=str(exc))
        raise
    finally:
        ci.write_json(result_path, report)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="operation", required=True)
    src = commands.add_parser("freeze")
    src.add_argument("--checkout", type=Path, required=True)
    src.add_argument("--source-sha", required=True)
    src.add_argument("--repository", required=True)
    src.add_argument("--output", type=Path, required=True)
    src.add_argument("--plan", type=Path)
    src.add_argument("--plan-sha256")
    run = commands.add_parser("probe")
    for name in ("root", "archive", "identity", "output"):
        run.add_argument("--" + name, type=Path, required=True)
    run.add_argument("--source-sha", required=True)
    modes = run.add_mutually_exclusive_group(required=True)
    modes.add_argument("--family", action="append")
    modes.add_argument("--families-file", type=Path)
    modes.add_argument("--all-families", action="store_true")
    modes.add_argument("--publication-only", action="store_true")
    run.add_argument("--helper-cache-dir", type=Path)
    run.add_argument("--cold-only", action="store_true")
    worker = commands.add_parser("worker")
    worker.add_argument("--root", type=Path, required=True)
    worker.add_argument("--output", type=Path, required=True)
    worker.add_argument("--collect-only", action="store_true")
    args = parser.parse_args()
    if args.operation == "freeze":
        freeze(args)
    elif args.operation == "probe":
        args.archive = canary.safe(args.archive)
        probe(args)
    else:
        return contracts.execute_tests(
            args.root,
            ci.read_json(args.output / "selectors.json"),
            args.output,
            collect_only=args.collect_only,
            installed_only=True,
        )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, RuntimeError, KeyError) as error:
        print(str(error), file=sys.stderr)
        raise SystemExit(2)
