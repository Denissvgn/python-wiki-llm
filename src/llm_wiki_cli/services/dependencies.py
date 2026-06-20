"""Internal dependency-graph analysis and external reconciliation.

Builds a module-file → module-file dependency graph from a structural
inventory's ``imports`` records, detects import cycles via strongly-connected
components, computes fan-in/fan-out metrics (Epic 2.1), and reconciles each
file's external imports against its language's declared dependency manifest —
Python (``pyproject.toml``), TypeScript/JS (``package.json``), Go (``go.mod``),
and Rust (``Cargo.toml``) — to surface undeclared and unused packages (Epic
2.2). Analogous to :mod:`llm_wiki_cli.services.entrypoints`: deterministic,
performs no LLM calls, imports only stdlib (plus the bundled ``tomli`` backport)
and :mod:`llm_wiki_cli.services.imports`, and takes the inventory as plain data
(returning plain dicts/lists). It tolerates slim or non-Python inventory entries
that omit optional fields — absence never raises.

The same module-path resolver that backs call-edge resolution
(:func:`extract_cmd.resolve_call_edges`) is reused here, so import→file
resolution stays consistent across the codebase. Imports that resolve to no
internal file (stdlib, third-party, unresolvable relatives) are collected in an
``unresolved`` bucket; the Epic 2.2 classifiers consume that bucket so an import
already resolved to an internal file is never double-counted as external.

Reconciliation is *language-partitioned*: each language pairs a manifest parser
with an import→package classifier behind a shared dispatcher. A language with
imports but no manifest (everything → undeclared) or a manifest but no imports
(everything → unused) degrades to warnings, never an exception; import→package
name mapping is best-effort per ecosystem, so undeclared/unused are advisory.
"""

from __future__ import annotations

import heapq
import json
import re
import sys
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional

from .imports import build_module_path_resolver

try:  # Python 3.11+
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - exercised on Python 3.9/3.10
    try:
        import tomli as tomllib
    except ModuleNotFoundError:  # pragma: no cover - dependency missing in ad-hoc envs
        tomllib = None  # type: ignore[assignment]


# ── Internal dependency graph (DL-101) ────────────────────────────────


def _build_symbol_file_index(inventory: dict) -> dict[str, set[str]]:
    """Map each top-level symbol name to the files that define it.

    Used only to disambiguate an import whose *module* resolves to more than
    one internal file (e.g. two packages each exposing a ``settings`` module).
    """
    index: defaultdict[str, set[str]] = defaultdict(set)
    for filepath, data in inventory.items():
        if not isinstance(data, dict):
            continue
        for cls in data.get("classes", []):
            index[cls["name"]].add(filepath)
        for fn in data.get("functions", []):
            index[fn["name"]].add(filepath)
    return index


def _resolve_target_module(module: str, name: str) -> str:
    """Return the module string to resolve for an import record.

    A purely-dotted module (``from . import local`` / ``from .. import shared``)
    carries the real target in *name*; fold it in so the resolver lands on the
    submodule file rather than the package ``__init__``.
    """
    if module and set(module) == {"."}:
        return module + name
    return module


def _resolve_internal_targets(
    imp: dict, filepath: str, resolver, symbol_index
) -> set[str]:
    """Return the internal files *imp* (from *filepath*) resolves to.

    Empty only when the import is stdlib/third-party/unresolvable; a module that
    resolves solely to its own file stays non-empty (so it is treated as an
    internal self-reference, not an undeclared external dependency — the caller
    drops the self-edge). When the module alone resolves ambiguously, narrow by
    the imported symbol's defining files.
    """
    module = imp.get("module", "") or ""
    name = imp.get("name", "") or ""
    targets = resolver.candidates(_resolve_target_module(module, name), filepath)
    if len(targets) > 1:
        narrowed = targets & symbol_index.get(name, set())
        if narrowed:
            targets = narrowed
    return targets


