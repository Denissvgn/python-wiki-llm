"""Policy source snapshots stay independent of release admission."""

from __future__ import annotations

import argparse
import json
import subprocess
import tarfile
from contextlib import nullcontext
from pathlib import Path
from types import SimpleNamespace

import pytest

from release import qualification


def _git(root: Path, *arguments: str) -> str:
    return subprocess.run(
        ["git", "-C", str(root), *arguments],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


@pytest.fixture
def repository(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    root = tmp_path / "source"
    root.mkdir()
    _git(root, "init", "--quiet")
    (root / "pyproject.toml").write_text(
        '[project]\nname = "agent-wiki-cli"\nversion = "1.5.0"\n', encoding="utf-8"
    )
    (root / "CHANGELOG.md").write_text(
        "## [1.5.0] - 2026-10-01\n"
        "[Unreleased]: https://example.test/compare/v1.5.0...HEAD\n"
        "[1.5.0]: https://example.test/compare/v1.4.0...v1.5.0\n",
        encoding="utf-8",
    )
    (root / "source.py").write_text("VALUE = 1\n", encoding="utf-8")
    _git(root, "add", "--all")
    _git(root, "-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid", "commit", "--quiet", "-m", "Fixture")
    origin = tmp_path / "origin.git"
    subprocess.run(
        ["git", "clone", "--bare", str(root), str(origin)],
        check=True, capture_output=True,
    )
    _git(root, "remote", "add", "origin", str(origin))
    monkeypatch.setattr(qualification, "_check_registry_unused", lambda _version: None)
    return root


def _freeze_args(root: Path, output: Path, **changes: object) -> argparse.Namespace:
    values: dict[str, object] = {
        "root": root,
        "output": output,
        "expected_sha": _git(root, "rev-parse", "HEAD"),
        "repository": "example/agent-wiki",
        "mode": "candidate",
        "check_registry": True,
        "required_ancestor": [],
    }
    values.update(changes)
    return argparse.Namespace(**values)


def test_release_eligibility_is_read_only_and_shared_by_candidate_freeze(
    repository: Path, tmp_path: Path,
) -> None:
    files = [repository / name for name in ("pyproject.toml", "CHANGELOG.md", "source.py")]
    before = [(path.read_bytes(), path.stat().st_mtime_ns) for path in files]
    result = qualification.release_eligibility(repository)
    assert result == {
        "schema_version": qualification.ELIGIBILITY_SCHEMA,
        "status": "eligible", "version": "1.5.0", "tag": "v1.5.0", "reason": None,
    }
    assert before == [(path.read_bytes(), path.stat().st_mtime_ns) for path in files]
    assert qualification.freeze_source(_freeze_args(repository, tmp_path / "frozen")) == 0
    assert qualification._validate_identity(
        qualification.load_json(tmp_path / "frozen" / "identity.json")
    )["mode"] == "candidate"


@pytest.mark.parametrize("reason", ["released-version", "changelog", "remote-tag", "published-version"])
def test_release_preparation_is_a_waiting_state_and_normal_freeze_remains_strict(
    repository: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, reason: str,
) -> None:
    if reason == "released-version":
        _git(repository, "tag", "v1.5.0")
    elif reason == "changelog":
        (repository / "CHANGELOG.md").write_text("## [Unreleased]\n", encoding="utf-8")
        _git(repository, "add", "CHANGELOG.md")
        _git(repository, "-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid", "commit", "--quiet", "-m", "Prepare changelog")
    elif reason == "remote-tag":
        _git(repository, "tag", "v1.5.0")
        _git(repository, "push", "origin", "refs/tags/v1.5.0:refs/tags/v1.5.0")
        _git(repository, "tag", "--delete", "v1.5.0")
    else:
        def published(_version: str) -> None:
            raise qualification.RegistryVersionExists("agent-wiki-cli 1.5.0 already exists on PyPI")

        monkeypatch.setattr(qualification, "_check_registry_unused", published)
    result = qualification.release_eligibility(repository)
    assert result["status"] == "waiting_release_preparation"
    with pytest.raises(qualification.QualificationError) as exc:
        qualification.freeze_source(_freeze_args(repository, tmp_path / "frozen"))
    assert str(exc.value) == result["reason"]


@pytest.mark.parametrize("service", ["registry", "origin"])
def test_unavailable_release_metadata_is_blocked_without_claiming_eligibility(
    repository: Path, monkeypatch: pytest.MonkeyPatch, service: str,
) -> None:
    if service == "registry":
        def unavailable(_version: str) -> None:
            raise qualification.QualificationError("PyPI preflight unavailable: fixture")

        monkeypatch.setattr(qualification, "_check_registry_unused", unavailable)
    else:
        _git(repository, "remote", "set-url", "origin", str(repository / "missing-origin"))
    result = qualification.release_eligibility(repository)
    assert result["status"] == "blocked_unavailable"
    assert result["reason"]


def test_registry_check_can_be_omitted_explicitly(
    repository: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    def unexpected(_version: str) -> None:
        raise AssertionError("registry lookup unexpectedly ran")

    monkeypatch.setattr(qualification, "_check_registry_unused", unexpected)
    assert qualification.release_eligibility(repository, check_registry=False)["status"] == "eligible"


def test_policy_source_freeze_ignores_release_preparation_and_registry(
    repository: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    _git(repository, "tag", "v1.5.0")
    (repository / "CHANGELOG.md").unlink()
    _git(repository, "add", "--all")
    _git(repository, "-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid", "commit", "--quiet", "-m", "No release preparation")
    _git(repository, "remote", "set-url", "origin", str(repository / "missing-origin"))

    def forbidden(_version: str) -> None:
        raise AssertionError("nonpromoting freeze queried PyPI")

    monkeypatch.setattr(qualification, "_check_registry_unused", forbidden)
    destination = tmp_path / "policy-source"
    assert qualification.freeze_source(_freeze_args(
        repository, destination, mode="policy-shadow",
        required_ancestor=[_git(repository, "rev-parse", "HEAD")],
    )) == 0
    identity = qualification.load_json(destination / "identity.json")
    assert qualification.validate_policy_identity(identity)["source"]["sha"] == _git(repository, "rev-parse", "HEAD")
    with tarfile.open(destination / "candidate-source.tar") as archive:
        assert archive.pax_headers["comment"] == identity["source"]["sha"]
        assert "source.py" in archive.getnames()
    with pytest.raises(qualification.QualificationError, match="identity.mode"):
        qualification._validate_identity(identity)
    with pytest.raises(qualification.QualificationError, match="identity.mode"):
        qualification.build_bundle(argparse.Namespace(
            evidence=[], identity=destination / "identity.json", output=tmp_path / "bundle",
        ))
    assert not (tmp_path / "bundle").exists()


@pytest.mark.parametrize("mutation", ["dirty", "wrong-sha", "missing-ancestor", "build-residue", "missing-version"])
def test_policy_source_freeze_keeps_source_identity_guards(
    repository: Path, tmp_path: Path, mutation: str,
) -> None:
    args = _freeze_args(repository, tmp_path / "frozen", mode="policy-shadow")
    if mutation == "dirty":
        (repository / "source.py").write_text("VALUE = 2\n", encoding="utf-8")
    elif mutation == "wrong-sha":
        args.expected_sha = "f" * 40
    elif mutation == "missing-ancestor":
        args.required_ancestor = ["f" * 40]
    elif mutation == "build-residue":
        (repository / "build").mkdir()
    else:
        (repository / "pyproject.toml").write_text('[project]\nname = "agent-wiki-cli"\n', encoding="utf-8")
        _git(repository, "add", "pyproject.toml")
        _git(repository, "-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid", "commit", "--quiet", "-m", "Missing version")
        args.expected_sha = _git(repository, "rev-parse", "HEAD")
    with pytest.raises(qualification.QualificationError):
        qualification.freeze_source(args)
    assert not (tmp_path / "frozen" / "candidate-source.tar").exists()


def test_tagged_source_contract_still_requires_exact_tag_identity(repository: Path, tmp_path: Path) -> None:
    _git(repository, "tag", "v1.5.0")
    _git(repository, "push", "origin", "refs/tags/v1.5.0:refs/tags/v1.5.0")
    args = _freeze_args(repository, tmp_path / "tagged", mode="tagged", check_registry=False)
    assert qualification.freeze_source(args) == 0
    identity = qualification.load_json(tmp_path / "tagged" / "identity.json")
    assert qualification._validate_identity(identity)["mode"] == "tagged"
    with pytest.raises(qualification.QualificationError, match="must be nonpromoting"):
        qualification.validate_policy_identity(identity)


def test_policy_mode_is_available_only_by_explicit_cli_choice() -> None:
    args = qualification._parser().parse_args([
        "freeze-source", "--output", "unused", "--expected-sha", "a" * 40,
        "--repository", "example/agent-wiki", "--mode", "policy-shadow",
    ])
    assert args.mode == "policy-shadow"
    args.mode = "unknown"
    with pytest.raises(qualification.QualificationError, match="mode is unsupported"):
        qualification.freeze_source(args)


def test_published_registry_version_has_a_distinct_preparation_exception(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        qualification.urllib.request, "urlopen",
        lambda *_args, **_kwargs: nullcontext(SimpleNamespace(status=200)),
    )
    with pytest.raises(qualification.RegistryVersionExists, match="already exists on PyPI"):
        qualification._check_registry_unused("1.5.0")


@pytest.mark.parametrize("field", ["extra", "source-sha", "mode", "epoch", "tag"])
def test_policy_identity_keeps_exact_schema_and_source_binding(field: str) -> None:
    identity = {
        "schema_version": qualification.IDENTITY_SCHEMA,
        "repository": "example/agent-wiki", "version": "1.5.0", "tag": "v1.5.0",
        "mode": "policy-shadow",
        "source": {
            "sha": "a" * 40, "tree": "b" * 40, "archive_sha256": "c" * 64,
            "commit_epoch": 1_788_134_400,
        },
    }
    if field == "extra":
        identity["extra"] = True
    elif field == "source-sha":
        identity["source"]["sha"] = "invalid"
    elif field == "mode":
        identity["mode"] = "candidate"
    elif field == "epoch":
        identity["source"]["commit_epoch"] = True
    else:
        identity["tag"] = "v1.4.0"
    with pytest.raises(qualification.QualificationError):
        qualification.validate_policy_identity(identity)


@pytest.mark.parametrize("wrapped", [False, True])
@pytest.mark.parametrize("marker", ["identity", "decision"])
def test_nonpromoting_policy_markers_cannot_enter_release_evidence(
    tmp_path: Path, marker: str, wrapped: bool,
) -> None:
    payload: object = (
        {"schema_version": qualification.IDENTITY_SCHEMA, "mode": "policy-shadow"}
        if marker == "identity"
        else {"schema_version": "agent-wiki-release-policy-decision/v1"}
    )
    if wrapped:
        payload = {"evidence": [payload]}
    path = tmp_path / "evidence.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(qualification.QualificationError, match="Nonqualifying shadow"):
        qualification._reject_shadow_evidence(path)
