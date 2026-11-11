"""Read-only, standard-library verification of canonical shard coverage.

Native aggregation uses the pinned coverage implementation. Promotion verifies
its authenticated output and the complete raw line union without installing or
executing a candidate or a third-party coverage reader.
"""

from __future__ import annotations

from contextlib import closing
import hashlib
import io
from pathlib import Path, PurePosixPath
import sqlite3
import stat
import tokenize
import xml.etree.ElementTree as ET


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def source_manifest(package: Path) -> dict:
    paths = sorted(package.rglob("*.py"))
    require(bool(paths), "coverage source inventory is empty")
    require(not any(path.is_symlink() for path in paths), "redirected coverage source")
    return {
        path.relative_to(package).as_posix(): {
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "line_count": len(path.read_bytes().splitlines()),
        }
        for path in paths
    }


def raw_lines(path: Path, roots: list[str], sources: dict) -> dict[str, list[int]]:
    metadata = path.lstat()
    require(stat.S_ISREG(metadata.st_mode) and 0 < metadata.st_size <= 64 * 1024 * 1024,
            "unsafe or oversized coverage database")
    require(isinstance(roots, list) and 1 <= len(roots) <= 2
            and len(set(roots)) == len(roots), "invalid coverage source roots")
    prefixes = [PurePosixPath(root) for root in roots]
    require(all(root.is_absolute() and ".." not in root.parts for root in prefixes),
            "invalid coverage source prefix")
    result: dict[str, set[int]] = {}
    with closing(sqlite3.connect(path.resolve().as_uri() + "?mode=ro&immutable=1", uri=True)) as db:
        db.setlimit(sqlite3.SQLITE_LIMIT_LENGTH, 64 * 1024 * 1024)
        require(not db.execute("SELECT 1 FROM sqlite_master WHERE type IN ('view', 'trigger') LIMIT 1").fetchall(),
                "coverage database contains executable schema objects")
        require(db.execute("SELECT version FROM coverage_schema LIMIT 2").fetchall() == [(7,)],
                "unsupported coverage database schema")
        rows = db.execute("SELECT key, value FROM meta LIMIT 33").fetchall()
        require(len(rows) <= 32 and len(dict(rows)) == len(rows), "invalid coverage metadata")
        require(dict(rows).get("has_arcs") == "0", "coverage branch policy differs")
        # The frozen flags never request per-test/dynamic coverage contexts.
        contexts = db.execute("SELECT id, context FROM context LIMIT 2").fetchall()
        require(len(contexts) == 1 and type(contexts[0][0]) is int
                and contexts[0][0] > 0 and contexts[0][1] == "",
                "coverage context policy differs")
        context_id = contexts[0][0]
        maximum = len(sources) * len(prefixes)
        rows = db.execute("SELECT id, path FROM file LIMIT ?", (maximum + 1,)).fetchall()
        require(0 < len(rows) <= maximum and len(dict(rows)) == len(rows)
                and len({row[1] for row in rows}) == len(rows), "invalid coverage file rows")
        files = {}
        for file_id, filename in rows:
            require(type(file_id) is int and file_id > 0 and isinstance(filename, str)
                    and len(filename) <= 4096, "invalid coverage file identity")
            relative = PurePosixPath(filename)
            matches = [root for root in prefixes if relative.is_relative_to(root)]
            require(len(matches) == 1 and ".." not in relative.parts,
                    "coverage measured outside candidate provider")
            name = relative.relative_to(matches[0]).as_posix()
            require(name in sources, "coverage source is not in frozen provider")
            files[file_id] = name
            result.setdefault(name, set())
        rows = db.execute("SELECT file_id, context_id, numbits FROM line_bits LIMIT ?", (len(files) + 1,)).fetchall()
        require(len(rows) <= len(files), "coverage line row budget exceeded")
        seen = set()
        for file_id, row_context, bits in rows:
            require(type(file_id) is int and type(row_context) is int
                    and file_id in files and row_context == context_id and file_id not in seen,
                    "invalid or duplicate coverage line rows")
            seen.add(file_id)
            name = files[file_id]
            bound = max(1, sources[name]["line_count"])
            require(isinstance(bits, bytes) and len(bits) <= bound // 8 + 1,
                    "coverage bitset exceeds frozen source line bound")
            result[name].update(index * 8 + bit for index, byte in enumerate(bits)
                                for bit in range(8) if byte & (1 << bit))
        require(not db.execute("SELECT 1 FROM arc LIMIT 1").fetchall(),
                "coverage branch records are not permitted")
    for name, lines in result.items():
        if sources[name]["line_count"] == 0 and lines == {0}:
            lines.clear()
        require(all(0 < line <= max(1, sources[name]["line_count"]) for line in lines),
                "invalid executed coverage line")
    return {name: sorted(lines) for name, lines in result.items()}


