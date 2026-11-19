"""Code-documentation source tables: built-in extractors by language and
container build file patterns.

``llm_wiki_cli.config`` re-exports every name for existing callers.
"""

from __future__ import annotations


# Docker file discovery patterns
DOCKERFILE_PATTERNS: list[str] = [
    "Dockerfile",
    "Dockerfile.*",
    "*.dockerfile",
]

COMPOSE_PATTERNS: list[str] = [
    "docker-compose.yml",
    "docker-compose.*.yml",
    "docker-compose.yaml",
    "docker-compose.*.yaml",
    "compose.yml",
    "compose.*.yml",
    "compose.yaml",
    "compose.*.yaml",
]

# Registry mapping language name → extractor entry point.
# Format: "module.path:ClassName"
# New extractors (TypeScript, Go, Rust, …) are registered here.
EXTRACTOR_REGISTRY: dict[str, str] = {
    "python": "llm_wiki_cli.extractors.python_extractor:PythonExtractor",
    "typescript": "llm_wiki_cli.extractors.ts_extractor:TypeScriptExtractor",
    "go": "llm_wiki_cli.extractors.go_extractor:GoExtractor",
    "rust": "llm_wiki_cli.extractors.rust_extractor:RustExtractor",
    "haskell": "llm_wiki_cli.extractors.haskell_extractor:HaskellExtractor",
}
