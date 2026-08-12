"""Structured managed-reference verification and provisioning contracts."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from llm_wiki_cli.services import skills
from llm_wiki_cli.services.skills import (
    BUNDLED_SKILLS_ROOT,
    REFERENCE_SKILL_FILES,
    REFERENCE_SKILL_ID,
    ReferenceSkillReason,
    ReferenceSkillState,
    SkillsReport,
    install_reference_skill,
    provision_reference_skill,
    reference_skill_state,
    verify_reference_skill,
)


def _installed(project: Path) -> Path:
    return project / ".claude" / "skills" / REFERENCE_SKILL_ID


def _copied_package_root(tmp_path: Path) -> Path:
    root = tmp_path / "package-skills"
    shutil.copytree(
        BUNDLED_SKILLS_ROOT / REFERENCE_SKILL_ID,
        root / REFERENCE_SKILL_ID,
    )
    return root


def test_structured_state_and_reason_values_are_stable() -> None:
    assert {state.value for state in ReferenceSkillState} == {
        "absent",
        "current",
        "locally_modified",
        "incomplete",
        "package_missing",
        "install_error",
    }
    assert {reason.value for reason in ReferenceSkillReason} == {
        "managed-reference-absent",
        "managed-reference-current",
        "managed-reference-modified",
        "managed-reference-incomplete",
        "managed-reference-package-missing",
        "managed-reference-install-failed",
    }


def test_verifier_is_read_only_and_reports_exact_absent_target(tmp_path: Path) -> None:
    result = verify_reference_skill(tmp_path)

    assert result.state is ReferenceSkillState.ABSENT
    assert result.reason is ReferenceSkillReason.ABSENT
    assert result.path == _installed(tmp_path)
    assert result.details == ()
    assert not result.current
    assert result.to_dict() == {
        "state": "absent",
        "reason": "managed-reference-absent",
        "path": _installed(tmp_path).as_posix(),
        "details": [],
        "current": False,
    }
    assert not _installed(tmp_path).exists()


def test_exact_install_is_current_and_compatibility_adapter_is_unmodified(
    tmp_path: Path,
) -> None:
    install_reference_skill(tmp_path)

    result = verify_reference_skill(tmp_path)

    assert result.state is ReferenceSkillState.CURRENT
    assert result.reason is ReferenceSkillReason.CURRENT
    assert result.current
    assert result.details == ()
    assert reference_skill_state(tmp_path) == "unmodified"


def test_normalized_line_endings_remain_current(tmp_path: Path) -> None:
    install_reference_skill(tmp_path)
    topic = _installed(tmp_path) / "references" / "maintenance.md"
    normalized = topic.read_text(encoding="utf-8")
    topic.write_bytes(normalized.replace("\n", "\r\n").encode("utf-8"))

    result = verify_reference_skill(tmp_path)

    assert result.state is ReferenceSkillState.CURRENT
    assert reference_skill_state(tmp_path) == "unmodified"


def test_content_drift_is_locally_modified_with_exact_detail(tmp_path: Path) -> None:
    install_reference_skill(tmp_path)
    topic = _installed(tmp_path) / "references" / "maintenance.md"
    topic.write_text("local notes\n", encoding="utf-8")

    result = verify_reference_skill(tmp_path)

    assert result.state is ReferenceSkillState.LOCALLY_MODIFIED
    assert result.reason is ReferenceSkillReason.LOCALLY_MODIFIED
    assert result.details == ("content_mismatch:references/maintenance.md",)
    assert reference_skill_state(tmp_path) == "modified"


def test_missing_extra_and_directory_drift_are_incomplete_and_sorted(
    tmp_path: Path,
) -> None:
    install_reference_skill(tmp_path)
    root = _installed(tmp_path)
    (root / "references" / "governance.md").unlink()
    (root / "references" / "local.md").write_text("local\n", encoding="utf-8")
    (root / "references" / "empty").mkdir()

    result = verify_reference_skill(tmp_path)

    assert result.state is ReferenceSkillState.INCOMPLETE
    assert result.reason is ReferenceSkillReason.INCOMPLETE
    assert result.details == tuple(sorted(result.details))
    assert set(result.details) == {
        "extra:references/local.md",
        "extra_directory:references/empty",
        "missing:references/governance.md",
    }


def test_conflicting_reference_root_file_is_incomplete(tmp_path: Path) -> None:
    root = _installed(tmp_path)
    root.parent.mkdir(parents=True)
    root.write_text("conflict\n", encoding="utf-8")

    result = verify_reference_skill(tmp_path)

    assert result.state is ReferenceSkillState.INCOMPLETE
    assert result.details == ("file:.",)


def test_unsafe_expected_entry_is_incomplete_and_never_followed(
    tmp_path: Path,
) -> None:
    install_reference_skill(tmp_path)
    topic = _installed(tmp_path) / "references" / "maintenance.md"
    outside = tmp_path / "outside.md"
    outside.write_text("sentinel\n", encoding="utf-8")
    topic.unlink()
    try:
        topic.symlink_to(outside)
    except OSError as exc:  # pragma: no cover - platform policy
        pytest.skip(f"symlinks unavailable: {exc}")

    result = verify_reference_skill(tmp_path)

    assert result.state is ReferenceSkillState.INCOMPLETE
    assert "missing:references/maintenance.md" in result.details
    assert "unsafe:references/maintenance.md" in result.details
    assert outside.read_text(encoding="utf-8") == "sentinel\n"


def test_unsafe_install_ancestry_is_incomplete_and_reports_component(
    tmp_path: Path,
) -> None:
    project = tmp_path / "project"
    project.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    alias = project / ".llm-wiki"
    try:
        alias.symlink_to(outside, target_is_directory=True)
    except OSError as exc:  # pragma: no cover - platform policy
        pytest.skip(f"symlinks unavailable: {exc}")

    result = verify_reference_skill(project, agent="generic")

    assert result.state is ReferenceSkillState.INCOMPLETE
    assert result.details == (f"unsafe:{alias}",)
    assert list(outside.iterdir()) == []


@pytest.mark.parametrize("damage", ["root", "skill", "missing_file", "extra_file"])
def test_damaged_package_is_distinct_from_installed_drift(
    tmp_path: Path,
    damage: str,
) -> None:
    package_root = _copied_package_root(tmp_path)
    if damage == "root":
        shutil.rmtree(package_root)
    elif damage == "skill":
        shutil.rmtree(package_root / REFERENCE_SKILL_ID)
    elif damage == "missing_file":
        (package_root / REFERENCE_SKILL_ID / "references" / "governance.md").unlink()
    else:
        (package_root / REFERENCE_SKILL_ID / "references" / "extra.md").write_text(
            "extra\n",
            encoding="utf-8",
        )

    result = verify_reference_skill(tmp_path, skills_root=package_root)

    assert result.state is ReferenceSkillState.PACKAGE_MISSING
    assert result.reason is ReferenceSkillReason.PACKAGE_MISSING
    assert result.path == _installed(tmp_path)
    assert result.details


def test_unsafe_packaged_entry_is_package_missing_and_never_followed(
    tmp_path: Path,
) -> None:
    package_root = _copied_package_root(tmp_path)
    topic = package_root / REFERENCE_SKILL_ID / "references" / "maintenance.md"
    outside = tmp_path / "outside-package.md"
    outside.write_text("sentinel\n", encoding="utf-8")
    topic.unlink()
    try:
        topic.symlink_to(outside)
    except OSError as exc:  # pragma: no cover - platform policy
        pytest.skip(f"symlinks unavailable: {exc}")

    result = verify_reference_skill(tmp_path, skills_root=package_root)

    assert result.state is ReferenceSkillState.PACKAGE_MISSING
    assert "package_missing:references/maintenance.md" in result.details
    assert "package_unsafe:references/maintenance.md" in result.details
    assert outside.read_text(encoding="utf-8") == "sentinel\n"


def test_installed_and_package_read_failures_have_distinct_states(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    package_root = _copied_package_root(tmp_path)
    install_reference_skill(tmp_path, skills_root=package_root)
    installed_topic = _installed(tmp_path) / "references" / "maintenance.md"
    package_topic = package_root / REFERENCE_SKILL_ID / "references" / "maintenance.md"
    real_read = skills.read_md

    def installed_unreadable(path: Path) -> str:
        if path == installed_topic:
            raise OSError("installed unreadable")
        return real_read(path)

    monkeypatch.setattr(skills, "read_md", installed_unreadable)
    installed_result = verify_reference_skill(tmp_path, skills_root=package_root)
    assert installed_result.state is ReferenceSkillState.INCOMPLETE
    assert installed_result.details == ("unreadable:references/maintenance.md",)

    def package_unreadable(path: Path) -> str:
        if path == package_topic:
            raise OSError("package unreadable")
        return real_read(path)

    monkeypatch.setattr(skills, "read_md", package_unreadable)
    package_result = verify_reference_skill(tmp_path, skills_root=package_root)
    assert package_result.state is ReferenceSkillState.PACKAGE_MISSING
    assert package_result.details == ("package_unreadable:references/maintenance.md",)


def test_invalid_text_encoding_is_classified_without_escaping(tmp_path: Path) -> None:
    package_root = _copied_package_root(tmp_path)
    install_reference_skill(tmp_path, skills_root=package_root)
    installed_topic = _installed(tmp_path) / "references" / "maintenance.md"
    installed_topic.write_bytes(b"\x81")

    installed_result = verify_reference_skill(tmp_path, skills_root=package_root)

    assert installed_result.state is ReferenceSkillState.INCOMPLETE
    assert installed_result.details == ("unreadable:references/maintenance.md",)

    package_topic = package_root / REFERENCE_SKILL_ID / "references" / "maintenance.md"
    package_topic.write_bytes(b"\x81")
    package_result = verify_reference_skill(tmp_path, skills_root=package_root)

    assert package_result.state is ReferenceSkillState.PACKAGE_MISSING
    assert package_result.details == ("package_unreadable:references/maintenance.md",)


def test_arbitrary_packaged_root_classifies_identically_to_source_tree(
    tmp_path: Path,
) -> None:
    package_root = _copied_package_root(tmp_path)
    source_project = tmp_path / "source-project"
    package_project = tmp_path / "package-project"
    source_project.mkdir()
    package_project.mkdir()
    install_reference_skill(source_project)
    install_reference_skill(package_project, skills_root=package_root)

    source = verify_reference_skill(source_project)
    packaged = verify_reference_skill(package_project, skills_root=package_root)

    assert (packaged.state, packaged.reason, packaged.details) == (
        source.state,
        source.reason,
        source.details,
    )


def test_successful_provision_exposes_report_and_current_verification(
    tmp_path: Path,
) -> None:
    result = provision_reference_skill(tmp_path)

    assert result.ok
    assert result.state is ReferenceSkillState.CURRENT
    assert result.reason is ReferenceSkillReason.CURRENT
    assert result.verification.current
    assert result.report is not None and result.report.ok
    assert result.to_dict()["path"] == result.path.as_posix()
    assert result.to_dict()["verification"]["state"] == "current"


def test_provision_preserves_local_drift_and_returns_live_state(tmp_path: Path) -> None:
    install_reference_skill(tmp_path)
    topic = _installed(tmp_path) / "references" / "maintenance.md"
    topic.write_text("local notes\n", encoding="utf-8")

    result = provision_reference_skill(tmp_path)

    assert not result.ok
    assert result.state is ReferenceSkillState.LOCALLY_MODIFIED
    assert result.reason is ReferenceSkillReason.LOCALLY_MODIFIED
    assert result.report is not None and not result.report.ok
    assert topic.read_text(encoding="utf-8") == "local notes\n"
    assert any(
        detail.startswith("report:existing_file_differs:") for detail in result.details
    )


def test_provision_write_failure_is_install_error_with_live_verification(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_write(_path: Path, _text: str) -> None:
        raise OSError("injected write failure")

    monkeypatch.setattr(skills, "write_md", fail_write)

    result = provision_reference_skill(tmp_path)

    assert not result.ok
    assert result.state is ReferenceSkillState.INSTALL_ERROR
    assert result.reason is ReferenceSkillReason.INSTALL_ERROR
    assert result.verification.state is ReferenceSkillState.INCOMPLETE
    assert result.report is not None and not result.report.ok
    assert any(detail.startswith("report:write_failed:") for detail in result.details)


def test_provision_exception_is_structured_and_process_control_is_not_caught(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_install(*_args: object, **_kwargs: object) -> SkillsReport:
        raise RuntimeError("injected install exception")

    monkeypatch.setattr(skills, "install_reference_skill", fail_install)
    result = provision_reference_skill(tmp_path)

    assert result.state is ReferenceSkillState.INSTALL_ERROR
    assert result.reason is ReferenceSkillReason.INSTALL_ERROR
    assert result.verification.state is ReferenceSkillState.ABSENT
    assert result.report is None
    assert result.details == ("exception:RuntimeError:injected install exception",)

    def interrupt(*_args: object, **_kwargs: object) -> SkillsReport:
        raise KeyboardInterrupt

    monkeypatch.setattr(skills, "install_reference_skill", interrupt)
    with pytest.raises(KeyboardInterrupt):
        provision_reference_skill(tmp_path)


def test_missing_package_during_provision_remains_package_missing(
    tmp_path: Path,
) -> None:
    missing_root = tmp_path / "missing-package"

    result = provision_reference_skill(tmp_path, skills_root=missing_root)

    assert not result.ok
    assert result.state is ReferenceSkillState.PACKAGE_MISSING
    assert result.reason is ReferenceSkillReason.PACKAGE_MISSING
    assert result.verification.state is ReferenceSkillState.PACKAGE_MISSING
    assert result.report is None
    assert any(detail.startswith("package_root_missing:") for detail in result.details)
    assert not (tmp_path / ".claude").exists()


@pytest.mark.parametrize(
    "damage",
    ["missing", "conflicting_directory", "unsafe", "unreadable"],
)
def test_package_preflight_failure_performs_zero_destination_mutation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    damage: str,
) -> None:
    project = tmp_path / "project"
    project.mkdir()
    package_root = _copied_package_root(tmp_path)
    topic = package_root / REFERENCE_SKILL_ID / "references" / "maintenance.md"
    real_read = skills.read_md
    writes: list[Path] = []

    if damage == "missing":
        topic.unlink()
    elif damage == "conflicting_directory":
        topic.unlink()
        topic.mkdir()
    elif damage == "unsafe":
        outside = tmp_path / "outside-package-topic.md"
        outside.write_text("sentinel\n", encoding="utf-8")
        topic.unlink()
        try:
            topic.symlink_to(outside)
        except OSError as exc:  # pragma: no cover - platform policy
            pytest.skip(f"symlinks unavailable: {exc}")
    else:

        def unreadable(path: Path) -> str:
            if path == topic:
                raise OSError("injected package read failure")
            return real_read(path)

        monkeypatch.setattr(skills, "read_md", unreadable)

    def record_write(path: Path, _text: str) -> None:
        writes.append(path)
        raise AssertionError("package preflight must precede destination writes")

    monkeypatch.setattr(skills, "write_md", record_write)

    result = provision_reference_skill(project, skills_root=package_root)

    assert result.state is ReferenceSkillState.PACKAGE_MISSING
    assert result.reason is ReferenceSkillReason.PACKAGE_MISSING
    assert result.verification.state is ReferenceSkillState.PACKAGE_MISSING
    assert result.details == result.verification.details
    assert result.report is None
    assert result.details
    assert writes == []
    assert not (project / ".claude").exists()


def test_unknown_failed_report_is_install_error(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    failed = SkillsReport(ok=False, dest_dir=str(tmp_path / ".claude" / "skills"))
    monkeypatch.setattr(
        skills,
        "install_reference_skill",
        lambda *_args, **_kwargs: failed,
    )

    result = provision_reference_skill(tmp_path)

    assert result.state is ReferenceSkillState.INSTALL_ERROR
    assert result.verification.state is ReferenceSkillState.ABSENT
    assert result.report is failed


def test_reported_success_without_current_tree_is_install_error(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    inconsistent = SkillsReport(
        ok=True,
        dest_dir=str(tmp_path / ".claude" / "skills"),
    )
    monkeypatch.setattr(
        skills,
        "install_reference_skill",
        lambda *_args, **_kwargs: inconsistent,
    )

    result = provision_reference_skill(tmp_path)

    assert result.state is ReferenceSkillState.INSTALL_ERROR
    assert result.verification.state is ReferenceSkillState.ABSENT
    assert result.report is inconsistent


def test_expected_file_contract_is_exact() -> None:
    assert len(REFERENCE_SKILL_FILES) == 11
    assert len(set(REFERENCE_SKILL_FILES)) == len(REFERENCE_SKILL_FILES)
