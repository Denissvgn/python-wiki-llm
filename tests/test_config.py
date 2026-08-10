"""Tests for config.py — shared constants and validate_path."""

import json
import os
import re
import sys
import warnings
from pathlib import Path
from types import SimpleNamespace

import pytest

from llm_wiki_cli import config as config_module
from llm_wiki_cli.config import (
    AGENT_CHOICES,
    AgentConfigState,
    CLI_AGENTS,
    DEFAULT_WIKI_DIR,
    IDE_AGENTS,
    _normalize_gitignore_trailing_spaces,
    _parse_gitignore_file,
    build_gitignore_matcher,
    config_requires_manual_recovery,
    inspect_config,
    read_config,
    PathValidationError,
    validate_path,
    validate_source_paths,
    validate_source_root,
    write_config,
)
from llm_wiki_cli.services.rendering_lifecycle import RenderReason
from llm_wiki_cli.services.schema import SCHEMA_BLOCK_VERSION, SchemaRenderProfile


class TestConstants:
    def test_default_wiki_dir(self):
        assert DEFAULT_WIKI_DIR == "docs/llm_wiki"

    def test_agent_choices_has_all(self):
        assert set(AGENT_CHOICES) == set(CLI_AGENTS) | IDE_AGENTS

    def test_cli_and_ide_disjoint(self):
        assert set(CLI_AGENTS) & IDE_AGENTS == set()


