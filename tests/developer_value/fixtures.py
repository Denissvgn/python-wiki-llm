"""Small owned Python projects; no generated wiki or provider expectations.

The larger project is synthetic scale evidence, never an external repository.
Fixture generation needs no product import, installed helper, or network access.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
import random

SEED = 261003
LARGE_MODULES = 96
POLICY_SOURCE = (
    'class Batch:\n'
    '    """Keep every item up to the permitted batch limit."""\n'
    '    def cap(self, values: list[int], limit: int = 3) -> list[int]:\n'
    '        return values[:limit]\n'
    '\n'
    'def public_values() -> list[int]:\n'
    '    return Batch().cap([1, 2, 3])\n'
)
RETRY_SOURCE = '''"""Retry a transient operation with a bounded attempt count."""

def retry(operation, attempts: int = 3):
    for attempt in range(attempts - 1):
        try:
            return operation()
        except ValueError:
            if attempt == attempts - 2:
                raise ValueError("retry budget exhausted")
    raise ValueError("retry budget exhausted")
'''
TEXT_SOURCE = '''"""Normalize user-provided tags for consistent lookup."""

def normalize_tag(value: str) -> str:
    normalized = value.strip().lower()
    if not normalized:
        raise ValueError("tag cannot be blank")
    return normalized
'''
VALIDATION_SOURCE = '''"""Validate the permitted batch limit."""

def validate_limit(limit: int) -> int:
    if limit <= 0:
        raise ValueError("batch limit must be positive")
    return limit
'''


def _library() -> dict[str, str]:
    return {
        "policy.py": POLICY_SOURCE,
        "retry.py": RETRY_SOURCE,
        "text.py": TEXT_SOURCE,
        "validation.py": VALIDATION_SOURCE,
        "client.py": '''from policy import Batch
from retry import retry

def assigned_values():
    batch = Batch()
    return batch.cap([1, 2, 3])

def fetch(operation):
    return retry(operation)
''',
        "scope.py": '''"""Deliberately repeated declarations retain separate occurrences."""

def sibling(value: int = 9) -> int:
    return value + 1

class Repeated:
    def touch(self, value):
        return value + 1

class Repeated:
    def touch(self, value):
        return value + 2

def outer(value):
    def inner(value):
        return value + 1
    return inner(value)
''',
    }


def _service() -> dict[str, str]:
    return {
        "policy.py": POLICY_SOURCE,
        "handlers.py": '''"""List a bounded page of items for a recognized tenant."""
from guards import validate_tenant
from policy import Batch as BatchPolicy
from store import Store

def list_items(tenant: str, items: list[int], limit: int = 20) -> list[int]:
    validate_tenant(tenant)
    if limit <= 0:
        raise ValueError("invalid item limit")
    return BatchPolicy().cap(items, limit)

def save_item(store: Store, tenant: str, request_id: str, value: int):
    validate_tenant(tenant)
    return store.save(request_id, value)
''',
        "guards.py": '''"""Reject unknown tenants before reading or writing records."""
KNOWN_TENANTS = {"acme", "sample"}

def validate_tenant(tenant: str) -> str:
    if tenant not in KNOWN_TENANTS:
        raise PermissionError("unknown tenant")
    return tenant
''',
        "store.py": '''"""Deduplicate writes using an in-memory request identifier."""
ALLOW_WRITES = True

class Store:
    def __init__(self):
        self.values = {}

    def save(self, request_id: str, value: int) -> int:
        if not ALLOW_WRITES:
            raise PermissionError("write refused")
        if request_id not in self.values:
            self.values[request_id] = value
        return self.values[request_id]
''',
        "dynamic.py": '''"""These dispatch patterns do not establish a unique receiver."""
from policy import Batch as BatchPolicy

class OtherBatch:
    def cap(self, values, limit=9):
        return values[:limit]

def factory_values(factory):
    receiver = factory()
    return receiver.cap([1, 2, 3])

def shadowed_values(BatchPolicy):
    return BatchPolicy().cap([1, 2, 3])

def conflicting_values(flag):
    receiver = BatchPolicy()
    if flag:
        receiver = OtherBatch()
    return receiver.cap([1, 2, 3])

def rebound_values():
    receiver = BatchPolicy()
    receiver = object()
    return receiver.cap([1, 2, 3])
''',
        "cli.py": '''"""Route explicit local service commands."""
from handlers import list_items

def main():
    return list_items("acme", [1, 2, 3], 2)

if __name__ == "__main__":
    print(main())
''',
    }


def _large() -> dict[str, str]:
    generator = random.Random(SEED)
    files = {
        "parts/__init__.py": '"""Owned deterministic scale modules."""\n',
        "rank.py": '''"""Put relevant record matches first using local token overlap."""

def rank_records(query: str, records: list[str]) -> list[str]:
    terms = set(query.lower().split())
    return sorted(records, key=lambda record: (-len(terms & set(record.lower().split())), record))
''',
        "catalog.py": '''"""Select records without exceeding the explicit byte budget."""
from guards import validate_catalog_access

def select_records(records: list[str], byte_budget: int = 4096) -> list[str]:
    validate_catalog_access(True)
    if sum(len(record.encode("utf-8")) for record in records) > byte_budget:
        raise ValueError("catalog exceeds selected byte budget")
    return list(records)
''',
        "search.py": '''"""Search selects the corpus, ranks records, and returns matching text."""
from catalog import select_records
from rank import rank_records

def validate_query(query: str) -> str:
    if not query.strip():
        raise ValueError("query cannot be blank")
    return query

def search_records(query: str, records: list[str]) -> list[str]:
    validate_query(query)
    selected = select_records(records)
    return rank_records(query, selected)
''',
        "cli.py": '''"""Dispatch a command through validation, search, and output formatting."""
import argparse
from guards import validate_command
from search import search_records

def format_results(records: list[str]) -> str:
    return "\\n".join(records)

def dispatch(command: str, query: str, records: list[str]) -> str:
    validate_command(command)
    if command == "search":
        return format_results(search_records(query, records))
    raise ValueError("unknown command")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("query")
    args = parser.parse_args()
    return dispatch("search", args.query, ["bounded search records", "other item"])

if __name__ == "__main__":
    print(main())
''',
    }
    guards = [
        '"""A deep validation subtree must not obscure main operation stages."""',
        '',
        'def validate_catalog_access(allowed: bool) -> bool:',
        '    if not allowed:',
        '        raise PermissionError("catalog access denied")',
        '    return allowed',
        '',
        'def validate_command(command: str) -> str:',
        '    validate_catalog_access(command == "search")',
        '    return check_00(command)',
        '',
    ]
    for number in range(36):
        guards.extend([
            f'def check_{number:02}(value: str) -> str:',
            f'    return check_{number + 1:02}(value)' if number < 35 else '    return value',
            '',
        ])
    files["guards.py"] = "\n".join(guards)
    for number in range(LARGE_MODULES):
        amount = generator.randrange(1, 1000)
        files[f"parts/part_{number:03}.py"] = (
            f'"""Scale partition {number}; deterministic local record transformation."""\n\n'
            f'class Record{number:03}:\n'
            f'    def transform(self, value: int) -> int:\n'
            f'        return value + {amount}\n\n'
            f'def transform_{number:03}(value: int) -> int:\n'
            f'    return Record{number:03}().transform(value)\n\n'
            f'def describe_{number:03}() -> str:\n'
            f'    return "partition {number:03}"\n'
        )
    return files


def projects() -> dict[str, dict[str, str]]:
    """Return detached source-only fixture bytes for all three projects."""
    return {"library": _library(), "service": _service(), "large": _large()}


def baseline_guides(name: str) -> dict[str, str]:
    """Identical authored input for every provider arm, kept outside source."""
    if name not in projects():
        raise ValueError(f"unknown owned project: {name}")
    summaries = {
        "library": "The library caps batches, retries transient operations, and normalizes tags.",
        "service": "The service validates tenants, lists bounded item pages, and deduplicates writes.",
        "large": "The search command validates access, selects records, ranks matches, and formats output.",
    }
    return {"index.md": f"# Owned {name} project\n\n{summaries[name]}\n\n"
            "Read source for runtime behavior; static observations do not prove correctness.\n"}


def source_hashes(files: dict[str, str]) -> dict[str, str]:
    return {name: hashlib.sha256(text.encode("utf-8")).hexdigest()
            for name, text in sorted(files.items())}


def materialize(name: str, project_root: Path) -> Path:
    """Create only a new or empty owned workspace; return its source root.

    No expectations, corpus manifest, generated wiki, or oracle enters the
    workspace. The caller explicitly prepares and retains wiki content.
    """
    available = projects()
    if name not in available:
        raise ValueError(f"unknown owned project: {name}")
    root = Path(project_root).absolute()
    if root.is_symlink() or any(parent.is_symlink() for parent in root.parents):
        raise ValueError("owned workspace must not follow a redirected path")
    if root.exists() and (not root.is_dir() or any(root.iterdir())):
        raise ValueError("owned workspace must be new or empty")
    root.mkdir(parents=True, exist_ok=True)
    source = root / "src"
    source.mkdir()
    for relative, text in available[name].items():
        path = source / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(text.encode("utf-8"))
    return source
