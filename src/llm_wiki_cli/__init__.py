"""LLM Wiki CLI."""
from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version("llm-wiki-cli")
except PackageNotFoundError:
    __version__ = "0.0.0"  # fallback for editable installs not yet built