def build_dependency_graph(inventory: dict) -> dict:
    """Resolve each file's imports into an internal module-dependency graph.

    For every file, each ``imports`` record is resolved to an internal target
    file with the shared module-path resolver. Resolved targets become directed
    ``(from_file, to_file)`` edges (self-edges excluded, de-duplicated); imports
    that resolve to no internal file land in ``unresolved``.

    Returns ``{"edges": [(from_file, to_file), ...], "nodes": [...],
    "unresolved": [{"file", "module", "name"}, ...]}`` with every list stably
    ordered. A file that imports nothing internal still appears as an isolated
    node. Slim/non-Python entries (no ``imports``) contribute no edges and never
    raise.
    """
    resolver = build_module_path_resolver(inventory)
    symbol_index = _build_symbol_file_index(inventory)

    edges: set[tuple[str, str]] = set()
    unresolved: list[dict] = []
    nodes: set[str] = set()

    for filepath, data in inventory.items():
        if not isinstance(data, dict) or "imports" not in data:
            continue
        nodes.add(filepath)
        for imp in data.get("imports", []):
            targets = _resolve_internal_targets(imp, filepath, resolver, symbol_index)
            if not targets:
                unresolved.append(
                    {
                        "file": filepath,
                        "module": imp.get("module", "") or "",
                        "name": imp.get("name", "") or "",
                    }
                )
                continue
            for target in targets:
                if target != filepath:
                    edges.add((filepath, target))

    for source, target in edges:
        nodes.add(source)
        nodes.add(target)

    return {
        "edges": sorted(edges),
        "nodes": sorted(nodes),
        "unresolved": sorted(
            unresolved, key=lambda u: (u["file"], u["module"], u["name"])
        ),
    }


# ── Cycle detection (DL-102) ──────────────────────────────────────────


def _build_adjacency(graph: dict) -> tuple[dict[str, list[str]], set[str], set[str]]:
    """Return ``(adjacency, nodes, self_loops)`` from a dependency graph."""
    nodes: set[str] = set(graph.get("nodes", []))
    adjacency: defaultdict[str, set[str]] = defaultdict(set)
    self_loops: set[str] = set()
    for source, target in graph.get("edges", []):
        nodes.add(source)
        nodes.add(target)
        if source == target:
            self_loops.add(source)
        else:
            adjacency[source].add(target)
    return ({k: sorted(v) for k, v in adjacency.items()}, nodes, self_loops)


def detect_cycles(graph: dict) -> list[list[str]]:
    """Return the import cycles in *graph* as sorted node lists.

    Computes strongly-connected components (iterative Tarjan, so deep graphs
    never blow the recursion limit) and reports every SCC of size > 1, plus any
    explicit self-loop, as a cycle. Each cycle is a sorted node list and the
    list of cycles is itself deterministically ordered; an acyclic graph returns
    ``[]``.
    """
    adjacency, nodes, self_loops = _build_adjacency(graph)

    indices: dict[str, int] = {}
    lowlink: dict[str, int] = {}
    on_stack: dict[str, bool] = {}
    stack: list[str] = []
    counter = 0
    cycles: list[list[str]] = []

    for root in sorted(nodes):
        if root in indices:
            continue
        work: list[tuple[str, int]] = [(root, 0)]
        while work:
            node, next_child = work[-1]
            if next_child == 0:
                indices[node] = lowlink[node] = counter
                counter += 1
                stack.append(node)
                on_stack[node] = True

            neighbors = adjacency.get(node, ())
            descended = False
            for index in range(next_child, len(neighbors)):
                neighbor = neighbors[index]
                if neighbor not in indices:
                    work[-1] = (node, index + 1)
                    work.append((neighbor, 0))
                    descended = True
                    break
                if on_stack.get(neighbor):
                    lowlink[node] = min(lowlink[node], indices[neighbor])
            if descended:
                continue

            if lowlink[node] == indices[node]:
                component: list[str] = []
                while True:
                    member = stack.pop()
                    on_stack[member] = False
                    component.append(member)
                    if member == node:
                        break
                if len(component) > 1:
                    cycles.append(sorted(component))

            work.pop()
            if work:
                parent = work[-1][0]
                lowlink[parent] = min(lowlink[parent], lowlink[node])

    cycles.extend([node] for node in self_loops)
    cycles.sort()
    return cycles


# ── Fan-in / fan-out metrics (DL-103) ─────────────────────────────────


def dependency_metrics(graph: dict) -> dict:
    """Compute per-module fan-in/fan-out counts and a most-depended ranking.

    ``fan_out`` is the number of internal modules a file depends on; ``fan_in``
    is the number of internal modules that depend on it. Returns
    ``{"metrics": {file: {"fan_in", "fan_out"}}, "most_depended_on": [file, ...]}``
    where the ranking is by descending fan-in with an alphabetical tie-break.
    Counts match the edge list and the output is deterministic.
    """
    fan_in: defaultdict[str, int] = defaultdict(int)
    fan_out: defaultdict[str, int] = defaultdict(int)
    modules: set[str] = set(graph.get("nodes", []))

    for source, target in graph.get("edges", []):
        modules.add(source)
        modules.add(target)
        fan_out[source] += 1
        fan_in[target] += 1

    metrics = {
        module: {"fan_in": fan_in[module], "fan_out": fan_out[module]}
        for module in sorted(modules)
    }
    most_depended_on = sorted(modules, key=lambda m: (-fan_in[m], m))
    return {"metrics": metrics, "most_depended_on": most_depended_on}


