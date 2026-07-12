from __future__ import annotations

import errno

import pytest

from llm_wiki_cli.services.resource_diagnostics import (
    format_resource_failure,
    resource_failure_hint,
)


@pytest.mark.parametrize(
    ("error_number", "marker"),
    [
        (error_number, marker)
        for name, marker in [
            ("ENOSPC", "does not identify a single cause"),
            ("EMFILE", "process file-descriptor capacity"),
            ("ENFILE", "host file-descriptor capacity"),
            ("ENOMEM", "Memory capacity"),
            ("EAGAIN", "temporary process, thread, or file resource"),
        ]
        if (error_number := getattr(errno, name, None)) is not None
    ],
)
def test_errno_resource_failures_have_portable_manual_recovery_guidance(
    error_number, marker
):
    hint = resource_failure_hint(OSError(error_number, "capacity exhausted"))

    assert hint is not None
    assert marker in hint
    assert "manually retry once with --jobs 1" in hint
    assert "no automatic retry was attempted" in hint


def test_memory_error_has_recovery_guidance():
    message = format_resource_failure(MemoryError())

    assert message.startswith("MemoryError. Resource guidance:")
    assert "Memory capacity was exhausted" in message


def test_wrapped_resource_failure_is_discovered_through_cause():
    error_number = getattr(errno, "EMFILE", None)
    if error_number is None:
        pytest.skip("EMFILE is not defined on this platform")
    inner = OSError(error_number, "too many open files")
    outer = RuntimeError("inventory failed")
    outer.__cause__ = inner

    hint = resource_failure_hint(outer)

    assert hint is not None
    assert "EMFILE" in hint


def test_wrapped_executor_runtime_error_is_discovered_through_cause():
    inner = RuntimeError("cannot start new thread")
    outer = Exception("executor unavailable")
    outer.__cause__ = inner

    hint = resource_failure_hint(outer, executor_start=True)

    assert hint is not None
    assert "worker pool could not start" in hint


def test_generic_failure_has_no_resource_diagnosis():
    error = ValueError("bad input")

    assert resource_failure_hint(error) is None
    assert format_resource_failure(error) == "bad input"


@pytest.mark.parametrize(
    "error",
    [RuntimeError("ENOSPC while scanning"), ValueError("errno=ENOSPC")],
)
def test_resource_names_in_untyped_messages_are_not_parsed(error):
    assert resource_failure_hint(error) is None


def test_runtime_error_only_gets_executor_hint_at_executor_boundary():
    error = RuntimeError("bad runtime state")

    assert resource_failure_hint(error) is None
    assert resource_failure_hint(error, executor_start=True) is not None
