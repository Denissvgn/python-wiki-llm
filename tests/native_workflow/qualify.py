"""Run independent controls on owned fixtures, never general target workloads."""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

from tests.native_workflow.oracles import observe_owned_retry_patch, source_facts, verify_corpus
from tests.provider_conformance.frontends import Frontends
from tests.provider_conformance.model import Incomplete


def run_controls(config, work, runtime_python, provider_helpers=None):
    root = Path(__file__).parent
    manifest = verify_corpus(root)
    frontends = Frontends(config, work / "frontends")
    results = {}
    executions = []

    def variant(task, name, updates):
        destination = work / task / name
        shutil.copytree(root / "fixtures" / task / "project", destination)
        for filename, text in updates.items():
            path = destination / filename
            if text is None:
                path.unlink()
            else:
                path.write_text(text, encoding="utf-8")
        return destination

    def execute(arguments, cwd):
        outcome = subprocess.run([str(arg) for arg in arguments], cwd=cwd, env=frontends.environment,
                                 capture_output=True, text=True, timeout=120)
        record = {"process_exit": outcome.returncode, "stdout": outcome.stdout,
                  "stderr": outcome.stderr, "argv": [str(arg) for arg in arguments]}
        executions.append(record)
        (work / "executions.json").write_text(json.dumps(executions, indent=2) + "\n")
        return record

    # Python behavior: successful process/compilation do not imply a correct patch.
    retry = (root / "fixtures/T01/project/retry.py").read_text()
    positive = variant("T01", "correct", {"retry.py": retry.replace("range(attempts - 1)", "range(attempts)").replace("attempts - 2", "attempts - 1")})
    negative = variant("T01", "wrong", {"retry.py": retry.replace("attempts: int = 3", "attempts: int = 4")})
    results["T01"] = {"positive": observe_owned_retry_patch(positive), "negative": observe_owned_retry_patch(negative)}
    assert results["T01"]["positive"]["oracle_passed"]
    assert not results["T01"]["negative"]["oracle_passed"]
    assert results["T01"]["negative"]["compiled"] and results["T01"]["negative"]["process_exit"] == 0

    # TypeScript source observer and a separate, deliberately owned VM behavior control.
    ts_source = (root / "fixtures/T02/project/options.ts").read_text()
    correct_ts = ts_source.replace("timeout: number;", "timeout?: number;").replace("return options.timeout;", "return options.timeout ?? 30;")
    wrong_ts = correct_ts.replace("?? 30", "|| 30")
    client = 'import { timeout } from "./options";\nexport const value = timeout({});\n'
    ts_results = {}
    script = root / "typescript_oracle.cjs"
    for name, text in (("correct", correct_ts), ("wrong", wrong_ts)):
        project = variant("T02", name, {"options.ts": text, "client.ts": client})
        observed = frontends.observe(project / "options.ts")
        attribute = next(record for record in observed["declarations"] if record["kind"] == "attribute")
        assert attribute["owner"] == "Options" and attribute["optional"] is True and "default" not in attribute
        process = execute([config["node"], script, config["typescript_module"], project], project)
        assert process["process_exit"] == 0
        verdict = json.loads(process["stdout"])
        assert verdict["compiled"] and verdict["oracle_passed"] is (name == "correct")
        ts_results[name] = {"observation": observed, "execution": process, "verdict": verdict}
    results["T02"] = ts_results

    # FastAPI source facts are AST-only. Runtime schema generation is a separate
    # owned-fixture action in an explicitly prepared environment.
    app = (root / "fixtures/T03/project/app.py").read_text()
    fastapi_script = '''import importlib.util,json,sys
spec=importlib.util.spec_from_file_location("owned_fixture",sys.argv[1]); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
operation=m.app.openapi()["paths"]["/items"]["get"]
parameters=operation.get("parameters",[])
passed=any(p["name"]=="limit" and p["in"]=="query" and p.get("required") is False and p["schema"].get("default")==20 for p in parameters)
print(json.dumps({"oracle_passed":passed,"operation":operation}))
'''
    for name, text in (("correct", app.replace("def list_items():", "def list_items(limit: int = 20):")),
                       ("wrong", app + "\ndef unrelated(limit: int = 20):\n    return limit\n")):
        project = variant("T03", name, {"app.py": text})
        observed = source_facts(project / "app.py")
        ast.parse(text)
        process = execute([runtime_python, "-I", "-c", fastapi_script, project / "app.py"], project)
        assert process["process_exit"] == 0
        verdict = json.loads(process["stdout"])
        assert verdict["oracle_passed"] is (name == "correct")
        results[f"T03/{name}"] = {"compiled": True, "observation": observed, "execution": process, "verdict": verdict}

    # Receiver and callback ownership stay parse-only observations. The separate
    # owned runtime checks one explicitly chosen callback; it cannot resolve all calls.
    go_source = (root / "fixtures/T04/project/store.go").read_text()
    changed_go = go_source.replace("Handle(value string)", "Handle(prefix string, value string)")
    go_oracle = 'package hooks\nimport "testing"\nfunc TestPrefix(t *testing.T) { s := &Store{Hook: func(v string) string { return v }}; if s.Handle("p:", "x") != "p:x" { t.Fatal("prefix lost") } }\n'
    for name, text in (("correct", changed_go.replace("s.Hook(value)", "s.Hook(prefix + value)")), ("wrong", changed_go)):
        project = variant("T04", name, {"store.go": text, "oracle_test.go": go_oracle})
        observed = frontends.observe(project / "store.go")
        handler = next(record for record in observed["declarations"] if record["kind"] == "method")
        assert handler["owner"] == "Store" and [p["name"] for p in handler["params"]] == ["prefix", "value"]
        process = execute([config["go"], "test", "-json", "."], project)
        assert process["process_exit"] == (0 if name == "correct" else 1)
        assert '"Action":"run"' in process["stdout"]  # the negative compiles and reaches behavior
        results[f"T04/{name}"] = {"compiled": True, "observation": observed, "execution": process,
                                   "oracle_passed": name == "correct", "static_callback_resolution": "unresolved"}

    # Moving a declaration is insufficient without its consumer and durable link.
    for name, fix_client in (("correct", True), ("wrong", False)):
        client_text = (root / "fixtures/T05/project/client.py").read_text()
        if fix_client:
            client_text = client_text.replace("from models import", "from account import")
        project = variant("T05", name, {"models.py": None, "account.py": "class Account:\n    name: str\n",
            "client.py": client_text, "wiki/index.md": "# Guide\n[Account](../account.py)\n"})
        declared = source_facts(project / "account.py")["declarations"]
        imports = source_facts(project / "client.py")["imports"]
        passed = declared[0]["name"] == "Account" and imports[0]["module"] == "account"
        assert passed is fix_client
        results[f"T05/{name}"] = {"compiled": True, "oracle_passed": passed, "observed_import": imports}

    rust_source = (root / "fixtures/T06/project/lib.rs").read_text()
    for name, target_type in (("correct", "Option<u32>"), ("wrong", "Option<u64>")):
        project = variant("T06", name, {"lib.rs": rust_source.replace("timeout: u32", "timeout: " + target_type)})
        observed = frontends.observe(project / "lib.rs")
        field = next(record for record in observed["declarations"] if record["kind"] == "attribute")
        passed = field["owner"] == "Request" and frontends.normalize("rust", "type", field["type"]) == frontends.normalize("rust", "type", "Option<u32>")
        process = execute([Path(config["cargo"]).with_name("rustc"), "--crate-type", "lib", "--emit", "metadata",
                           "lib.rs", "-o", "owned.rmeta"], project)
        assert process["process_exit"] == 0 and passed is (name == "correct")
        results[f"T06/{name}"] = {"compiled": True, "oracle_passed": passed, "observation": observed,
                                   "execution": process, "observer_cfg_macros_evaluated": False}

    haskell = root / "fixtures/T07/project/Apply.hs"
    observed = frontends.observe(haskell)
    signature = next(record["signature"] for record in observed["declarations"] if "signature" in record)
    assert frontends.normalize("haskell", "type", signature) != frontends.normalize("haskell", "type", "a -> b -> a -> b")
    try:
        frontends.observe(root / "fixtures/T07/project/Raw.hs")
    except Incomplete as exc:
        assert "parse error" in str(exc) and "haskell" in frontends.identities
        results["T07"] = {"grouping_preserved": True, "raw_cpp": "expected-unsupported", "observer": observed,
                          "cpp_executed": False, "reason": str(exc)}
    else:
        raise AssertionError("Raw CPP was accepted")

    if provider_helpers is not None:
        from llm_wiki_cli import api

        checks = (("T02", "options.ts:Options", "interface"), ("T04", "store.go:Store.Handle", "method"),
                  ("T06", "lib.rs:Request", "struct"), ("T07", "Apply.hs:apply#1", "signature"))
        for case, selector, expected_kind in checks:
            request = {"schema_version": "llm-wiki-task-request/v1", "requirements": [
                {"id": "contract", "facet": "source-contract", "selector": selector}]}
            context = api.build_task_context(request, src_dir=str((root / "fixtures" / case / "project").resolve()),
                wiki_dir=str(work / case / "absent-wiki"), helper_cache_dir=str(provider_helpers))
            payload = api.validate_task_context(context.rendered, request)
            assert payload["coverage"][0]["satisfied"]
            fact = payload["facts"][0]["observation"]
            assert fact["kind"] == expected_kind, "declaration kind was lost at task composition"
            if case == "T02":
                assert fact["contract"]["attributes"][0]["optional"] is False
            elif case == "T04":
                assert fact["owner"] == "Store" and fact["contract"]["calls"][0]["attr"] == "s.Hook"
            elif case == "T06":
                assert fact["contract"]["attributes"][0]["type"] == "u32"
            else:
                assert fact["contract"]["signature"] == "(a -> b) -> a -> b"
            results[f"{case}/task-context"] = {"request": request, "result_id": context.result_id,
                                               "observation": fact, "independent_kind": expected_kind}

    return {"schema_version": "native-workflow-owned-oracles/v1", "status": "pass", "tasks": results,
            "corpus_sha256": hashlib.sha256((root / "corpus.json").read_bytes()).hexdigest(),
            "oracle_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "task_count": len(manifest["tasks"]), "remaining_scenarios_owner": "tests/test_native_workflow_scenarios.py",
            "frontends": frontends.identities, "model_execution": False,
            "general_target_admission": False, "execution_scope": "fixed owned fixture variants only"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--toolchains", type=Path, required=True)
    parser.add_argument("--work", type=Path, required=True)
    parser.add_argument("--runtime-python", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--provider-helpers", type=Path)
    args = parser.parse_args()
    if args.work.exists():
        raise ValueError("Oracle work directory must be new")
    try:
        result = run_controls(json.loads(args.toolchains.read_text()), args.work.resolve(), args.runtime_python.absolute(), args.provider_helpers)
    except BaseException as exc:
        args.output.write_text(json.dumps({"status": "failed", "error": str(exc), "model_execution": False}, indent=2) + "\n")
        raise
    args.output.write_text(json.dumps(result, indent=2) + "\n")


if __name__ == "__main__":
    main()