# ══ Load / startup order (Epic 2.3) ═══════════════════════════════════════


def _condense(
    graph: dict,
) -> tuple[dict[str, str], dict[str, list[str]], list[list[str]]]:
    """Condense the graph's strongly-connected components into super-nodes.

    Returns ``(node_to_component, components, cycle_groups)`` where every node
    maps to a component representative (the smallest member), ``components``
    lists each representative's sorted members, and ``cycle_groups`` are the
    multi-module SCCs whose internal load order is indeterminate.
    """
    nodes: set[str] = set(graph.get("nodes", []))
    for source, target in graph.get("edges", []):
        nodes.add(source)
        nodes.add(target)

    node_to_component: dict[str, str] = {}
    components: dict[str, list[str]] = {}
    for cycle in detect_cycles(graph):  # SCCs (size > 1) and explicit self-loops
        representative = cycle[0]  # cycles are sorted, so this is the smallest
        components[representative] = list(cycle)
        for node in cycle:
            node_to_component[node] = representative
    for node in nodes:
        if node not in node_to_component:
            node_to_component[node] = node
            components[node] = [node]

    cycle_groups = [members for members in components.values() if len(members) > 1]
    cycle_groups.sort()
    return node_to_component, components, cycle_groups


def topological_order(graph: dict) -> dict:
    """Order modules so each loads after the internal modules it imports.

    Strongly-connected components (import cycles) are condensed into single
    nodes, the resulting DAG is Kahn-sorted with an alphabetical tie-break for
    determinism, then each component is expanded in sorted order. An edge
    ``(importer, imported)`` places ``imported`` before ``importer`` — the
    dependency loads first. Returns ``{"order": [files...], "cycle_groups":
    [[files...]]}`` where each cyclic group is surfaced (its members listed
    sorted and adjacent) rather than silently dropped, since their relative load
    order is indeterminate. Deterministic; isolated modules still appear.
    """
    node_to_component, components, cycle_groups = _condense(graph)

    # Condensed dependency edges: for importer→imported, the imported
    # component must load before the importer component.
    adjacency: defaultdict[str, set[str]] = defaultdict(set)
    for importer, imported in graph.get("edges", []):
        src, dst = node_to_component[imported], node_to_component[importer]
        if src != dst:
            adjacency[src].add(dst)

    indegree: dict[str, int] = {component: 0 for component in components}
    for dependents in adjacency.values():
        for dependent in dependents:
            indegree[dependent] += 1

    ready = [component for component in components if indegree[component] == 0]
    heapq.heapify(ready)
    order: list[str] = []
    while ready:
        component = heapq.heappop(ready)
        order.extend(sorted(components[component]))
        for dependent in sorted(adjacency.get(component, ())):
            indegree[dependent] -= 1
            if indegree[dependent] == 0:
                heapq.heappush(ready, dependent)

    return {"order": order, "cycle_groups": cycle_groups}


# Heuristic factory / dependency-wiring function names. ``create_*`` builds an
# app/server object; the rest configure or register wiring at import or setup
# time. Matching is best-effort (names only), tagged as such by the caller.
_FACTORY_PREFIXES: tuple[str, ...] = ("create_",)
_WIRING_NAMES: frozenset[str] = frozenset({"configure", "setup", "wire"})
_WIRING_PREFIXES: tuple[str, ...] = ("register_", "configure_", "setup_", "wire_")


def _factory_kind(name: str) -> str:
    """Classify a function name as a ``"factory"``, ``"wiring"`` helper, or ``""``."""
    if name.startswith(_FACTORY_PREFIXES):
        return "factory"
    if name in _WIRING_NAMES or name.startswith(_WIRING_PREFIXES):
        return "wiring"
    return ""


def detect_side_effects(inventory: dict) -> dict:
    """List import-time side effects and factory/wiring functions per module.

    Reads the deep extractor's ``module_calls`` (DL-301) to report each module's
    top-level side effects, and flags top-level functions whose names match the
    app-factory / dependency-wiring heuristics (``create_app``, ``configure``,
    ``setup``, ``wire``, ``register_*``, …). Returns ``{"side_effects":
    [{file, calls}], "factories": [{file, symbol, kind}], "best_effort": True}``,
    both lists deterministically ordered. The detection is name-based and
    therefore advisory, hence ``best_effort``. A module with no module-level
    calls contributes no side-effect entry; absence of optional fields never
    raises.
    """
    side_effects: list[dict] = []
    factories: list[dict] = []
    for filepath in sorted(inventory):
        data = inventory[filepath]
        if not isinstance(data, dict):
            continue
        calls = data.get("module_calls") or []
        if calls:
            side_effects.append({"file": filepath, "calls": calls})
        for fn in data.get("functions", []):
            kind = _factory_kind(fn.get("name", ""))
            if kind:
                factories.append({"file": filepath, "symbol": fn["name"], "kind": kind})

    factories.sort(key=lambda f: (f["file"], f["symbol"]))
    return {"side_effects": side_effects, "factories": factories, "best_effort": True}