class TestValidatePath:
    def test_accepts_relative_subdir(self, tmp_path):
        os.chdir(tmp_path)
        sub = tmp_path / "docs" / "wiki"
        sub.mkdir(parents=True)
        result = validate_path("docs/wiki", "--wiki-dir")
        assert result == sub

    def test_accepts_dot(self, tmp_path):
        os.chdir(tmp_path)
        result = validate_path(".", "--src-dir")
        assert result == tmp_path

    def test_rejects_traversal(self, tmp_path):
        os.chdir(tmp_path)
        with pytest.raises(PathValidationError):
            validate_path("../../etc", "--wiki-dir")

    def test_rejects_absolute_outside(self, tmp_path):
        os.chdir(tmp_path)
        with pytest.raises(PathValidationError):
            validate_path("/tmp/outside", "--wiki-dir")

    def test_rejects_embedded_nul_before_path_resolution(self, tmp_path):
        os.chdir(tmp_path)

        with pytest.raises(PathValidationError, match="embedded NUL character"):
            validate_path("docs\0wiki", "--wiki-dir")

    def test_accepts_absolute_inside(self, tmp_path):
        os.chdir(tmp_path)
        sub = tmp_path / "inner"
        sub.mkdir()
        result = validate_path(str(sub), "--wiki-dir")
        assert result == sub

    def test_source_root_preserves_default_cwd_guard(self, tmp_path):
        project = tmp_path / "project"
        outside = tmp_path / "outside"
        project.mkdir()
        outside.mkdir()
        os.chdir(project)

        with pytest.raises(PathValidationError):
            validate_source_root(str(outside), "--src-dir")

    def test_source_root_allows_external_existing_directory(self, tmp_path):
        project = tmp_path / "project"
        outside = tmp_path / "outside"
        project.mkdir()
        outside.mkdir()
        os.chdir(project)

        with warnings.catch_warnings():
            warnings.simplefilter("error")
            assert (
                validate_source_root(str(outside), "--src-dir", allow_external=True)
                == outside
            )

    def test_external_source_root_allows_plain_parent_relative_directory_silently(
        self, tmp_path
    ):
        project = tmp_path / "project"
        outside = tmp_path / "outside"
        project.mkdir()
        outside.mkdir()
        os.chdir(project)

        with warnings.catch_warnings():
            warnings.simplefilter("error")
            result = validate_source_root(
                "../outside",
                "--src-dir",
                allow_external=True,
            )

        assert result == outside

    def test_external_source_root_allows_same_owner_symlink_with_one_warning(
        self, tmp_path
    ):
        project = tmp_path / "project"
        outside = tmp_path / "outside"
        target = outside / "target"
        project.mkdir()
        target.mkdir(parents=True)
        link = outside / "source-link"
        try:
            link.symlink_to(target, target_is_directory=True)
        except OSError:
            pytest.skip("Directory symlinks are unavailable to this test account.")
        os.chdir(project)

        if not hasattr(os, "geteuid") and sys.platform != "win32":
            with pytest.raises(
                PathValidationError,
                match="ownership cannot be verified on this platform",
            ):
                validate_source_root(
                    str(link),
                    "--src-dir",
                    allow_external=True,
                )
            return

        message = f"external source root '{link}' resolves to '{target.resolve()}'."
        with pytest.warns(UserWarning, match=re.escape(message)) as emitted:
            result = validate_source_root(
                str(link),
                "--src-dir",
                allow_external=True,
            )

        assert result == target.resolve()
        assert len(emitted) == 1

    def test_external_source_root_allows_parent_relative_same_owner_symlink(
        self, tmp_path
    ):
        if not hasattr(os, "geteuid"):
            pytest.skip("Symlink ownership is not verifiable on this platform.")
        project = tmp_path / "project"
        outside = tmp_path / "outside"
        target = outside / "target"
        project.mkdir()
        target.mkdir(parents=True)
        link = outside / "source-link"
        try:
            link.symlink_to(target, target_is_directory=True)
        except OSError:
            pytest.skip("Directory symlinks are unavailable to this test account.")
        os.chdir(project)

        with pytest.warns(UserWarning, match="external source root"):
            result = validate_source_root(
                "../outside/source-link",
                "--src-dir",
                allow_external=True,
            )

        assert result == target.resolve()

    @pytest.mark.parametrize(
        ("path_owner_sid", "accepted"),
        [
            ("S-1-5-21-current", True),
            ("S-1-5-18", True),
            ("S-1-5-32-544", True),
            ("S-1-5-21-other", False),
        ],
    )
    def test_external_source_root_uses_windows_owner_sid_for_reparse_policy(
        self,
        tmp_path,
        monkeypatch,
        path_owner_sid,
        accepted,
    ):
        project = tmp_path / "project"
        target = tmp_path / "target"
        project.mkdir()
        target.mkdir()
        link = tmp_path / "source-link"
        try:
            link.symlink_to(target, target_is_directory=True)
        except OSError:
            pytest.skip("Directory symlinks are unavailable to this test account.")
        os.chdir(project)
        inspected: list[Path] = []

        monkeypatch.setattr(config_module.sys, "platform", "win32")
        monkeypatch.setattr(
            config_module,
            "windows_current_user_sid",
            lambda: "S-1-5-21-current",
        )

        def owner_sid(path):
            inspected.append(path)
            return path_owner_sid

        monkeypatch.setattr(config_module, "windows_path_owner_sid", owner_sid)

        if accepted:
            with pytest.warns(UserWarning, match="external source root"):
                result = validate_source_root(
                    str(link),
                    "--src-dir",
                    allow_external=True,
                )
            assert result == target.resolve()
        else:
            with pytest.raises(
                PathValidationError,
                match="not owned by the current Windows user, LocalSystem, "
                "or Administrators",
            ):
                validate_source_root(
                    str(link),
                    "--src-dir",
                    allow_external=True,
                )

        assert link in inspected

    def test_external_source_root_fails_closed_when_windows_sid_is_unavailable(
        self, tmp_path, monkeypatch
    ):
        project = tmp_path / "project"
        target = tmp_path / "target"
        project.mkdir()
        target.mkdir()
        link = tmp_path / "source-link"
        try:
            link.symlink_to(target, target_is_directory=True)
        except OSError:
            pytest.skip("Directory symlinks are unavailable to this test account.")
        os.chdir(project)
        monkeypatch.setattr(config_module.sys, "platform", "win32")

        def unavailable_sid():
            raise OSError("SID lookup unavailable")

        monkeypatch.setattr(
            config_module,
            "windows_current_user_sid",
            unavailable_sid,
        )

        with pytest.raises(
            PathValidationError,
            match="ownership cannot be verified on this platform",
        ):
            validate_source_root(
                str(link),
                "--src-dir",
                allow_external=True,
            )

    def test_external_source_root_fails_closed_without_verifiable_uid(
        self, tmp_path, monkeypatch
    ):
        if sys.platform == "win32":
            pytest.skip("This exercises the POSIX UID-unavailable branch.")
        project = tmp_path / "project"
        outside = tmp_path / "outside"
        target = outside / "target"
        project.mkdir()
        target.mkdir(parents=True)
        link = outside / "source-link"
        try:
            link.symlink_to(target, target_is_directory=True)
        except OSError:
            pytest.skip("Directory symlinks are unavailable to this test account.")
        os.chdir(project)
        monkeypatch.delattr(config_module.os, "geteuid", raising=False)

        with pytest.raises(
            PathValidationError,
            match="ownership cannot be verified on this platform",
        ):
            validate_source_root(
                str(link),
                "--src-dir",
                allow_external=True,
            )

    @pytest.mark.parametrize(
        "failure",
        [
            OSError("UID lookup unavailable"),
            NotImplementedError("geteuid unavailable"),
        ],
    )
    def test_external_source_root_fails_closed_when_uid_lookup_fails(
        self, tmp_path, monkeypatch, failure
    ):
        if sys.platform == "win32":
            pytest.skip("This exercises the POSIX UID lookup branch.")
        project = tmp_path / "project"
        target = tmp_path / "target"
        project.mkdir()
        target.mkdir()
        link = tmp_path / "source-link"
        try:
            link.symlink_to(target, target_is_directory=True)
        except OSError:
            pytest.skip("Directory symlinks are unavailable to this test account.")
        os.chdir(project)

        def unavailable_uid():
            raise failure

        monkeypatch.setattr(config_module.os, "geteuid", unavailable_uid)

        with pytest.raises(
            PathValidationError,
            match="ownership cannot be verified on this platform",
        ):
            validate_source_root(
                str(link),
                "--src-dir",
                allow_external=True,
            )

    def test_external_source_root_fails_closed_for_invalid_uid(
        self, tmp_path, monkeypatch
    ):
        if sys.platform == "win32":
            pytest.skip("This exercises the POSIX UID validation branch.")
        project = tmp_path / "project"
        target = tmp_path / "target"
        project.mkdir()
        target.mkdir()
        link = tmp_path / "source-link"
        try:
            link.symlink_to(target, target_is_directory=True)
        except OSError:
            pytest.skip("Directory symlinks are unavailable to this test account.")
        os.chdir(project)
        monkeypatch.setattr(config_module.os, "geteuid", lambda: -1)

        with pytest.raises(
            PathValidationError,
            match="ownership cannot be verified on this platform",
        ):
            validate_source_root(
                str(link),
                "--src-dir",
                allow_external=True,
            )

    def test_external_source_root_discloses_symlink_target_chain_once(self, tmp_path):
        project = tmp_path / "project"
        outside = tmp_path / "outside"
        target = outside / "target"
        project.mkdir()
        target.mkdir(parents=True)
        inner_link = outside / "inner-link"
        outer_link = outside / "outer-link"
        try:
            inner_link.symlink_to(target, target_is_directory=True)
            outer_link.symlink_to(inner_link, target_is_directory=True)
        except OSError:
            pytest.skip("Directory symlinks are unavailable to this test account.")
        os.chdir(project)
        if not hasattr(os, "geteuid"):
            pytest.skip("Symlink-owner disclosure requires POSIX UID semantics.")

        with warnings.catch_warnings(record=True) as emitted:
            warnings.simplefilter("always")
            result = validate_source_root(
                str(outer_link),
                "--src-dir",
                allow_external=True,
            )

        assert result == target.resolve()
        assert len(emitted) == 1
        assert "external source root" in str(emitted[0].message)

    def test_external_source_root_rejects_untrusted_symlink_component(
        self, tmp_path, monkeypatch
    ):
        project = tmp_path / "project"
        outside = tmp_path / "outside"
        target = outside / "target"
        project.mkdir()
        target.mkdir(parents=True)
        link = outside / "source-link"
        try:
            link.symlink_to(target, target_is_directory=True)
        except OSError:
            pytest.skip("Directory symlinks are unavailable to this test account.")
        os.chdir(project)
        observed = {}

        def untrusted_component(
            path,
            *,
            trusted_symlink_uids,
            trusted_symlink_owner,
        ):
            observed["path"] = path
            observed["trusted"] = trusted_symlink_uids
            observed["owner_check"] = trusted_symlink_owner
            return link

        monkeypatch.setattr(
            config_module,
            "first_unsafe_path_component",
            untrusted_component,
        )

        if sys.platform == "win32":
            ownership_error = "not owned by the current Windows user"
        elif hasattr(os, "geteuid"):
            ownership_error = "not owned by the current user or root"
        else:
            ownership_error = "ownership cannot be verified on this platform"
        with pytest.raises(PathValidationError, match=ownership_error):
            validate_source_root(str(link), "--src-dir", allow_external=True)

        assert observed["path"] == link
        if sys.platform == "win32":
            assert observed["trusted"] == set()
            assert callable(observed["owner_check"])
        elif hasattr(os, "geteuid"):
            assert 0 in observed["trusted"]
            assert os.geteuid() in observed["trusted"]
            assert observed["owner_check"] is None
        else:
            assert observed["trusted"] == set()
            assert observed["owner_check"] is None

    def test_external_source_root_detects_other_owner_end_to_end(
        self, tmp_path, monkeypatch
    ):
        if not hasattr(os, "geteuid"):
            pytest.skip("Symlink ownership is not verifiable on this platform.")
        project = tmp_path / "project"
        outside = tmp_path / "outside"
        target = outside / "target"
        project.mkdir()
        target.mkdir(parents=True)
        link = outside / "source-link"
        try:
            link.symlink_to(target, target_is_directory=True)
        except OSError:
            pytest.skip("Directory symlinks are unavailable to this test account.")
        os.chdir(project)
        original_lstat = Path.lstat
        hostile_uid = os.geteuid() + 1
        if hostile_uid == 0:
            hostile_uid = 1

        def lstat_with_other_owner(path):
            metadata = original_lstat(path)
            if path.name == link.name:
                return SimpleNamespace(
                    st_file_attributes=getattr(
                        metadata,
                        "st_file_attributes",
                        0,
                    ),
                    st_mode=metadata.st_mode,
                    st_uid=hostile_uid,
                )
            return metadata

        monkeypatch.setattr(Path, "lstat", lstat_with_other_owner)

        with pytest.raises(
            PathValidationError,
            match="not owned by the current user or root",
        ):
            validate_source_root(
                str(link),
                "--src-dir",
                allow_external=True,
            )

    def test_external_source_root_rejects_unresolvable_path_clearly(self, tmp_path):
        project = tmp_path / "project"
        project.mkdir()
        broken_link = tmp_path / "broken-source"
        try:
            broken_link.symlink_to(tmp_path / "missing", target_is_directory=True)
        except OSError:
            pytest.skip("Directory symlinks are unavailable to this test account.")
        os.chdir(project)

        with pytest.raises(
            PathValidationError,
            match="cannot be resolved to an existing directory",
        ):
            validate_source_root(
                str(broken_link),
                "--src-dir",
                allow_external=True,
            )

    def test_external_source_root_rejects_nul_path_clearly(self):
        with pytest.raises(
            PathValidationError,
            match="cannot be resolved to an existing directory",
        ):
            validate_source_root(
                "invalid\0source",
                "--src-dir",
                allow_external=True,
            )

    def test_external_source_root_rejects_unexpandable_home_clearly(self, monkeypatch):
        def unavailable_home(_path):
            raise RuntimeError("Could not determine home directory")

        monkeypatch.setattr(Path, "expanduser", unavailable_home)

        with pytest.raises(
            PathValidationError,
            match="cannot be resolved to an existing directory",
        ):
            validate_source_root(
                "~missing-user/source",
                "--src-dir",
                allow_external=True,
            )

    def test_source_paths_reject_escape_from_source_root(self, tmp_path):
        source = tmp_path / "source"
        source.mkdir()
        with pytest.raises(PathValidationError):
            validate_source_paths(source, ["../outside.py"])

    def test_source_paths_accept_relative_and_absolute_inside_root(self, tmp_path):
        source = tmp_path / "source"
        package = source / "package"
        package.mkdir(parents=True)
        module = package / "module.py"
        module.write_text("VALUE = 1\n", encoding="utf-8")

        assert (
            validate_source_paths(
                source,
                ["package/module.py", str(module)],
            )
            is None
        )

    def test_source_paths_accept_nonexistent_relative_inside_root(self, tmp_path):
        source = tmp_path / "source"
        source.mkdir()

        assert validate_source_paths(source, ["generated/future.py"]) is None

    def test_source_paths_ignore_empty_inputs(self, tmp_path):
        source = tmp_path / "source"
        source.mkdir()

        assert validate_source_paths(source, None) is None
        assert validate_source_paths(source, [""]) is None

    def test_source_paths_reject_absolute_outside_root(self, tmp_path):
        source = tmp_path / "source"
        outside = tmp_path / "outside.py"
        source.mkdir()
        outside.write_text("VALUE = 1\n", encoding="utf-8")

        with pytest.raises(PathValidationError):
            validate_source_paths(source, [str(outside)])


