"""Keep collected test identities representable on every supported host."""

from collections.abc import Iterable


WINDOWS_ENVIRONMENT_LIMIT = 32767


def current_test_environment_units(node_id: str) -> int:
    """Count the largest pytest phase in a Windows UTF-16 environment entry."""
    # pytest replaces NULs before setting PYTEST_CURRENT_TEST. CPython's Windows
    # putenv checks the complete name=value string, not just the value. Reserve
    # its terminating NUL as well; teardown is the longest built-in phase name.
    value = f"{node_id} (teardown)".replace("\x00", "(null)")
    entry = f"PYTEST_CURRENT_TEST={value}\0"
    return len(entry.encode("utf-16-le", errors="surrogatepass")) // 2


def require_portable_node_ids(node_ids: Iterable[str]) -> None:
    """Reject oversized labels before pytest can fail in setup or teardown."""
    failures = 0
    examples = []
    for node_id in node_ids:
        size = current_test_environment_units(node_id)
        if size <= WINDOWS_ENVIRONMENT_LIMIT:
            continue
        failures += 1
        if len(examples) < 5:
            # Identify the test without dumping a potentially enormous payload.
            test = ascii(node_id.partition("[")[0][:120])
            examples.append(f"{test}: {size} UTF-16 units")
    if failures:
        extra = f"; {failures - len(examples)} more" if failures > len(examples) else ""
        raise ValueError(
            f"{failures} collected test ID(s) exceed the Windows environment "
            f"budget ({WINDOWS_ENVIRONMENT_LIMIT} UTF-16 units){extra}. "
            "Use short explicit pytest.param(..., id=...) labels; keep the full test data.\n"
            + "\n".join(examples)
        )