def statement_inventory(receipt: dict, sources: dict) -> dict:
    statements = receipt.get("statements")
    if not isinstance(statements, dict):
        raise ValueError("coverage omitted frozen statement inventories")
    require(set(statements) == set(sources), "coverage omitted frozen statement inventories")
    for name, lines in statements.items():
        require(isinstance(lines, list) and all(type(line) is int for line in lines)
                and lines == sorted(set(lines))
                and all(0 < line <= sources[name]["line_count"] for line in lines),
                "invalid coverage statement inventory")
    return statements


def logical_statement_hits(source: bytes, executed: list[int]) -> set[int]:
    """Attribute physical trace events to their Python logical statement."""
    hits = set(executed)
    beginning = None
    trivia = {tokenize.ENCODING, tokenize.COMMENT, tokenize.NL,
              tokenize.INDENT, tokenize.DEDENT, tokenize.ENDMARKER}
    try:
        for item in tokenize.tokenize(io.BytesIO(source).readline):
            if item.type in trivia:
                continue
            if item.type == tokenize.NEWLINE:
                if beginning is not None and item.end[0] > beginning:
                    physical = hits.intersection(range(beginning, item.end[0] + 1))
                    if physical:
                        hits.difference_update(physical)
                        hits.add(beginning)
                beginning = None
            elif beginning is None:
                beginning = item.start[0]
    except (tokenize.TokenError, IndentationError, SyntaxError, UnicodeError) as error:
        raise ValueError("coverage logical statement mapping failed") from error
    return hits


def validate_combination(directory: Path, shards: list[Path], package: Path, load) -> None:
    sources = source_manifest(package)
    union: dict[str, set[int]] = {name: set() for name in sources}
    statement_map = None
    for shard in shards:
        receipt = load(shard / "coverage.json")
        require(set(receipt) == {"schema_version", "sources", "source_roots", "statements", "lines"}
                and receipt["schema_version"] == "agent-wiki-core-shard-coverage/v2"
                and receipt["sources"] == sources, "coverage source identity differs")
        current_statements = statement_inventory(receipt, sources)
        if statement_map is None:
            statement_map = current_statements
        require(statement_map == current_statements, "shard coverage statement inventories differ")
        observed = raw_lines(shard / "coverage.data", receipt["source_roots"], sources)
        require(observed == receipt["lines"], "coverage receipt differs from raw data")
        for name, lines in observed.items():
            union.setdefault(name, set()).update(lines)
    if statement_map is None:
        raise ValueError("coverage is missing every shard statement inventory")
    joined = load(directory / "coverage.json")
    require(set(joined) == {"schema_version", "sources", "source_roots", "statements", "lines"}
            and joined["schema_version"] == "agent-wiki-core-shard-coverage/v2"
            and joined["sources"] == sources, "combined coverage source identity differs")
    require(statement_inventory(joined, sources) == statement_map, "combined coverage statement inventory differs")
    require(joined["lines"] == {name: sorted(lines) for name, lines in union.items()}
            == raw_lines(directory / "coverage.data", joined["source_roots"], sources),
            "combined coverage is not the complete raw shard union")
    require(set(joined["lines"]) == set(sources), "coverage omitted frozen source files")
    xml = ET.parse(directory / "coverage-core-ubuntu-3.11.xml").getroot()
    seen = set()
    statements = covered = 0
    for entry in xml.iter("class"):
        name = entry.attrib["filename"]
        prefix = "src/llm_wiki_cli/"
        if name.startswith(prefix):
            name = name[len(prefix):]
        require(name in sources and name not in seen, "coverage XML source inventory differs")
        seen.add(name)
        source = (package / name).read_bytes()
        require(hashlib.sha256(source).hexdigest() == sources[name]["sha256"],
                "coverage XML source identity differs")
        # XML uses logical statements; the checked raw union remains physical.
        executed = logical_statement_hits(source, joined["lines"][name])
        line_ids = set()
        for line in entry.findall("./lines/line"):
            number, hits = int(line.attrib["number"]), int(line.attrib["hits"])
            require(0 < number <= max(1, sources[name]["line_count"])
                    and number not in line_ids and hits >= 0,
                    "invalid coverage XML line")
            line_ids.add(number)
            require((hits > 0) == (number in executed),
                    "coverage XML hits differ from raw union")
            statements += 1
            covered += hits > 0
        require(line_ids == set(statement_map[name]), "coverage XML omitted executable statements")
    require(seen == set(sources), "coverage XML omitted frozen source files")
    require(statements > 0 and int(xml.attrib["lines-valid"]) == statements
            and int(xml.attrib["lines-covered"]) == covered,
            "coverage XML counters differ")
    require(abs(float(xml.attrib["line-rate"]) - covered / statements) < 0.0001
            and covered * 100 >= 87 * statements, "combined coverage is below 87%")
