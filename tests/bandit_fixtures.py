"""Owned complete-report fixtures for the pinned scanner contract."""

from copy import deepcopy
import hashlib
import json
import sys

RANKS = ("UNDEFINED", "LOW", "MEDIUM", "HIGH")
COMMAND = (sys.executable, "-m", "bandit", "-r", "source.py", "-f", "json", "-o", "bandit-full.json")
RUN_ID = "1" * 32


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def raw(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def report(pairs=(("LOW", "HIGH"),)):
    metrics = {"loc": 1, "nosec": 0, "skipped_tests": 0,
               **{f"{kind}.{rank}": 0 for kind in ("SEVERITY", "CONFIDENCE") for rank in RANKS}}
    findings = []
    for severity, confidence in pairs:
        metrics["SEVERITY." + severity] += 1
        metrics["CONFIDENCE." + confidence] += 1
        findings.append({"filename": "source.py", "code": "value = 1\n", "test_id": "B950", "test_name": "owned_issue",
                         "issue_text": "Owned control", "issue_cwe": {}, "issue_severity": severity,
                         "issue_confidence": confidence, "line_number": 1, "line_range": [1],
                         "col_offset": 0, "end_col_offset": 9, "more_info": "https://example.invalid/owned"})
    return {"errors": [], "generated_at": "2026-09-22T00:00:00Z", "results": findings,
            "metrics": {"_totals": metrics, "source.py": deepcopy(metrics)}}


def source():
    files = {"source.py": sha(b"value = 1\n")}
    return {"paths": ["source.py"], "files": files, "sha256": sha(raw(files))}


def observation(payload, log=b"", **changes):
    return {"schema_version": "agent-wiki-bandit-execution/v1", "run_id": RUN_ID,
            "command": list(COMMAND), "tool": {"name": "bandit", "version": "1.9.4", "python": sys.executable},
            "source": source(), "returncode": int(bool(json.loads(payload)["results"])), "error": None,
            "report_sha256": sha(payload), "report_bytes": len(payload), "log_sha256": sha(log),
            "started_at": "2026-09-22T00:00:00+00:00", "finished_at": "2026-09-22T00:00:01+00:00",
            "elapsed_ns": 1_000_000_000, **changes}
