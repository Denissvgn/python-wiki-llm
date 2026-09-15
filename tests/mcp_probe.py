"""Bounded SDK request settings and durable evidence for installed MCP probes."""

from contextlib import contextmanager
from datetime import timedelta
from importlib.metadata import PackageNotFoundError, version
import json
from pathlib import Path
import re
import sys
import time
import traceback
from typing import Any


def _error_details(error):
    return {
        "type": f"{type(error).__module__}.{type(error).__qualname__}",
        "message": str(error)[:4096],
        "traceback": "".join(
            traceback.format_exception(type(error), error, error.__traceback__)
        )[-16000:],
    }


class McpProbe:
    """Record assertions before SDK cleanup can obscure their original failure.

    Pass ``read_timeout`` to ClientSession so the SDK bounds each RPC. The
    artifact harness separately bounds the entire probe subprocess; do not
    cancel the SDK's nested task groups with a session-wide asyncio.wait_for.
    """

    def __init__(self, output, expected_steps, *, request_timeout_seconds=45):
        self.output = Path(output)
        self.expected_steps = tuple(expected_steps)
        if not self.expected_steps or len(set(self.expected_steps)) != len(
            self.expected_steps
        ):
            raise ValueError("MCP probe steps must be nonempty and unique")
        if (
            isinstance(request_timeout_seconds, bool)
            or not isinstance(request_timeout_seconds, (int, float))
            or not 0 < request_timeout_seconds <= 45
        ):
            raise ValueError(
                "MCP request timeout must be positive and at most 45 seconds"
            )
        self.read_timeout = timedelta(seconds=request_timeout_seconds)
        versions = {}
        for name in ("mcp", "anyio"):
            try:
                versions[name] = version(name)
            except PackageNotFoundError:
                versions[name] = None
        self.result: dict[str, Any] = {
            "schema_version": "agent-wiki-mcp-probe/v1",
            "status": "running",
            "python": sys.version,
            "packages": versions,
            "request_timeout_seconds": request_timeout_seconds,
            "expected_steps": list(self.expected_steps),
            "steps": [],
        }

    def _save(self):
        self.output.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.output.with_suffix(self.output.suffix + ".tmp")
        temporary.write_bytes(
            (json.dumps(self.result, indent=2, sort_keys=True) + "\n").encode("utf-8")
        )
        temporary.replace(self.output)

    def capture(self, name, payload):
        """Save synthetic expected/actual observations beside the probe receipt."""
        if re.fullmatch(r"[a-zA-Z0-9_-]+", name) is None:
            raise ValueError("MCP observation name must be a simple identifier")
        self.output.parent.mkdir(parents=True, exist_ok=True)
        path = self.output.with_name(f"{self.output.stem}-{name}.json")
        path.write_bytes(
            (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode("utf-8")
        )

    @contextmanager
    def session(self):
        started = time.monotonic()
        self._save()
        try:
            yield self
            steps = self.result["steps"]
            if [step["name"] for step in steps] != list(self.expected_steps) or any(
                step["status"] != "pass" for step in steps
            ):
                raise AssertionError("MCP probe did not verify every expected step")
        except BaseException as error:
            self.result["status"] = "fail"
            self.result["session_error"] = _error_details(error)
            raise
        else:
            self.result["status"] = "pass"
        finally:
            self.result["elapsed_seconds"] = round(time.monotonic() - started, 6)
            self._save()

    @contextmanager
    def step(self, name, *, request=None):
        index = len(self.result["steps"])
        if index >= len(self.expected_steps) or self.expected_steps[index] != name:
            raise AssertionError(f"Unexpected MCP probe step: {name}")
        record = {"name": name, "status": "running"}
        if request is not None:
            record["request"] = json.loads(json.dumps(request))
        self.result["steps"].append(record)
        started = time.monotonic()
        self._save()
        print(
            f"MCP probe {self.output.stem}: {name} started", file=sys.stderr, flush=True
        )
        try:
            yield
        except BaseException as error:
            record["status"] = "fail"
            record["error"] = _error_details(error)
            raise
        else:
            record["status"] = "pass"
        finally:
            record["elapsed_seconds"] = round(time.monotonic() - started, 6)
            self._save()
            print(
                f"MCP probe {self.output.stem}: {name} {record['status']} "
                f"({record['elapsed_seconds']:.3f}s)",
                file=sys.stderr,
                flush=True,
            )
