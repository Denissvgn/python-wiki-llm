"""One helper policy across public SDK, CLI and MCP operation boundaries."""
from __future__ import annotations

import inspect
from typing import Any, cast
import pytest

from llm_wiki_cli import api, cli
from llm_wiki_cli.services import helper_runtime as runtime
from llm_wiki_cli.services import mcp_server


def active_operation():
    operation = runtime.current_helper_operation()
    assert operation is not None
    return operation


def test_api_omission_and_explicit_read_only_have_distinct_setup_intent():
    seen = []

    @api._api_boundary
    def read(*, read_only=True):
        operation = runtime.current_helper_operation()
        assert operation is not None
        seen.append((read_only, operation))
        return operation.policy

    assert inspect.signature(read).parameters["read_only"].default is True
    assert read() == "auto"
    assert read(read_only=True) == "never"
    assert read(read_only=False) == "auto"
    assert [item[0] for item in seen] == [True, True, False]
    assert runtime.current_helper_operation() is None
    assert len({id(item[1]) for item in seen}) == 3


def test_api_internal_read_only_forwarding_keeps_one_auto_operation():
    captured = []

    @api._api_boundary
    def inner(*, read_only=True):
        captured.append(runtime.current_helper_operation())

    @api._api_boundary
    def outer():
        captured.append(runtime.current_helper_operation())
        inner(read_only=True)

    outer()
    assert captured[0] is captured[1]
    assert captured[0].policy == "auto"


def test_api_configuration_is_not_a_long_lived_operation(tmp_path):
    captured = []

    @api._api_boundary
    def read():
        captured.append(runtime.current_helper_operation())

    with api.helper_preparation("never", cache_dir=tmp_path / "cache"):
        assert runtime.current_helper_operation() is None
        read()
        read()
    assert captured[0] is not captured[1]
    assert all(op.policy == "never" and op.cache_dir == str(tmp_path / "cache") for op in captured)
    assert runtime.current_helper_configuration() is None
    assert not (tmp_path / "cache").exists()


def test_nested_never_configuration_tightens_active_api_operation():
    captured = []

    @api._api_boundary
    def inner():
        captured.append(active_operation().policy)

    @api._api_boundary
    def outer():
        inner()
        with api.helper_preparation("never"):
            inner()
        inner()

    outer()
    assert captured == ["auto", "never", "auto"]


def test_api_request_cache_wins_over_existing_configuration(tmp_path):
    captured = []

    @api._api_boundary
    def inner():
        captured.append(runtime.current_helper_operation())

    @api._api_boundary
    def outer(*, helper_cache_dir=None):
        captured.append(runtime.current_helper_operation())
        inner()

    with api.helper_preparation("auto", cache_dir=tmp_path / "configured"):
        outer(helper_cache_dir=tmp_path / "request")
    assert captured[0] is captured[1]
    assert captured[0].cache_dir == str(tmp_path / "request")


def test_api_policy_preserves_user_exception_and_rejects_bad_read_intent():
    failure = RuntimeError("caller failure")
    with pytest.raises(RuntimeError) as raised:
        with api.helper_preparation("never"):
            raise failure
    assert raised.value is failure
    assert runtime.current_helper_configuration() is None

    @api._api_boundary
    def read(*, read_only=True):
        pytest.fail("invalid input entered operation")

    with pytest.raises(api.InvalidRequestError, match="read_only"):
        read(read_only=cast(Any, "yes"))
    assert runtime.current_helper_operation() is None


@pytest.mark.parametrize("argv", [
    ["--helper-preparation", "never", "extract"],
    ["extract", "--helper-preparation", "never"],
    ["knowledge", "storage-check", "--helper-preparation", "never"],
])
def test_cli_helper_policy_can_follow_nested_commands(argv):
    args = cli._build_parser().parse_args(argv)
    assert args.helper_preparation == "never"


@pytest.mark.parametrize("argv, expected", [
    (["extract"], "auto"),
    (["extract", "--read-only"], "never"),
    (["sync", "--dry-run"], "never"),
    (["doctor", "--capabilities"], "never"),
    (["prepare-extractors", "--plan"], "never"),
])
def test_cli_resolves_mode_before_dispatch(monkeypatch, argv, expected):
    seen = []
    monkeypatch.setattr("sys.argv", ["llm-wiki", *argv])
    monkeypatch.setattr(cli, "_dispatch_command", lambda args: seen.append(active_operation().policy))
    cli.main()
    assert seen == [expected]
    assert runtime.current_helper_operation() is None


