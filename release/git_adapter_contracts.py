"""Native contracts for the explicitly selected external Git stdin adapter."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time


def verify(adapter: Path, real: Path, output: Path) -> dict:
    if os.name != "nt" or sys.platform != "win32":
        raise ValueError("adapter contracts require native Windows")
    environment = {**os.environ, "AGENT_WIKI_REAL_GIT": str(real)}
    checks = []

    def parity(arguments: list[str], data: bytes | None = None):
        expected = subprocess.run([str(real), *arguments], input=data, capture_output=True,
                                  timeout=10, check=False, env=environment)
        actual = subprocess.run([str(adapter), *arguments], input=data, capture_output=True,
                                timeout=10, check=False, env=environment)
        assert (actual.returncode, actual.stdout, actual.stderr) == (
            expected.returncode, expected.stdout, expected.stderr), arguments
        checks.append({"arguments": arguments, "input_sha256": None if data is None else hashlib.sha256(data).hexdigest(),
                       "exit_code": actual.returncode, "stdout_sha256": hashlib.sha256(actual.stdout).hexdigest(),
                       "stderr_sha256": hashlib.sha256(actual.stderr).hexdigest()})

    with tempfile.TemporaryDirectory(prefix="git adapter native ", dir=output) as temporary:
        root = Path(temporary) / "caller with spaces Ω"
        root.mkdir()
        subprocess.run([str(real), "init", "--quiet", str(root)], check=True, timeout=10)
        (root / ".gitignore").write_text("ignored.txt\n", encoding="utf-8")
        (root / "tracked.txt").write_text("original source\n", encoding="utf-8")
        subprocess.run([str(real), "-C", str(root), "add", "."], check=True, timeout=10)
        subprocess.run([str(real), "-C", str(root), "-c", "user.name=Adapter control",
                        "-c", "user.email=adapter@example.invalid", "-c", "core.hooksPath=NUL",
                        "commit", "--quiet", "-m", "independent control"], check=True, timeout=10)
        prefix = ["-C", str(root)]
        probes = [["rev-parse", "--absolute-git-dir", "--git-path", "index"],
                  ["rev-parse", "--verify", "HEAD"], ["symbolic-ref", "-q", "HEAD"]]
        timings = []
        for probe in probes:
            parity([*prefix, *probe])
            started = time.monotonic()
            # Keep the parent protocol-like input pipe open until the child exits.
            # communicate() would close it and conceal inherited-input stalls.
            child = subprocess.Popen([str(adapter), *prefix, *probe], stdin=subprocess.PIPE,
                                     stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=environment)
            try:
                assert child.wait(timeout=10) == 0
                timings.append({"arguments": probe, "seconds": round(time.monotonic() - started, 6)})
            finally:
                if child.poll() is None:
                    child.kill()
                child.communicate(timeout=10)
        parity([*prefix, "hash-object", "--stdin"], b"owned binary stdin\x00\xff\n")
        parity([*prefix, "check-ignore", "--stdin", "-z"], b"ignored.txt\x00tracked.txt\x00")
        for literal in ('spaces Ω', 'literal "quotes"', 'C:\\path with spaces\\', 'a\\\\"b\\'):
            parity([*prefix, "-c", "adapter.value=" + literal, "config", "--get", "adapter.value"])
        parity([*prefix, "config", "--get", "adapter.missing"])
        parity([*prefix, "not-a-git-command"])
    return {"status": "pass", "native": sys.platform, "parity": checks, "open_stdin_probes": timings}


if __name__ == "__main__":
    print(json.dumps(verify(Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])), indent=2))
