"""Explicit, isolated compiler-front-end preparation and observation dispatch."""

from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from typing import Any

from .model import Incomplete, canonical_json, digest
from . import python_ast


LANGUAGES = {
    ".py": "python",
    ".pyi": "python",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".js": "typescript",
    ".jsx": "typescript",
    ".go": "go",
    ".rs": "rust",
    ".hs": "haskell",
}


def language(path: str) -> str:
    try:
        return LANGUAGES[Path(path).suffix]
    except KeyError as error:
        raise Incomplete(f"No independent parser for {path}") from error


class Frontends:
    def __init__(self, config: dict, work: Path):
        self.config = config
        self.work = work.absolute()
        self.work.mkdir(parents=True, exist_ok=True)
        self.environment = {
            **os.environ,
            "PYTHONUTF8": "1",
            "PYTHONIOENCODING": "utf-8",
            "GOENV": "off",
            "GOTOOLCHAIN": "local",
            "GOCACHE": str(self.work / "go-cache"),
            "GOPATH": str(self.work / "go-path"),
            "GHC_ENVIRONMENT": "-",
        }
        self.environment.pop("PYTHONPATH", None)
        self.environment.pop("PYTHONHOME", None)
        if config.get("cargo_home"):
            self.environment["CARGO_HOME"] = config["cargo_home"]
        self.commands: dict[str, list[str]] = {}
        self.cache: dict[tuple[str, str, str], Any] = {}
        self.identities: dict[str, dict] = {"python": {"version": sys.version}}

    def execute(
        self,
        command: list[str],
        *,
        data: bytes | None = None,
        cwd: Path | None = None,
        timeout: int = 180,
    ) -> bytes:
        try:
            result = subprocess.run(
                command,
                input=data,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=cwd or self.work,
                env=self.environment,
                timeout=timeout,
            )
        except (OSError, subprocess.TimeoutExpired) as error:
            raise Incomplete(
                f"Independent frontend unavailable: {command[0]}: {error}"
            ) from error
        if result.returncode:
            raise Incomplete(
                f"Independent frontend failed ({command[0]}): {result.stderr.decode('utf-8', errors='replace')[-6000:]}"
            )
        return result.stdout

    def prepare(self, lang: str) -> list[str]:
        if lang in self.commands:
            return self.commands[lang]
        assets = Path(__file__).parent / "frontends"
        tool = self.config.get(
            {"typescript": "node", "go": "go", "rust": "cargo", "haskell": "ghc"}[lang]
        )
        if not tool or not Path(tool).is_file():
            raise Incomplete(f"Explicit {lang} tool path is required")
        version_flag = (
            "version"
            if lang == "go"
            else "--numeric-version"
            if lang == "haskell"
            else "--version"
        )
        version = self.execute([tool, version_flag]).decode().strip()
        if expected := self.config.get("versions", {}).get(lang):
            if version != expected:
                raise Incomplete(
                    f"{lang} tool identity differs: {version!r}, expected {expected!r}"
                )
        if lang == "typescript":
            module = self.config.get("typescript_module")
            if not module or not Path(module).exists():
                raise Incomplete("Explicit locked ts-morph module path is required")
            command = [tool, str(assets / "typescript.cjs"), module]
        elif lang == "go":
            executable = self.work / (
                "go-observer.exe" if os.name == "nt" else "go-observer"
            )
            self.execute(
                [tool, "build", "-o", str(executable), str(assets / "go/main.go")]
            )
            command = [str(executable)]
        elif lang == "rust":
            build = self.work / "rust"
            if not build.exists():
                shutil.copytree(assets / "rust", build)
            else:
                for source in (assets / "rust").rglob("*"):
                    if source.is_file():
                        target = build / source.relative_to(assets / "rust")
                        target.parent.mkdir(parents=True, exist_ok=True)
                        target.write_bytes(source.read_bytes())
            self.execute(
                [
                    tool,
                    "build",
                    "--locked",
                    "--manifest-path",
                    str(build / "Cargo.toml"),
                ],
                timeout=300,
            )
            command = [
                str(
                    build
                    / "target/debug"
                    / (
                        "provider-conformance-rust.exe"
                        if os.name == "nt"
                        else "provider-conformance-rust"
                    )
                )
            ]
        else:
            executable = self.work / "haskell-observer"
            self.execute(
                [
                    tool,
                    "-package-env",
                    "-",
                    "-package",
                    "ghc",
                    "-outputdir",
                    str(self.work / "ghc"),
                    "-o",
                    str(executable),
                    str(assets / "Haskell.hs"),
                ],
                timeout=180,
            )
            libdir = self.execute([tool, "--print-libdir"]).decode().strip()
            command = [str(executable), libdir]
        self.identities[lang] = {
            "version": version,
            "command": command,
            "frontend_sha256": digest(
                b"".join(
                    p.read_bytes() for p in sorted(assets.rglob("*")) if p.is_file()
                )
            ),
        }
        self.commands[lang] = command
        return command

    def batch(self, lang: str, jobs: list[dict]) -> list:
        if lang == "python":
            try:
                return [
                    python_ast.observe(j["text"])
                    if j["mode"] == "source"
                    else python_ast.normalize(j["mode"], j["text"])
                    for j in jobs
                ]
            except (SyntaxError, ValueError) as error:
                raise Incomplete(f"Python oracle parse failed: {error}") from error
        command = self.prepare(lang)
        if lang == "haskell":
            parts = [str(len(jobs)) + "\n"]
            for job in jobs:
                for value in (
                    job["mode"],
                    job["text"],
                    job.get("filename", "Probe.hs"),
                ):
                    parts.extend([str(len(value)) + "\n", value, "\n"])
            raw = "".join(parts).encode()
        else:
            raw = canonical_json(jobs)
        try:
            results = json.loads(self.execute(command, data=raw))
        except ValueError as error:
            raise Incomplete(f"{lang} frontend returned invalid JSON") from error
        if not isinstance(results, list) or len(results) != len(jobs):
            raise Incomplete(f"{lang} frontend returned an incomplete batch")
        return results

    def observe(self, path: Path) -> dict:
        return self.batch(
            language(str(path)),
            [
                {
                    "mode": "source",
                    "text": path.read_text(encoding="utf-8"),
                    "filename": path.name,
                }
            ],
        )[0]

    def normalize(self, lang: str, mode: str, text: str):
        key = (lang, mode, text)
        if key not in self.cache:
            try:
                self.cache[key] = self.batch(lang, [{"mode": mode, "text": text}])[0]
            except Incomplete as error:
                raise Incomplete(
                    f"{lang} {mode} observation {text!r}: {error}"
                ) from error
        return self.cache[key]
