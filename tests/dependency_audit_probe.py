"""Offline controls for the pinned scanner API in the release tool environment."""

from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
from typing import cast
from unittest.mock import patch


def probe(evidence: Path) -> dict:
    import requests
    from pip_audit._service.pypi import PyPIService

    spec = importlib.util.spec_from_file_location("dependency_audit", Path(__file__).parents[1] / "release/dependency_audit.py")
    assert spec is not None and spec.loader is not None
    audit = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(audit)
    evidence.mkdir(parents=True, exist_ok=True)
    inventory = {
        "schema_version": audit.SCHEMA, "scanner": {"name": "pip-audit", "version": audit.PINNED_AUDIT},
        "packages": [{"name": name, "version": version, "installed_version": version}
                     for name, version in ((audit.OWNED_PROJECT, "2.3.0"), ("pip-audit", audit.PINNED_AUDIT), ("runtime-extra", "1.0"))],
        "exclusion": {"name": audit.OWNED_PROJECT, "version": "2.3.0", "verification": {
            "version": "2.3.0", "editable": False, "implementation_hash": "sha256:" + "b" * 64,
        }},
    }
    inventory_path = evidence / "inventory.json"
    audit.write(inventory_path, inventory)
    rows = []
    cases = {
        "success": ("completed", False), "503": ("http-503", True), "429": ("http-429", True),
        "401": ("http-401", False), "404": ("completed", False),
        "malformed": ("permanent-error", False), "connect-timeout": ("connection-timeout", True),
        "read-timeout": ("connection-timeout", True), "connection": ("connection-unavailable", True),
        "certificate": ("certificate-error", False), "finding": ("completed", False),
        "proxy-authentication": ("proxy-error", False),
        "finding-then-outage": ("http-503", False),
    }
    for case, (category, retryable) in cases.items():
        output = evidence / case
        output.mkdir(exist_ok=True)
        queries = []

        class Session:
            def get(self, *, url, timeout):
                queries.append(url)
                assert timeout == 15 and audit.OWNED_PROJECT not in url
                errors = {
                    "connect-timeout": requests.ConnectTimeout, "read-timeout": requests.ReadTimeout,
                    "connection": requests.ConnectionError, "certificate": requests.exceptions.SSLError,
                    "proxy-authentication": requests.exceptions.ProxyError,
                }
                if case in errors:
                    raise errors[case]("controlled transport failure")
                response = requests.Response()
                response.url = url
                response.status_code = int(case) if case.isdigit() else 200
                response.headers["Retry-After"] = "999999"
                payload = {"vulnerabilities": []}
                if case.startswith("finding"):
                    if case == "finding-then-outage" and len(queries) > 1:
                        response.status_code = 503
                    payload["vulnerabilities"] = [{"id": "PYSEC-2099-1", "aliases": ["CVE-2099-0001"],
                                                   "summary": "Controlled finding", "fixed_in": ["99"]}]
                response._content = b"invalid json" if case == "malformed" else json.dumps(payload).encode()
                return response

            def close(self):
                pass

        def service(**kwargs):
            instance = PyPIService(**kwargs)
            instance.session.close()
            instance.session = cast(requests.Session, Session())
            return instance

        with patch("pip_audit._service.pypi.PyPIService", service):
            returncode = audit.worker(inventory_path, output)
        outcome = json.loads((output / "outcome.json").read_text())
        assert (outcome["category"], outcome["retryable"]) == (category, retryable), (case, outcome)
        assert returncode == int(category != "completed")
        assert outcome["report_sha256"] == audit.digest(audit.read(output / "report.json"))
        if case in {"success", "finding"}:
            assert len(queries) == 2
            assert audit.validate_report(audit.read(output / "report.json"), inventory) == (2 if case == "finding" else 0)
        if case == "404":
            try:
                audit.validate_report(audit.read(output / "report.json"), inventory)
            except ValueError as exc:
                assert "unaudited third-party" in str(exc)
            else:
                raise AssertionError("unexpected third-party skip passed")
        if case == "429":
            assert outcome["retry_after"] == 60
        if case == "finding-then-outage":
            assert outcome["findings_seen"] == 1
        rows.append({"case": case, "outcome": outcome, "queries": queries, "returncode": returncode})
    result = {"passed": True, "scanner": audit.PINNED_AUDIT, "cases": rows}
    audit.write(evidence / "summary.json", result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence", type=Path, required=True)
    args = parser.parse_args()
    result = probe(args.evidence)
    print(f"Pinned dependency-audit controls: {len(result['cases'])} passed (offline)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
