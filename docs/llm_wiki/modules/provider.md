# provider Module

**Path:** `integrations/wiki-candidate/provider.py`

## Description

Install the provider packaged with the pinned action and attest its bytes.

## Imports

| Source | Symbols |
|--------|---------|
| `hashlib` | `hashlib` |
| `importlib` | `metadata` |
| `json` | `json` |
| `llm_wiki_cli` | `llm_wiki_cli` |
| `llm_wiki_engine` | `llm_wiki_engine` |
| `os` | `os` |
| `pathlib` | `Path` |
| `re` | `re` |
| `shutil` | `shutil` |
| `subprocess` | `subprocess` |
| `sys` | `sys` |
| `tarfile` | `tarfile` |
| `tempfile` | `tempfile` |
| `tomllib` | `tomllib` |
| `venv` | `venv` |

## Local dependency map

<!-- Auto-generated local dependency summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["integrations/wiki-candidate/provider.py"]
    n1["src/llm_wiki_cli/__init__.py"]
    n0 --> n1
    click n0 "../modules/provider.md"
    click n1 "../modules/llm_wiki_cli___init__.md"
```

### Internal neighbors

| Direction | Module |
|---|---|
| Outbound | [llm_wiki_cli___init__](../modules/llm_wiki_cli___init__.md) |

### External packages

| Language | Used packages | Undeclared packages |
|---|---:|---:|
| python | 1 | 1 |

## Functions

| Function | Signature | Decorators | Description |
|----------|-----------|------------|-------------|
| `_installed_files` | `(package: Path, expected: Path, declared, prefix: str = '') -> dict[str, str]` | — | Hash installed package files that match the pinned source byte for byte. |
| `verify` | `(source: Path, receipt: Path, revision: str, repository: str) -> None` | — | — |
| `build_input` | `(provider: Path, runtime: Path) -> tuple[Path, str, str]` | — | — |
| `setup` | `(*, impact_only: bool = False) -> None` | — | — |
