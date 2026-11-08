"""Install the provider packaged with the pinned action and attest its bytes."""

import hashlib
from importlib import metadata
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import tomllib
import venv


ACTION = Path(__file__).resolve().parent
FULL_SHA = re.compile(r"[0-9a-f]{40}(?:[0-9a-f]{24})?")


def verify(source: Path, receipt: Path, revision: str, repository: str) -> None:
    import llm_wiki_cli

    package = Path(llm_wiki_cli.__file__).resolve().parent
    if not package.is_relative_to(Path(sys.prefix).resolve()):
        raise ValueError("Provider was imported from outside the isolated environment")
    project = tomllib.loads((source / "pyproject.toml").read_text(encoding="utf-8"))
    version = metadata.version("agent-wiki-cli")
    if version != project["project"]["version"]:
        raise ValueError("Installed provider version differs from the pinned source")
    expected = source / "src/llm_wiki_cli"
    files = {}
    for path in sorted(package.rglob("*")):
        if "__pycache__" in path.parts or not path.is_file():
            continue
        relative = path.relative_to(package).as_posix()
        original = expected / relative
        if path.is_symlink() or original.is_symlink() or not original.is_file():
            raise ValueError(f"Unexpected installed provider file: {relative}")
        raw = path.read_bytes()
        if raw != original.read_bytes():
            raise ValueError(f"Installed provider differs from pinned source: {relative}")
        files[relative] = hashlib.sha256(raw).hexdigest()
    declared = project["tool"]["setuptools"]["package-data"]["llm_wiki_cli"]
    required = set(declared) | {p.relative_to(expected).as_posix() for p in expected.rglob("*.py")}
    if not required <= files.keys():
        raise ValueError("Installed provider is missing declared package files")
    fingerprint = hashlib.sha256(json.dumps(files, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    receipt.write_text(
        json.dumps({
            "schema_version": "llm-wiki-action-provider/v1", "installed": True,
            "action_ref": revision, "action_repository": repository, "provider_revision": revision,
            "package_origin": str(package), "package_sha256": fingerprint,
            "version": version, "parser_version": metadata.version("markdown-it-py"),
            "python": sys.version, "platform": sys.platform,
        }, indent=2, sort_keys=True) + "\n", encoding="utf-8",
    )


def build_input(provider: Path, runtime: Path) -> tuple[Path, str, str]:
    # Installing a wheel runs its backend. Keep all such writes in the private
    # runtime, including for a local action invoked from the consumer checkout.
    source = runtime / "provider-source"
    source.mkdir()
    ref = os.environ.get("PROVIDER_ACTION_REF", "")
    repository = os.environ.get("PROVIDER_REPOSITORY", "")
    build_paths = (
        "src", "pyproject.toml", "release_build_backend.py", "MANIFEST.in",
        "README.md", "LICENSE", "docs/standalone-documentation.md",
    )
    if ref:
        if not FULL_SHA.fullmatch(ref) or not repository:
            raise ValueError("Pin the remote candidate action to a full immutable Git SHA")
        for name in build_paths:
            path = provider / name
            destination = source / name
            destination.parent.mkdir(parents=True, exist_ok=True)
            if path.is_dir():
                shutil.copytree(path, destination)
            else:
                shutil.copyfile(path, destination)
    else:
        # Local actions (including repository self-checks) have no action_ref.
        repository = os.environ["GITHUB_REPOSITORY"]
        git = ["git", "-C", str(provider), "-c", "core.fsmonitor=false"]
        top = Path(subprocess.check_output([*git, "rev-parse", "--show-toplevel"], text=True).strip())
        if top.resolve() != provider or subprocess.check_output([*git, "status", "--porcelain"]):
            raise ValueError("The local action must use a clean provider checkout")
        ref = subprocess.check_output([*git, "rev-parse", "HEAD"], text=True).strip()
        if not FULL_SHA.fullmatch(ref):
            raise ValueError("Cannot identify the local provider checkout")
        archive = runtime / "provider.tar"
        subprocess.run([*git, "archive", "--format=tar", "-o", str(archive), ref, *build_paths], check=True)
        with tarfile.open(archive) as tar:
            tar.extractall(source, filter="data")
        archive.unlink()
    return source, ref, repository


def setup() -> None:
    workspace = Path(os.environ["GITHUB_WORKSPACE"]).resolve(strict=True)
    consumer = (workspace / os.environ["INPUT_WORKING_DIRECTORY"]).resolve(strict=True)
    if not consumer.is_dir() or not consumer.is_relative_to(workspace):
        raise ValueError("working-directory must be a directory inside GITHUB_WORKSPACE")
    suffix = os.environ["INPUT_EVIDENCE_ID"]
    if not re.fullmatch(r"[a-z0-9][a-z0-9._-]{0,39}", suffix):
        raise ValueError("Invalid evidence-id (use up to 40 lowercase letters, digits, dots, dashes or underscores)")
    temporary = Path(os.environ["RUNNER_TEMP"]).resolve(strict=True)
    if temporary.is_relative_to(workspace):
        raise ValueError("RUNNER_TEMP must be separate from the workspace")
    runtime = Path(tempfile.mkdtemp(prefix=f"llm-wiki-candidate-{suffix}.", dir=temporary))
    evidence = runtime / "evidence"
    evidence.mkdir()
    environment = runtime / ".venv"
    python = environment / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    receipt = evidence / "provider.json"
    with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as output:
        for key, path in {"runtime": runtime, "consumer": consumer, "python": python,
                          "evidence-dir": evidence, "provider-receipt": receipt}.items():
            if "\n" in path.as_posix() or "\r" in path.as_posix():
                raise ValueError("Action paths must be one line")
            output.write(f"{key}={path.as_posix()}\n")
    source, revision, repository = build_input(ACTION.parents[1], runtime)
    venv.create(environment, with_pip=True)
    with (evidence / "provider-install.log").open("wb") as log:
        subprocess.run(
            [str(python), "-I", "-m", "pip", "--isolated", "--disable-pip-version-check",
             "install", "--no-cache-dir", "--no-input", f"{source}[publication]"],
            cwd=runtime, stdout=log, stderr=subprocess.STDOUT, check=True, timeout=600,
        )
    subprocess.run(
        [str(python), "-I", str(ACTION / "provider.py"), "verify",
         str(source), str(receipt), revision, repository], cwd=runtime, check=True,
    )


if __name__ == "__main__":
    if sys.argv[1:2] == ["verify"]:
        verify(Path(sys.argv[2]), Path(sys.argv[3]), sys.argv[4], sys.argv[5])
    else:
        setup()