class TestReadWriteConfig:
    """Round-trip JSON config and backward compatibility."""

    def test_write_then_read(self, tmp_path):
        os.chdir(tmp_path)
        wiki = tmp_path / "docs" / "wiki"
        wiki.mkdir(parents=True)
        data = {
            "agent": "copilot",
            "quality_hints": False,
            "issue_reporting": True,
        }
        write_config(str(wiki), data)
        result = read_config(str(wiki))
        assert result["agent"] == "copilot"
        assert result["quality_hints"] is False
        assert result["issue_reporting"] is True

    def test_render_config_allowlists_match_lifecycle_contract(self):
        assert config_module._RENDER_PROFILES == frozenset(
            profile.value for profile in SchemaRenderProfile
        )
        assert config_module._RENDER_REASONS == frozenset(
            reason.value for reason in RenderReason
        )
        assert config_module._RENDER_PROFILE_VERSION == SCHEMA_BLOCK_VERSION

    def test_defaults_when_no_file(self, tmp_path):
        os.chdir(tmp_path)
        wiki = tmp_path / "nonexistent"
        result = read_config(str(wiki))
        assert result["agent"] == "generic"
        assert result["quality_hints"] is True
        assert result["issue_reporting"] is False
        assert inspect_config(wiki).state is AgentConfigState.ABSENT

    def test_backward_compat_bare_string(self, tmp_path):
        os.chdir(tmp_path)
        wiki = tmp_path / "docs" / "wiki"
        wiki.mkdir(parents=True)
        config_path = wiki / ".llm-wiki-agent"
        config_path.write_text("claude")
        result = read_config(str(wiki))
        assert result["agent"] == "claude"
        assert result["quality_hints"] is True
        assert result["issue_reporting"] is False
        assert inspect_config(wiki).state is AgentConfigState.LEGACY

    def test_legacy_reader_preserves_unknown_future_agent_but_inspection_rejects(
        self, tmp_path
    ):
        os.chdir(tmp_path)
        wiki = tmp_path / "docs" / "wiki"
        wiki.mkdir(parents=True)
        config_path = wiki / ".llm-wiki-agent"
        config_path.write_text("future-agent", encoding="utf-8")

        assert read_config(wiki)["agent"] == "future-agent"
        inspection = inspect_config(wiki)
        assert inspection.state is AgentConfigState.INVALID
        assert inspection.data["agent"] == "generic"

    def test_missing_key_gets_default(self, tmp_path):
        os.chdir(tmp_path)
        wiki = tmp_path / "docs" / "wiki"
        wiki.mkdir(parents=True)
        config_path = wiki / ".llm-wiki-agent"
        config_path.write_text(json.dumps({"agent": "aider"}))
        result = read_config(str(wiki))
        assert result["agent"] == "aider"
        assert result["quality_hints"] is True
        assert result["issue_reporting"] is False

    def test_corrupted_json_returns_defaults(self, tmp_path):
        os.chdir(tmp_path)
        wiki = tmp_path / "docs" / "wiki"
        wiki.mkdir(parents=True)
        config_path = wiki / ".llm-wiki-agent"
        config_path.write_text("{invalid json!!}")
        result = read_config(str(wiki))
        assert result["agent"] == "generic"
        assert result["quality_hints"] is True
        assert result["issue_reporting"] is False

    def test_inspection_preserves_unknown_fields_and_valid_render_state(self, tmp_path):
        os.chdir(tmp_path)
        wiki = tmp_path / "docs" / "wiki"
        wiki.mkdir(parents=True)
        config_path = wiki / ".llm-wiki-agent"
        config_path.write_text(
            json.dumps(
                {
                    "agent": "generic",
                    "custom_extension": {"kept": True},
                    "rendered_profile": "compact",
                    "render_profile_version": 1,
                    "render_reason": "reference-current",
                }
            ),
            encoding="utf-8",
        )

        inspection = inspect_config(wiki)

        assert inspection.state is AgentConfigState.VALID
        assert inspection.data["custom_extension"] == {"kept": True}
        assert inspection.data["rendered_profile"] == "compact"

    @pytest.mark.parametrize(
        "render_state",
        [
            {"rendered_profile": "compact"},
            {
                "rendered_profile": "future",
                "render_profile_version": 1,
                "render_reason": "reference-current",
            },
            {
                "rendered_profile": "compact",
                "render_profile_version": 2,
                "render_reason": "reference-current",
            },
            {
                "rendered_profile": "compact",
                "render_profile_version": 1,
                "render_reason": "future",
            },
        ],
    )
    def test_inspection_rejects_partial_or_unsupported_render_state(
        self, tmp_path, render_state
    ):
        os.chdir(tmp_path)
        wiki = tmp_path / "docs" / "wiki"
        wiki.mkdir(parents=True)
        config_path = wiki / ".llm-wiki-agent"
        config_path.write_text(
            json.dumps({"agent": "generic", **render_state}),
            encoding="utf-8",
        )

        inspection = inspect_config(wiki)

        assert inspection.state is AgentConfigState.INVALID
        assert "rendered_profile" not in inspection.data
        assert "render_profile_version" not in inspection.data
        assert "render_reason" not in inspection.data

    def test_inspection_classifies_invalid_utf8_without_raising(self, tmp_path):
        os.chdir(tmp_path)
        wiki = tmp_path / "docs" / "wiki"
        wiki.mkdir(parents=True)
        config_path = wiki / ".llm-wiki-agent"
        config_path.write_bytes(b"{\xff}")

        inspection = inspect_config(wiki)

        assert inspection.state is AgentConfigState.INVALID
        assert inspection.reason == "invalid-config-encoding"
        assert inspection.data["agent"] == "generic"

    @pytest.mark.parametrize(
        "payload",
        [
            [],
            {"agent": "generic", "quality_hints": 1},
            {"agent": "generic", "reference_skill": 0},
            {"agent": "generic", "issue_reporting": "false"},
        ],
    )
    def test_inspection_rejects_nonobject_and_bool_like_known_values(
        self, tmp_path, payload
    ):
        os.chdir(tmp_path)
        wiki = tmp_path / "docs" / "wiki"
        wiki.mkdir(parents=True)
        (wiki / ".llm-wiki-agent").write_text(
            json.dumps(payload),
            encoding="utf-8",
        )

        assert inspect_config(wiki).state is AgentConfigState.INVALID

    def test_atomic_config_failure_preserves_previous_bytes(
        self, tmp_path, monkeypatch
    ):
        os.chdir(tmp_path)
        wiki = tmp_path / "docs" / "wiki"
        wiki.mkdir(parents=True)
        write_config(wiki, {"agent": "generic", "custom": "before"})
        config_path = wiki / ".llm-wiki-agent"
        before = config_path.read_bytes()

        def fail_write(_path, _payload):
            raise OSError("injected config write failure")

        monkeypatch.setattr(config_module, "atomic_write_private_bytes", fail_write)
        with pytest.raises(OSError, match="injected"):
            write_config(wiki, {"agent": "claude", "custom": "after"})

        assert config_path.read_bytes() == before

    def test_snapshot_bound_config_write_preserves_concurrent_update(self, tmp_path):
        os.chdir(tmp_path)
        wiki = tmp_path / "docs" / "wiki"
        wiki.mkdir(parents=True)
        write_config(wiki, {"agent": "generic", "extension": {"owner": "initial"}})
        inspection = inspect_config(wiki)
        assert inspection.raw_bytes is not None

        concurrent = {
            "agent": "generic",
            "extension": {"owner": "concurrent"},
            "pending_cleanup_agent": "claude",
            "pending_cleanup_reference": True,
        }
        write_config(wiki, concurrent)
        config_path = wiki / ".llm-wiki-agent"
        concurrent_bytes = config_path.read_bytes()

        with pytest.raises(OSError, match="changed after preflight"):
            write_config(
                wiki,
                {"agent": "generic", "extension": {"owner": "stale"}},
                expected_existing=inspection.raw_bytes,
            )

        assert config_path.read_bytes() == concurrent_bytes

    def test_multiple_config_homes_fail_closed(self, tmp_path):
        os.chdir(tmp_path)
        Path(".git").mkdir()
        wiki = Path("docs/wiki")
        wiki.mkdir(parents=True)
        (Path(".git") / ".llm-wiki-agent").write_text(
            '{"agent":"generic"}',
            encoding="utf-8",
        )
        (wiki / ".llm-wiki-agent").write_text(
            '{"agent":"claude"}',
            encoding="utf-8",
        )

        inspection = inspect_config(wiki)

        assert inspection.state is AgentConfigState.INVALID
        assert inspection.reason == "multiple-agent-config-homes"
        assert config_requires_manual_recovery(inspection)

    def test_config_rejects_symlinked_git_ancestor_without_outside_write(
        self, tmp_path
    ):
        project = tmp_path / "project"
        outside = tmp_path / "outside"
        project.mkdir()
        outside.mkdir()
        try:
            (project / ".git").symlink_to(outside, target_is_directory=True)
        except OSError:
            pytest.skip("Directory symlinks are unavailable to this test account.")
        os.chdir(project)

        inspection = inspect_config("docs/llm_wiki")
        assert inspection.state is AgentConfigState.INVALID
        assert inspection.reason == "config-path-unsafe"

        with pytest.raises(PathValidationError, match="unsafe component"):
            write_config(
                "docs/llm_wiki",
                {"agent": "generic", "quality_hints": True},
            )
        assert not (outside / ".llm-wiki-agent").exists()

    def test_config_parent_rebind_at_guarded_write_does_not_escape(
        self, tmp_path, monkeypatch
    ):
        project = tmp_path / "project"
        outside = tmp_path / "outside"
        project.mkdir()
        (project / ".git").mkdir()
        outside.mkdir()
        os.chdir(project)
        original_write = config_module.atomic_write_private_bytes

        def redirect_then_write(path, payload):
            (project / ".git").rename(project / ".git-held")
            (project / ".git").symlink_to(outside, target_is_directory=True)
            return original_write(path, payload)

        monkeypatch.setattr(
            config_module,
            "atomic_write_private_bytes",
            redirect_then_write,
        )

        with pytest.raises(OSError):
            write_config("docs/llm_wiki", {"agent": "generic"})

        assert not (outside / ".llm-wiki-agent").exists()

    def test_config_rejects_parent_traversal_fallback_without_outside_write(
        self, tmp_path
    ):
        project = tmp_path / "project"
        project.mkdir()
        os.chdir(project)

        inspection = inspect_config("../outside-wiki")
        assert inspection.state is AgentConfigState.INVALID
        assert inspection.reason == "config-path-unsafe"

        with pytest.raises(PathValidationError, match="unsafe component"):
            write_config("../outside-wiki", {"agent": "generic"})
        assert not (tmp_path / "outside-wiki" / ".llm-wiki-agent").exists()

    @pytest.mark.parametrize(
        "pending",
        [
            {"pending_cleanup_agent": "generic"},
            {"pending_cleanup_reference": True},
            {
                "pending_cleanup_agent": "generic",
                "pending_cleanup_reference": "yes",
            },
            {
                "pending_cleanup_agent": "claude",
                "pending_cleanup_reference": True,
            },
        ],
    )
    def test_inspection_rejects_partial_invalid_or_same_agent_pending_state(
        self, tmp_path, pending
    ):
        os.chdir(tmp_path)
        wiki = tmp_path / "docs" / "wiki"
        wiki.mkdir(parents=True)
        (wiki / ".llm-wiki-agent").write_text(
            json.dumps({"agent": "claude", **pending}),
            encoding="utf-8",
        )

        inspection = inspect_config(wiki)

        assert inspection.state is AgentConfigState.INVALID
        if pending.get("pending_cleanup_agent") == "generic":
            assert inspection.data["pending_cleanup_agent"] == "generic"
        else:
            assert "pending_cleanup_agent" not in inspection.data
        if pending == {"pending_cleanup_reference": True}:
            assert inspection.data["pending_cleanup_reference"] is True
        else:
            assert "pending_cleanup_reference" not in inspection.data

    def test_inspection_retains_complete_cross_agent_pending_state(self, tmp_path):
        os.chdir(tmp_path)
        wiki = tmp_path / "docs" / "wiki"
        wiki.mkdir(parents=True)
        (wiki / ".llm-wiki-agent").write_text(
            json.dumps(
                {
                    "agent": "claude",
                    "pending_cleanup_agent": "generic",
                    "pending_cleanup_reference": True,
                }
            ),
            encoding="utf-8",
        )

        inspection = inspect_config(wiki)

        assert inspection.state is AgentConfigState.VALID
        assert inspection.data["pending_cleanup_agent"] == "generic"
        assert inspection.data["pending_cleanup_reference"] is True

    def test_invalid_agent_retains_individually_valid_pending_as_untrusted_evidence(
        self, tmp_path
    ):
        os.chdir(tmp_path)
        wiki = tmp_path / "docs" / "wiki"
        wiki.mkdir(parents=True)
        (wiki / ".llm-wiki-agent").write_text(
            json.dumps(
                {
                    "agent": "future-agent",
                    "pending_cleanup_agent": "generic",
                    "pending_cleanup_reference": True,
                }
            ),
            encoding="utf-8",
        )

        inspection = inspect_config(wiki)

        assert inspection.state is AgentConfigState.INVALID
        assert inspection.data["agent"] == "generic"
        assert inspection.data["pending_cleanup_agent"] == "generic"
        assert inspection.data["pending_cleanup_reference"] is True


