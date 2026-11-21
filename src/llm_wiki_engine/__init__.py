"""Standard-library-only core of the LLM Wiki engine.

The modules in this package hold the parts of the engine that need nothing
beyond the Python standard library: canonical JSON encodings and digests,
the host boundary (processes, environment, working directory, clock), path
and request validation, the knowledge graph and evidence vocabularies, wiki
surface and media rules, search ranking, and validators for the published
JSON formats. They import only the standard library and each other.

``agent-wiki-cli`` builds the code-documentation product on top of this
package. Its ``llm_wiki_cli.services.<module>`` import paths for these
modules remain available as aliases of the same module objects.
"""

__version__ = "5.0.0"


def __getattr__(name: str):
    # The Engine loads its modules on first use, so importing the package stays cheap.
    if name == "Engine":
        from .engine import Engine

        return Engine
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