# ══ External dependency reconciliation (Epic 2.2) ═════════════════════════
#
# Each language pairs a *manifest parser* (declared dependencies) with an
# *import classifier* (import string → external package name, or ``None`` to
# exclude an internal/relative/stdlib import) behind the shared dispatcher
# below. A parsed manifest is carried as a :class:`_Manifest`; the classifier
# receives it so language-specific exclusions (Go's own-module prefix, the
# Python alias override) stay accurate, and degrades when it is absent.


@dataclass(frozen=True)
class _Manifest:
    """A language's declared dependencies, parsed from its manifest.

    ``required`` are runtime dependencies; ``optional`` are extras/dev/build
    dependencies (never counted "unused"). The remaining fields are
    language-specific context for classification and default to inert values:
    ``own_module``/``internal_modules`` exclude Go intra-module imports, and
    ``aliases`` is the Python import→distribution map already merged with the
    ``[tool.llm-wiki] dependency-aliases`` override.
    """

    required: frozenset[str]
    optional: frozenset[str]
    own_module: str = ""
    internal_modules: frozenset[str] = frozenset()
    aliases: Optional[dict[str, str]] = None


@dataclass(frozen=True)
class _LanguagePlugin:
    """A manifest parser + import classifier for one language family."""

    key: str  # canonical language label used in the reconciliation output
    languages: tuple[str, ...]  # inventory ``language`` values this handles
    parse: Callable[[Path], "Optional[_Manifest]"]
    classify: Callable[[str, str, "Optional[_Manifest]"], "Optional[str]"]


# ── Python (DL-201) ───────────────────────────────────────────────────


# Import top-level name → distribution name where they differ. Keys are the
# (case-sensitive) import names; values are normalized to PEP 503 form on use.
_PYTHON_ALIASES: dict[str, str] = {
    "yaml": "pyyaml",
    "PIL": "pillow",
    "cv2": "opencv-python",
    "bs4": "beautifulsoup4",
    "sklearn": "scikit-learn",
    "dateutil": "python-dateutil",
    "dotenv": "python-dotenv",
    "OpenSSL": "pyopenssl",
    "Crypto": "pycryptodome",
    "git": "gitpython",
    "jose": "python-jose",
    "jwt": "pyjwt",
    "serial": "pyserial",
    "usb": "pyusb",
    "attr": "attrs",
    "MySQLdb": "mysqlclient",
    "psycopg2": "psycopg2-binary",
    "win32com": "pywin32",
}

