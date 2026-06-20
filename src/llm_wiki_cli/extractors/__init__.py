"""Extractor plugin architecture for agent-wiki-cli."""

from __future__ import annotations

from typing import Protocol


class ExtractorProtocol(Protocol):
    """Protocol that all language extractors must implement.

    An extractor is responsible for scanning source files of a particular
    language, parsing their structure (classes, functions, imports, etc.)
    and returning a uniform inventory dict.

    Each value in the returned inventory dict **must** include a
    ``"language"`` key identifying which language produced the entry.
    """

    def extract(
        self,
        src_dir: str,
        only_files: list[str] | None = None,
        deep: bool = False,
    ) -> dict:
        """Scan *src_dir* and return an inventory dict mapping filepath → file_entry.

        Parameters
        ----------
        src_dir:
            Root directory to scan.
        only_files:
            Optional list of paths (relative to *src_dir*) to restrict
            extraction to.  When ``None``, all files of the supported
            language found under *src_dir* are scanned.
        deep:
            When ``True``, include enriched data (docstrings, attributes,
            method details, imports).  When ``False``, return a slim
            name-only summary suitable for quick index generation.

            In deep mode a function/method entry **may** carry an optional
            ``"data_effects"`` block for inputs, selected reads/writes,
            returns, and bounded boundary effects such as filesystem,
            environment, process, network, output, and logging calls. The field
            is additive and omitted when no extractable effects exist.

            In deep mode a function/method entry **may** also carry an
            optional ``"calls"`` list of in-body call targets
            (``{"name", "attr"?, "line", "args"?, "kwargs"?}``) used for
            call-edge resolution. ``args`` and ``kwargs`` contain compact
            expression summaries when emitted. The field is additive: it is
            omitted when empty, and consumers must tolerate its absence for
            extractors that do not emit it.

        Returns
        -------
        dict
            ``{filepath: file_entry}`` where each ``file_entry`` contains
            at minimum ``"classes"``, ``"functions"``, and ``"language"``.
        """
        ...