class TestGitIgnoreMatcher:
    @pytest.mark.parametrize(
        ("line", "expected"),
        [
            ("generated/ ", "generated/"),
            ("generated/   ", "generated/"),
            (r"literal\ ", "literal "),
            (r"literal\ /", "literal /"),
            (r"mixed\  ", "mixed "),
            (r"two\ \ ", "two  "),
            (r"two\\ ", r"two\\"),
            (r"three\\\ ", "three\\\\ "),
            (r"two words \ ", "two words  "),
            ("   ", ""),
            ("generated/\t", "generated/\t"),
            ("generated/ \t", "generated/ \t"),
        ],
    )
    def test_normalizes_only_unescaped_trailing_ascii_spaces(self, line, expected):
        assert _normalize_gitignore_trailing_spaces(line) == expected

    def test_normalizes_trailing_spaces_before_parsing_rule_syntax(self, tmp_path):
        gitignore = tmp_path / ".gitignore"
        gitignore.write_bytes(
            b"   \r\n"
            b".shared/ \r\n"
            b".agent/   \r\n"
            b"!kept/ \r\n"
            b"/root/ \r\n"
            b"literal\\ \r\n"
            b"literal-dir\\ /\r\n"
            b"mixed\\  \r\n"
            b"two\\ \\ \r\n"
            b"tabbed\t \r\n"
        )

        rules = _parse_gitignore_file(gitignore)
        assert [
            (
                rule.pattern,
                rule.negated,
                rule.directory_only,
                rule.anchored,
            )
            for rule in rules
        ] == [
            (".shared", False, True, False),
            (".agent", False, True, False),
            ("kept", True, True, False),
            ("root", False, True, True),
            ("literal ", False, False, False),
            ("literal-dir ", False, True, False),
            ("mixed ", False, False, False),
            ("two  ", False, False, False),
            ("tabbed\t", False, False, False),
        ]

        matcher = build_gitignore_matcher(tmp_path)
        assert matcher.is_ignored(".shared/example.py")
        assert matcher.is_ignored("pkg/.agent/example.py")
        assert not matcher.is_ignored("kept/example.py")
        assert matcher.is_ignored("root/example.py")
        assert not matcher.is_ignored("pkg/root/example.py")
        assert matcher.is_ignored("literal ")
        assert matcher.is_ignored("literal-dir /example.py")
        assert matcher.is_ignored("mixed ")
        assert matcher.is_ignored("two  ")
        assert not matcher.is_ignored("two ")
        assert matcher.is_ignored("tabbed\t")

    def test_supports_root_anchored_negation_and_dir_patterns(self, tmp_path):
        (tmp_path / ".gitignore").write_text(
            "/root_only.py\nbuild/\n*.pyc\n!keep.pyc\n**/cache/*.json\n",
            encoding="utf-8",
        )
        matcher = build_gitignore_matcher(tmp_path)

        assert matcher.is_ignored("root_only.py")
        assert not matcher.is_ignored("pkg/root_only.py")
        assert matcher.is_ignored("build/out.py")
        assert matcher.is_ignored("pkg/build/out.py")
        assert matcher.is_ignored("x.pyc")
        assert not matcher.is_ignored("keep.pyc")
        assert matcher.is_ignored("pkg/cache/data.json")

    def test_nested_gitignore_applies_to_subtree(self, tmp_path):
        nested = tmp_path / "pkg"
        nested.mkdir()
        (nested / ".gitignore").write_text("generated/\n", encoding="utf-8")
        matcher = build_gitignore_matcher(tmp_path)

        assert matcher.is_ignored("pkg/generated/out.py")
        assert not matcher.is_ignored("generated/out.py")
