"""LLM Wiki CLI."""

from importlib import metadata
from pathlib import Path
import tomllib


_DISTRIBUTION = "agent-wiki-cli"


def _provider_package_identity() -> dict[str, str]:
    # Scope discovery to the loaded provider. An unrelated project in cwd or
    # on sys.path can have its own pyproject and distribution metadata.
    location = Path(__file__).resolve().parent.parent
    distributions = list(
        metadata.Distribution.discover(name=_DISTRIBUTION, path=[str(location)])
    )
    wheels = [dist for dist in distributions if dist.read_text("WHEEL") is not None]
    if len(wheels) == 1:
        return _installed_identity(wheels[0])
    if wheels:
        raise ValueError("Multiple installed wheels claim the loaded llm-wiki provider")
    source_metadata = location.parent / "pyproject.toml"
    if location.name == "src" and source_metadata.is_file():
        # Generated egg-info can predate an edit to this provider checkout.
        try:
            project = tomllib.loads(source_metadata.read_text(encoding="utf-8"))[
                "project"
            ]
            return _identity(
                project["name"], project["version"], project["requires-python"]
            )
        except (KeyError, TypeError) as exc:
            raise ValueError("Incomplete provider project metadata") from exc
    if len(distributions) == 1:
        return _installed_identity(distributions[0])
    raise ValueError(
        "Cannot identify a unique distribution for the loaded llm-wiki provider"
    )


def _installed_identity(distribution: metadata.Distribution) -> dict[str, str]:
    record = distribution.metadata
    if any(
        len(record.get_all(field) or []) != 1
        for field in ("Name", "Version", "Requires-Python")
    ):
        raise ValueError("Incomplete or ambiguous installed provider metadata")
    return _identity(record["Name"], record["Version"], record["Requires-Python"])


def _identity(name: str, version: str, requires_python: str) -> dict[str, str]:
    if (
        name != _DISTRIBUTION
        or not isinstance(version, str)
        or not version.strip()
        or not isinstance(requires_python, str)
        or not requires_python.strip()
    ):
        raise ValueError(
            "The provider must declare its name, version and Python requirement"
        )
    return {"name": name, "version": version, "requires_python": requires_python}


try:
    __version__ = _provider_package_identity()["version"]
except (OSError, ValueError):
    # Keep a loose source copy importable when its metadata is unavailable.
    __version__ = "0.0.0"
