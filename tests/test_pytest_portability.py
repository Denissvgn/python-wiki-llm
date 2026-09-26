"""Regression controls for Windows-safe pytest environment metadata."""

import os
from pathlib import Path
import subprocess
import sys

import pytest

from tests.pytest_portability import (
    WINDOWS_ENVIRONMENT_LIMIT,
    current_test_environment_units,
    require_portable_node_ids,
)


@pytest.mark.parametrize(
    "character", ["a", "\U0001f9ea", "\0"], ids=["ascii", "astral", "nul"]
)
def test_environment_budget_includes_phase_name_encoding_and_nul_expansion(character):
    overhead = current_test_environment_units("")
    width = {"a": 1, "\U0001f9ea": 2, "\0": len("(null)")}[character]
    count = (WINDOWS_ENVIRONMENT_LIMIT - overhead) // width
    node_id = character * count
    assert current_test_environment_units(node_id) == overhead + count * width
    require_portable_node_ids([node_id])
    with pytest.raises(ValueError, match="Windows environment budget"):
        require_portable_node_ids([node_id + character])


def test_collection_error_is_bounded_and_does_not_dump_large_payloads():
    node_ids = [
        f"tests/test_policy.py::test_invalid_{i}[" + " " * 65537 + "]"
        for i in range(12)
    ]
    with pytest.raises(ValueError) as error:
        require_portable_node_ids(node_ids)
    message = str(error.value)
    assert "12 collected test ID(s)" in message and "7 more" in message
    assert "pytest.param(..., id=...)" in message
    assert len(message.encode("utf-8")) < 2048 and " " * 100 not in message


@pytest.mark.parametrize(
    "explicit_id", [False, True], ids=["auto-id-rejected", "explicit-id-full-payload"]
)
def test_real_pytest_collection_enforces_portability_before_setup(
    tmp_path, explicit_id
):
    # Load the repository's actual hook in an isolated tiny suite. All hosts
    # reproduce the native Windows limit without needing Windows emulation.
    (tmp_path / "conftest.py").write_text(
        "from tests.conftest import pytest_collection_modifyitems\n", encoding="utf-8"
    )
    value = (
        "pytest.param(b' ' * 65537, id='oversized-policy')"
        if explicit_id
        else "b' ' * 65537"
    )
    (tmp_path / "test_policy.py").write_text(
        "from pathlib import Path\nimport pytest\n"
        f"@pytest.mark.parametrize('payload', [{value}])\n"
        "def test_oversized_policy(payload):\n"
        "    assert len(payload) == 65537\n"
        "    Path('executed').write_text(str(len(payload)))\n",
        encoding="utf-8",
    )
    environment = {
        **os.environ,
        "PYTHONPATH": str(Path(__file__).resolve().parents[1]),
        "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1",
    }
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider"],
        cwd=tmp_path,
        env=environment,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    if explicit_id:
        assert result.returncode == 0, (result.stdout, result.stderr)
        assert (tmp_path / "executed").read_text() == "65537"
    else:
        assert result.returncode == pytest.ExitCode.USAGE_ERROR, (
            result.stdout,
            result.stderr,
        )
        assert "Windows environment budget" in result.stderr
        assert "test_oversized_policy" in result.stderr
        assert len(result.stderr) < 2048
        assert not (tmp_path / "executed").exists()
