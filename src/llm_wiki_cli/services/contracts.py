"""Stable machine-readable contracts exposed by source-adapter commands.

Dependency/load-order architecture decisions stay additive under the current
extract contract: deep Python inventory may include ``module_calls`` only when
module-level side effects exist, and ``extract --deep`` may include a top-level
``dependencies`` block. Python dependency reconciliation treats
``sys.stdlib_module_names`` as the stdlib source when available, falls back to
the bundled Python 3.9 list in dependency analysis, and uses the curated
import-to-distribution aliases there with optional project overrides from
``[tool.llm-wiki.dependency-aliases]``.
"""

from __future__ import annotations

EXTRACT_SCHEMA_VERSION = "llm-wiki-extract/v1"
BOOTSTRAP_SUMMARY_SCHEMA_VERSION = "llm-wiki-bootstrap-summary/v1"