@pytest.mark.parametrize("argv", [
    ["extract", "--read-only", "--helper-preparation", "auto"],
    ["prepare-extractors", "--helper-preparation", "never"],
    ["init", "--prepare-extractors", "--helper-preparation", "never"],
])
def test_cli_conflicting_setup_authority_never_dispatches(monkeypatch, argv):
    monkeypatch.setattr("sys.argv", ["llm-wiki", *argv])
    monkeypatch.setattr(cli, "_dispatch_command", lambda args: pytest.fail("conflict dispatched"))
    with pytest.raises(SystemExit) as raised:
        cli.main()
    assert raised.value.code == 1
    assert runtime.current_helper_operation() is None


def test_cli_mcp_does_not_retain_an_operation_for_server_lifetime(monkeypatch):
    seen = []
    monkeypatch.setattr("sys.argv", ["llm-wiki", "mcp", "--helper-preparation", "never"])
    monkeypatch.setattr(cli, "_dispatch_command", lambda args: seen.append((runtime.current_helper_operation(), args.helper_preparation)))
    cli.main()
    assert seen == [(None, "never")]


@pytest.mark.parametrize("policy", ["auto", "never"])
def test_mcp_opens_fresh_request_bindings_without_workspace_setup(tmp_path, monkeypatch, policy):
    captured = []

    def inspect_concept(*args, **kwargs):
        captured.append(runtime.current_helper_operation())
        return {"state": "observed"}

    monkeypatch.setattr(mcp_server.public_api, "inspect_concept", inspect_concept)
    service = mcp_server.McpWikiService(src_dir=str(tmp_path), helper_preparation=policy,
                                      helper_cache_dir=str(tmp_path / "cache"))
    assert service.inspect_concept("modules/foo") == {"state": "observed"}
    assert service.inspect_concept("modules/foo") == {"state": "observed"}
    assert captured[0] is not captured[1]
    assert all(op.policy == policy and op.cache_dir == str(tmp_path / "cache") for op in captured)
    assert not (tmp_path / "cache").exists()
    assert runtime.current_helper_operation() is None


def test_mcp_auto_respects_stricter_host_configuration(tmp_path, monkeypatch):
    seen = []
    monkeypatch.setattr(mcp_server.public_api, "inspect_concept",
                        lambda *args, **kwargs: seen.append(active_operation().policy) or {})
    service = mcp_server.McpWikiService(src_dir=str(tmp_path))
    with api.helper_preparation("never"):
        service.inspect_concept("modules/foo")
    assert seen == ["never"]


@pytest.mark.parametrize("wrapped", [False, True])
def test_preparation_failure_is_operational_with_bounded_cause(tmp_path, wrapped):
    from llm_wiki_cli.services.helper_cache import HelperPreparationError

    @api._api_boundary
    def read():
        failure = HelperPreparationError(
            "typescript", "npm exited 1: " + "download notice " * 100 + "EINTEGRITY checksum mismatch",
            tmp_path / "selected-cache",
        )
        if wrapped:
            raise ValueError("service wrapper") from failure
        raise failure

    with pytest.raises(api.WorkspaceStateError) as raised:
        read()
    assert raised.value.code == "helper-preparation-failed"
    assert raised.value.details is not None
    assert raised.value.details["language"] == "typescript"
    assert len(raised.value.details["reason"]) <= 500
    assert raised.value.details["reason"].startswith("npm exited 1:")
    assert raised.value.details["reason"].endswith("EINTEGRITY checksum mismatch")
    assert raised.value.details["cache_root"] == str(tmp_path / "selected-cache")
    assert runtime.current_helper_operation() is None


def test_mcp_preparation_error_keeps_operational_code(tmp_path, monkeypatch):
    from llm_wiki_cli.services.helper_cache import HelperPreparationError

    def read(*args, **kwargs):
        raise HelperPreparationError(
            "go", "go exited 1: " + "building " * 100 + "disk quota exceeded", tmp_path,
        )

    monkeypatch.setattr(mcp_server.public_api, "inspect_concept", read)
    service = mcp_server.McpWikiService(src_dir=str(tmp_path))
    with pytest.raises(mcp_server.McpWikiError) as raised:
        service.inspect_concept("modules/foo")
    assert raised.value.code == "helper-preparation-failed"
    assert raised.value.data is not None
    assert raised.value.data["language"] == "go"
    assert raised.value.data["reason"].endswith("disk quota exceeded")
    assert raised.value.data["cache_root"] == str(tmp_path)


def test_api_configuration_propagates_progress_without_calling_it():
    messages = []
    callback = messages.append

    @api._api_boundary
    def read():
        assert active_operation().progress is callback
        assert messages == []

    with api.helper_preparation("auto", progress=callback):
        read()
    assert messages == []