# Bundled fallback for ``sys.stdlib_module_names`` (added in 3.10). Top-level
# standard-library module names for Python 3.9; used only on 3.9 so a stdlib
# import is never misreported as an undeclared external dependency.
_PYTHON_STDLIB_FALLBACK: frozenset[str] = frozenset(
    {
        "__future__",
        "_thread",
        "abc",
        "aifc",
        "argparse",
        "array",
        "ast",
        "asynchat",
        "asyncio",
        "asyncore",
        "atexit",
        "audioop",
        "base64",
        "bdb",
        "binascii",
        "bisect",
        "builtins",
        "bz2",
        "cProfile",
        "calendar",
        "cgi",
        "cgitb",
        "chunk",
        "cmath",
        "cmd",
        "code",
        "codecs",
        "codeop",
        "collections",
        "colorsys",
        "compileall",
        "concurrent",
        "configparser",
        "contextlib",
        "contextvars",
        "copy",
        "copyreg",
        "crypt",
        "csv",
        "ctypes",
        "curses",
        "dataclasses",
        "datetime",
        "dbm",
        "decimal",
        "difflib",
        "dis",
        "distutils",
        "doctest",
        "email",
        "encodings",
        "ensurepip",
        "enum",
        "errno",
        "faulthandler",
        "fcntl",
        "filecmp",
        "fileinput",
        "fnmatch",
        "fractions",
        "ftplib",
        "functools",
        "gc",
        "genericpath",
        "getopt",
        "getpass",
        "gettext",
        "glob",
        "graphlib",
        "grp",
        "gzip",
        "hashlib",
        "heapq",
        "hmac",
        "html",
        "http",
        "idlelib",
        "imaplib",
        "imghdr",
        "imp",
        "importlib",
        "inspect",
        "io",
        "ipaddress",
        "itertools",
        "json",
        "keyword",
        "lib2to3",
        "linecache",
        "locale",
        "logging",
        "lzma",
        "mailbox",
        "mailcap",
        "marshal",
        "math",
        "mimetypes",
        "mmap",
        "modulefinder",
        "msilib",
        "msvcrt",
        "multiprocessing",
        "netrc",
        "nis",
        "nntplib",
        "nt",
        "ntpath",
        "nturl2path",
        "numbers",
        "opcode",
        "operator",
        "optparse",
        "os",
        "ossaudiodev",
        "pathlib",
        "pdb",
        "pickle",
        "pickletools",
        "pipes",
        "pkgutil",
        "platform",
        "plistlib",
        "poplib",
        "posix",
        "posixpath",
        "pprint",
        "profile",
        "pstats",
        "pty",
        "pwd",
        "py_compile",
        "pyclbr",
        "pydoc",
        "pyexpat",
        "queue",
        "quopri",
        "random",
        "re",
        "readline",
        "reprlib",
        "resource",
        "rlcompleter",
        "runpy",
        "sched",
        "secrets",
        "select",
        "selectors",
        "shelve",
        "shlex",
        "shutil",
        "signal",
        "site",
        "smtpd",
        "smtplib",
        "sndhdr",
        "socket",
        "socketserver",
        "spwd",
        "sqlite3",
        "ssl",
        "stat",
        "statistics",
        "string",
        "stringprep",
        "struct",
        "subprocess",
        "sunau",
        "symtable",
        "sys",
        "sysconfig",
        "syslog",
        "tabnanny",
        "tarfile",
        "telnetlib",
        "tempfile",
        "termios",
        "test",
        "textwrap",
        "threading",
        "time",
        "timeit",
        "tkinter",
        "token",
        "tokenize",
        "trace",
        "traceback",
        "tracemalloc",
        "tty",
        "turtle",
        "turtledemo",
        "types",
        "typing",
        "unicodedata",
        "unittest",
        "urllib",
        "uu",
        "uuid",
        "venv",
        "warnings",
        "wave",
        "weakref",
        "webbrowser",
        "winreg",
        "winsound",
        "wsgiref",
        "xdrlib",
        "xml",
        "xmlrpc",
        "zipapp",
        "zipfile",
        "zipimport",
        "zlib",
        "zoneinfo",
    }
)


def _python_stdlib() -> frozenset[str]:
    names = getattr(sys, "stdlib_module_names", None)
    return frozenset(names) if names else _PYTHON_STDLIB_FALLBACK


def _normalize_python(name: str) -> str:
    """PEP 503 normalization: lowercase, runs of ``-``/``_``/``.`` → ``-``."""
    return re.sub(r"[-_.]+", "-", name.strip().lower()).strip("-")


def _pep508_name(spec: str) -> str:
    """Distribution name from a PEP 508 requirement (drops version/markers/extras)."""
    head = spec.split(";", 1)[0].strip()
    match = re.match(r"[A-Za-z0-9][A-Za-z0-9._-]*", head)
    return match.group(0) if match else ""


def _parse_python_manifest(project_root: Path) -> Optional[_Manifest]:
    data = _load_toml(project_root / "pyproject.toml")
    if data is None:
        return None
    project = data.get("project", {})
    project = project if isinstance(project, dict) else {}

    required = {
        n
        for dep in project.get("dependencies", []) or []
        if isinstance(dep, str) and (n := _normalize_python(_pep508_name(dep)))
    }
    optional: set[str] = set()
    extras = project.get("optional-dependencies", {})
    if isinstance(extras, dict):
        for group in extras.values():
            optional |= {
                n
                for dep in group or []
                if isinstance(dep, str) and (n := _normalize_python(_pep508_name(dep)))
            }

    aliases = dict(_PYTHON_ALIASES)
    tool = data.get("tool", {})
    override = (
        tool.get("llm-wiki", {}).get("dependency-aliases", {})
        if isinstance(tool, dict)
        else {}
    )
    if isinstance(override, dict):
        aliases.update({str(k): str(v) for k, v in override.items()})

    return _Manifest(frozenset(required), frozenset(optional), aliases=aliases)


def _classify_python(
    module: str, name: str, manifest: Optional[_Manifest]
) -> Optional[str]:
    module = module or ""
    if not module or module.startswith("."):
        return None  # relative / unresolved-relative import
    top = module.split(".", 1)[0]
    if not top or top in _python_stdlib():
        return None
    aliases = (
        manifest.aliases
        if manifest and manifest.aliases is not None
        else _PYTHON_ALIASES
    )
    return _normalize_python(aliases.get(top, top))


# ── TypeScript / JavaScript (DL-202) ──────────────────────────────────


_NODE_BUILTINS: frozenset[str] = frozenset(
    {
        "assert",
        "async_hooks",
        "buffer",
        "child_process",
        "cluster",
        "console",
        "constants",
        "crypto",
        "dgram",
        "diagnostics_channel",
        "dns",
        "domain",
        "events",
        "fs",
        "http",
        "http2",
        "https",
        "inspector",
        "module",
        "net",
        "os",
        "path",
        "perf_hooks",
        "process",
        "punycode",
        "querystring",
        "readline",
        "repl",
        "stream",
        "string_decoder",
        "sys",
        "timers",
        "tls",
        "trace_events",
        "tty",
        "url",
        "util",
        "v8",
        "vm",
        "wasi",
        "worker_threads",
        "zlib",
    }
)


def _parse_ts_manifest(project_root: Path) -> Optional[_Manifest]:
    path = project_root / "package.json"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, ValueError):
        return None
    if not isinstance(data, dict):
        return None

    def _keys(section: str) -> set[str]:
        block = data.get(section, {})
        return {k.lower() for k in block} if isinstance(block, dict) else set()

    required = _keys("dependencies") | _keys("peerDependencies")
    optional = _keys("devDependencies") | _keys("optionalDependencies")
    return _Manifest(frozenset(required), frozenset(optional))


def _classify_ts(
    module: str, name: str, manifest: Optional[_Manifest]
) -> Optional[str]:
    spec = (module or "").strip()
    if not spec or spec.startswith((".", "/")):
        return None  # relative
    if spec.startswith("node:"):
        return None  # explicit Node builtin
    if spec.startswith("@"):
        parts = spec.split("/")
        pkg = "/".join(parts[:2]) if len(parts) >= 2 else spec
    else:
        pkg = spec.split("/", 1)[0]
    if pkg in _NODE_BUILTINS:
        return None
    return pkg.lower()


# ── Go (DL-203) ───────────────────────────────────────────────────────


def _parse_go_manifest(project_root: Path) -> Optional[_Manifest]:
    try:
        text = (project_root / "go.mod").read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None

    own_module = ""
    required: set[str] = set()
    replaced_to_local: set[str] = set()
    in_require_block = False

    for raw in text.splitlines():
        line = raw.split("//", 1)[0].strip()
        if not line:
            continue
        if in_require_block:
            if line.startswith(")"):
                in_require_block = False
            elif path := _go_require_path(line):
                required.add(path)
            continue
        if line.startswith("module "):
            own_module = line.split(None, 1)[1].strip()
        elif line.startswith("replace"):
            old, target = _parse_go_replace(line)
            if old and _is_local_path(target):
                replaced_to_local.add(old)
        elif line.startswith("require"):
            rest = line[len("require") :].strip()
            if rest.startswith("("):
                in_require_block = True
            elif path := _go_require_path(rest):
                required.add(path)

    internal = replaced_to_local & required
    required -= internal
    return _Manifest(
        frozenset(required),
        frozenset(),
        own_module=own_module,
        internal_modules=frozenset(internal),
    )


def _go_require_path(line: str) -> str:
    """First whitespace-delimited token of a ``require`` line: the module path."""
    tokens = line.split()
    return tokens[0] if tokens else ""


def _parse_go_replace(line: str) -> tuple[str, str]:
    body = line[len("replace") :].strip().lstrip("(").strip()
    if "=>" not in body:
        return "", ""
    left, _, right = body.partition("=>")
    return left.split()[0] if left.split() else "", right.strip().split()[
        0
    ] if right.strip().split() else ""


def _is_local_path(target: str) -> bool:
    return target.startswith((".", "/")) or "." not in target.split("/", 1)[0]


def _go_default_module(path: str) -> str:
    """Heuristic module key when no ``go.mod`` is available: ``host/org/repo``."""
    segments = path.split("/")
    return "/".join(segments[:3]) if len(segments) >= 3 else path


def _classify_go(
    module: str, name: str, manifest: Optional[_Manifest]
) -> Optional[str]:
    path = (module or "").strip().strip('"')
    if not path:
        return None
    if "." not in path.split("/", 1)[0]:
        return None  # stdlib (e.g. ``fmt``, ``net/http``)
    if manifest is not None:
        if manifest.own_module and _path_under(path, manifest.own_module):
            return None  # intra-module import
        if any(_path_under(path, m) for m in manifest.internal_modules):
            return None  # replaced to a local path
        best = ""
        for dep in manifest.required:
            if _path_under(path, dep) and len(dep) > len(best):
                best = dep
        if best:
            return best
    return _go_default_module(path)


def _path_under(path: str, prefix: str) -> bool:
    return bool(prefix) and (path == prefix or path.startswith(prefix + "/"))


# ── Rust (DL-204) ─────────────────────────────────────────────────────


_RUST_INTERNAL_ROOTS: frozenset[str] = frozenset(
    {"crate", "self", "super", "std", "core", "alloc"}
)


def _normalize_rust(name: str) -> str:
    """Rust crate names are interchangeable across ``-``/``_``; canonicalize."""
    return name.strip().lower().replace("-", "_")


def _parse_rust_manifest(project_root: Path) -> Optional[_Manifest]:
    data = _load_toml(project_root / "Cargo.toml")
    if data is None:
        return None

    def _keys(section: str) -> set[str]:
        block = data.get(section, {})
        # The dependency-table *key* is the name used in ``use`` (``package =``
        # only renames the published crate), so reconcile against the key.
        return {_normalize_rust(k) for k in block} if isinstance(block, dict) else set()

    required = _keys("dependencies")
    optional = _keys("dev-dependencies") | _keys("build-dependencies")
    return _Manifest(frozenset(required), frozenset(optional))


def _classify_rust(
    module: str, name: str, manifest: Optional[_Manifest]
) -> Optional[str]:
    path = (module or "").strip()
    if not path:
        return None
    crate = path.split("::", 1)[0]
    if not crate or crate in _RUST_INTERNAL_ROOTS:
        return None
    return _normalize_rust(crate)


# ── Shared TOML loader ────────────────────────────────────────────────


def _load_toml(path: Path) -> Optional[dict]:
    """Parse a TOML file; ``None`` when missing, unreadable, or unparseable."""
    if tomllib is None:  # pragma: no cover - tomli always present as a dependency
        return None
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None
    try:
        data = tomllib.loads(text)
    except Exception:
        return None
    return data if isinstance(data, dict) else None


# ── Dispatcher + reconciliation (DL-201, DL-205) ──────────────────────


_PLUGINS: tuple[_LanguagePlugin, ...] = (
    _LanguagePlugin("python", ("python",), _parse_python_manifest, _classify_python),
    _LanguagePlugin(
        "typescript", ("typescript", "javascript"), _parse_ts_manifest, _classify_ts
    ),
    _LanguagePlugin("go", ("go",), _parse_go_manifest, _classify_go),
    _LanguagePlugin("rust", ("rust",), _parse_rust_manifest, _classify_rust),
)

_PLUGIN_BY_LANGUAGE: dict[str, _LanguagePlugin] = {
    lang: plugin for plugin in _PLUGINS for lang in plugin.languages
}


def parse_declared_dependencies(project_root: str = ".") -> dict:
    """Parse every available manifest under *project_root*.

    Returns ``{language: {"required": [...], "optional": [...]}}`` for each
    language whose manifest exists and parses; languages with no manifest are
    omitted. ``required`` is runtime dependencies, ``optional`` is extras/dev/
    build dependencies (never flagged "unused"). Both lists are sorted and
    normalized to their language's canonical form; a missing or malformed
    manifest is skipped rather than raised.
    """
    return {
        key: {
            "required": sorted(manifest.required),
            "optional": sorted(manifest.optional),
        }
        for key, manifest in _parse_manifests(Path(project_root)).items()
    }


def _parse_manifests(project_root: Path) -> dict[str, _Manifest]:
    manifests: dict[str, _Manifest] = {}
    for plugin in _PLUGINS:
        manifest = plugin.parse(project_root)
        if manifest is not None:
            manifests[plugin.key] = manifest
    return manifests


def classify_imports(
    inventory: dict,
    *,
    graph: Optional[dict] = None,
    manifests: Optional[dict[str, _Manifest]] = None,
) -> dict:
    """Group each file's external imports by language and package.

    Routes the graph's ``unresolved`` imports (those that resolve to no internal
    file — DL-101) through their file's per-language classifier, dropping
    relative, stdlib/builtin, and intra-module imports. Returns
    ``{language: {package: [importing_files]}}`` with every collection sorted.

    *graph* and *manifests* are accepted so a caller that already computed them
    (e.g. :func:`reconcile_dependencies`) avoids redundant work; both default to
    being derived on demand (manifests stay empty here — Go classification then
    degrades to a ``host/org/repo`` heuristic).
    """
    if graph is None:
        graph = build_dependency_graph(inventory)
    manifests = manifests or {}

    grouped: defaultdict[str, defaultdict[str, set[str]]] = defaultdict(
        lambda: defaultdict(set)
    )
    for item in graph.get("unresolved", []):
        data = inventory.get(item["file"])
        language = data.get("language") if isinstance(data, dict) else None
        plugin = _PLUGIN_BY_LANGUAGE.get(language)
        if plugin is None:
            continue
        package = plugin.classify(
            item["module"], item["name"], manifests.get(plugin.key)
        )
        if package:
            grouped[plugin.key][package].add(item["file"])

    return {
        language: {pkg: sorted(files) for pkg, files in sorted(packages.items())}
        for language, packages in sorted(grouped.items())
    }


def reconcile_dependencies(
    inventory: dict,
    project_root: str = ".",
    *,
    graph: Optional[dict] = None,
) -> dict:
    """Reconcile used external imports against declared dependencies per language.

    For every language with either imports or a manifest, computes
    ``undeclared = used − (required ∪ optional)`` and ``unused = required −
    used`` (extras/dev/build dependencies are never "unused"). Returns
    ``{"languages": {language: {"used", "required", "optional", "undeclared",
    "unused"}}, "summary": {...}}``; ``used`` maps each package to its importing
    files. Tolerant of a missing manifest (all used → undeclared) or missing
    imports (all required → unused); never raises.
    """
    if graph is None:
        graph = build_dependency_graph(inventory)
    manifests = _parse_manifests(Path(project_root))
    used = classify_imports(inventory, graph=graph, manifests=manifests)

    languages: dict[str, dict] = {}
    for key in sorted(set(used) | set(manifests)):
        used_packages = used.get(key, {})
        used_names = set(used_packages)
        manifest = manifests.get(key)
        required = manifest.required if manifest else frozenset()
        optional = manifest.optional if manifest else frozenset()
        languages[key] = {
            "used": used_packages,
            "required": sorted(required),
            "optional": sorted(optional),
            "undeclared": sorted(used_names - required - optional),
            "unused": sorted(required - used_names),
        }

    summary = {
        "languages": sorted(languages),
        "external_count": sum(len(lang["used"]) for lang in languages.values()),
        "undeclared_count": sum(len(lang["undeclared"]) for lang in languages.values()),
        "unused_count": sum(len(lang["unused"]) for lang in languages.values()),
    }
    return {"languages": languages, "summary": summary}


# ══ Aggregation + scale guard (Epic 2.4) ══════════════════════════════════


def analyze_dependencies(inventory: dict, project_root: str = ".") -> dict:
    """Run the full dependency analysis once, sharing the internal graph.

    Builds the internal module-dependency graph a single time and threads it
    through cycle detection, fan-in/fan-out metrics, topological load order, and
    external reconciliation, then pairs it with module-level side effects. The
    page generators, ``sync`` regeneration, and the ``extract`` block all consume
    this one bundle so the graph is never rebuilt per consumer. Returns
    ``{"graph", "cycles", "metrics", "load_order", "side_effects",
    "reconciliation"}``; deterministic and never raises on slim inventories.
    """
    graph = build_dependency_graph(inventory)
    return {
        "graph": graph,
        "cycles": detect_cycles(graph),
        "metrics": dependency_metrics(graph),
        "load_order": topological_order(graph),
        "side_effects": detect_side_effects(inventory),
        "reconciliation": reconcile_dependencies(inventory, project_root, graph=graph),
    }


def top_level_package(filepath: str) -> str:
    """Return the top-level package of *filepath* (its first path component).

    A file at the project root (no directory) is its own package, keyed by stem,
    so the collapsed graph never invents an empty bucket.
    """
    path = Path(filepath)
    parts = path.parts
    return parts[0] if len(parts) > 1 else path.stem


def package_dependency_graph(graph: dict) -> dict:
    """Collapse a module graph to a top-level-package graph.

    Every module node maps to its :func:`top_level_package`; intra-package edges
    are dropped and parallel inter-package edges de-duplicated, bounding the
    diagram for large repositories (DL-404). Returns the same
    ``{"nodes", "edges"}`` shape as :func:`build_dependency_graph` (minus
    ``unresolved``), stably sorted.
    """
    nodes = {top_level_package(node) for node in graph.get("nodes", [])}
    edges: set[tuple[str, str]] = set()
    for source, target in graph.get("edges", []):
        src, dst = top_level_package(source), top_level_package(target)
        nodes.add(src)
        nodes.add(dst)
        if src != dst:
            edges.add((src, dst))
    return {"nodes": sorted(nodes), "edges": sorted(edges)}
