"""Tests for services/dependencies.py — external reconciliation (Epic 2.2)."""
from __future__ import annotations

from llm_wiki_cli.services.dependencies import (
    classify_imports,
    parse_declared_dependencies,
    reconcile_dependencies,
)


def _imp(module, name=None):
    return {"module": module, "name": name if name is not None else module}


def _file(language, *imports):
    return {"language": language, "imports": list(imports)}


# ── DL-201: classification framework + Python ─────────────────────────


class TestClassifyImportsDispatcher:
    def test_routes_each_file_by_its_language(self):
        inventory = {
            "a.py": _file("python", _imp("requests.adapters", "HTTPAdapter")),
            "b.ts": _file("typescript", _imp("react")),
            "c.rs": _file("rust", _imp("serde::Deserialize", "Deserialize")),
        }
        used = classify_imports(inventory)
        assert used == {
            "python": {"requests": ["a.py"]},
            "rust": {"serde": ["c.rs"]},
            "typescript": {"react": ["b.ts"]},
        }

    def test_internal_resolved_imports_are_not_external(self):
        # ``b`` resolves to b.py (internal) and is excluded; ``click`` is external.
        inventory = {
            "a.py": _file("python", _imp("b"), _imp("click")),
            "b.py": _file("python"),
        }
        assert classify_imports(inventory) == {"python": {"click": ["a.py"]}}

    def test_unknown_language_is_skipped(self):
        inventory = {"Dockerfile": _file("docker", _imp("alpine"))}
        assert classify_imports(inventory) == {}

    def test_importing_files_are_sorted_and_deduplicated(self):
        inventory = {
            "z.py": _file("python", _imp("click")),
            "a.py": _file("python", _imp("click"), _imp("click", "echo")),
        }
        assert classify_imports(inventory) == {"python": {"click": ["a.py", "z.py"]}}


class TestPythonClassification:
    def test_stdlib_and_relative_excluded(self):
        inventory = {
            "a.py": _file("python", _imp("os"), _imp("xml.etree", "ElementTree"), _imp(".sibling", "x")),
        }
        assert classify_imports(inventory) == {}

    def test_submodule_maps_to_top_level_distribution(self):
        inventory = {"a.py": _file("python", _imp("requests.adapters", "HTTPAdapter"))}
        assert classify_imports(inventory) == {"python": {"requests": ["a.py"]}}

    def test_builtin_alias_table(self):
        inventory = {
            "a.py": _file("python", _imp("yaml"), _imp("PIL.Image", "Image"), _imp("cv2")),
        }
        used = classify_imports(inventory)["python"]
        assert set(used) == {"pyyaml", "pillow", "opencv-python"}

    def test_single_and_multiline_dependency_arrays_parse(self, tmp_path):
        (tmp_path / "pyproject.toml").write_text(
            '[project]\n'
            'name = "x"\n'
            'dependencies = ["requests>=2.0"]\n'
            '[project.optional-dependencies]\n'
            'dev = [\n'
            '  "pytest",   # test runner\n'
            '  "PyYAML",\n'
            ']\n',
            encoding="utf-8",
        )
        declared = parse_declared_dependencies(str(tmp_path))
        assert declared["python"]["required"] == ["requests"]
        assert declared["python"]["optional"] == ["pytest", "pyyaml"]

    def test_pep508_specifiers_markers_and_extras_stripped(self, tmp_path):
        (tmp_path / "pyproject.toml").write_text(
            '[project]\n'
            'name = "x"\n'
            'dependencies = [\n'
            '  "requests[security] >= 2.0",\n'
            '  "tomli ; python_version < \'3.11\'",\n'
            '  "Flask_SQLAlchemy",\n'
            ']\n',
            encoding="utf-8",
        )
        declared = parse_declared_dependencies(str(tmp_path))
        assert declared["python"]["required"] == ["flask-sqlalchemy", "requests", "tomli"]

    def test_missing_pyproject_is_omitted_not_raised(self, tmp_path):
        assert parse_declared_dependencies(str(tmp_path)) == {}

    def test_pyproject_without_dependencies_section_is_empty_not_absent(self, tmp_path):
        (tmp_path / "pyproject.toml").write_text('[project]\nname = "x"\n', encoding="utf-8")
        assert parse_declared_dependencies(str(tmp_path))["python"] == {
            "required": [],
            "optional": [],
        }

    def test_tool_override_alias_applies(self, tmp_path):
        (tmp_path / "pyproject.toml").write_text(
            '[project]\n'
            'name = "x"\n'
            'dependencies = ["my-dist"]\n'
            '[tool.llm-wiki.dependency-aliases]\n'
            'weirdimport = "my-dist"\n',
            encoding="utf-8",
        )
        inventory = {"a.py": _file("python", _imp("weirdimport"))}
        report = reconcile_dependencies(inventory, str(tmp_path))["languages"]["python"]
        # The override maps the import onto the declared distribution → not undeclared.
        assert report["undeclared"] == []
        assert report["used"] == {"my-dist": ["a.py"]}


# ── DL-202: TypeScript / JavaScript ───────────────────────────────────


class TestTypeScriptClassification:
    def test_scoped_subpath_and_bare_subpath(self):
        inventory = {
            "a.ts": _file(
                "typescript",
                _imp("@scope/pkg/sub", "Thing"),
                _imp("lodash/fp", "map"),
            ),
        }
        assert classify_imports(inventory) == {
            "typescript": {"@scope/pkg": ["a.ts"], "lodash": ["a.ts"]}
        }

    def test_node_builtins_and_relative_excluded(self):
        inventory = {
            "a.ts": _file(
                "typescript",
                _imp("node:fs", "readFile"),
                _imp("fs", "readFile"),
                _imp("./local", "x"),
                _imp("../up", "y"),
                _imp("/abs", "z"),
            ),
        }
        assert classify_imports(inventory) == {}

    def test_javascript_language_uses_same_classifier(self):
        inventory = {"a.js": _file("javascript", _imp("react"))}
        assert classify_imports(inventory) == {"typescript": {"react": ["a.js"]}}

    def test_dev_dependencies_reported_as_optional(self, tmp_path):
        (tmp_path / "package.json").write_text(
            '{"dependencies": {"react": "^18"},'
            ' "devDependencies": {"jest": "^29"},'
            ' "peerDependencies": {"react-dom": "^18"}}',
            encoding="utf-8",
        )
        declared = parse_declared_dependencies(str(tmp_path))["typescript"]
        assert declared["required"] == ["react", "react-dom"]
        assert declared["optional"] == ["jest"]

    def test_devdependency_use_is_not_undeclared(self, tmp_path):
        (tmp_path / "package.json").write_text(
            '{"dependencies": {"react": "^18"}, "devDependencies": {"jest": "^29"}}',
            encoding="utf-8",
        )
        inventory = {"a.test.ts": _file("typescript", _imp("jest"), _imp("react"))}
        report = reconcile_dependencies(inventory, str(tmp_path))["languages"]["typescript"]
        assert report["undeclared"] == []  # jest is a known devDependency
        assert report["unused"] == []  # react (required) is imported


# ── DL-203: Go ────────────────────────────────────────────────────────


class TestGoClassification:
    def test_stdlib_excluded_by_dotless_first_segment(self):
        inventory = {"a.go": _file("go", _imp("fmt"), _imp("net/http", "http"))}
        assert classify_imports(inventory) == {}

    def test_longest_prefix_match_with_version_suffix(self, tmp_path):
        (tmp_path / "go.mod").write_text(
            "module github.com/me/proj\n\n"
            "require (\n"
            "\tgithub.com/foo/bar/v2 v2.1.0\n"
            "\tgithub.com/baz/qux v1.0.0 // indirect\n"
            ")\n",
            encoding="utf-8",
        )
        inventory = {
            "a.go": _file(
                "go",
                _imp("github.com/foo/bar/v2/sub", "sub"),
                _imp("github.com/me/proj/internal/x", "x"),  # own module → internal
            ),
        }
        report = reconcile_dependencies(inventory, str(tmp_path))["languages"]["go"]
        assert report["used"] == {"github.com/foo/bar/v2": ["a.go"]}
        assert report["undeclared"] == []
        assert report["unused"] == ["github.com/baz/qux"]

    def test_single_line_require_and_replace_to_local(self, tmp_path):
        (tmp_path / "go.mod").write_text(
            "module github.com/me/proj\n"
            "require github.com/foo/bar v1.2.3\n"
            "replace github.com/foo/bar => ../local/bar\n",
            encoding="utf-8",
        )
        declared = parse_declared_dependencies(str(tmp_path))["go"]
        # Replaced to a local path → treated as internal, not a declared require.
        assert declared["required"] == []

    def test_no_manifest_falls_back_to_host_org_repo(self):
        inventory = {"a.go": _file("go", _imp("github.com/foo/bar/baz/qux", "qux"))}
        assert classify_imports(inventory) == {
            "go": {"github.com/foo/bar": ["a.go"]}
        }


# ── DL-204: Rust ──────────────────────────────────────────────────────


class TestRustClassification:
    def test_std_and_crate_roots_excluded(self):
        inventory = {
            "a.rs": _file(
                "rust",
                _imp("std::collections::HashMap", "HashMap"),
                _imp("crate::foo", "foo"),
                _imp("self::bar", "bar"),
                _imp("super::baz", "baz"),
                _imp("core::mem", "mem"),
            ),
        }
        assert classify_imports(inventory) == {}

    def test_use_path_maps_to_crate(self):
        inventory = {"a.rs": _file("rust", _imp("serde::Deserialize", "Deserialize"))}
        assert classify_imports(inventory) == {"rust": {"serde": ["a.rs"]}}

    def test_dash_underscore_normalization_reconciles(self, tmp_path):
        (tmp_path / "Cargo.toml").write_text(
            "[dependencies]\n"
            'proc-macro2 = "1"\n'
            "[dev-dependencies]\n"
            'criterion = "0.5"\n',
            encoding="utf-8",
        )
        inventory = {"a.rs": _file("rust", _imp("proc_macro2::TokenStream", "TokenStream"))}
        report = reconcile_dependencies(inventory, str(tmp_path))["languages"]["rust"]
        assert report["used"] == {"proc_macro2": ["a.rs"]}
        assert report["undeclared"] == []
        assert report["unused"] == []
        assert report["optional"] == ["criterion"]


# ── DL-205: reconcile_dependencies ────────────────────────────────────


class TestReconcileDependencies:
    def test_undeclared_unused_and_extras(self, tmp_path):
        (tmp_path / "pyproject.toml").write_text(
            '[project]\n'
            'name = "x"\n'
            'dependencies = ["requests", "PyYAML"]\n'
            '[project.optional-dependencies]\n'
            'dev = ["pytest"]\n',
            encoding="utf-8",
        )
        inventory = {
            "a.py": _file(
                "python",
                _imp("requests.adapters", "HTTPAdapter"),
                _imp("yaml"),
                _imp("click"),  # undeclared
                _imp("os"),  # stdlib, ignored
            ),
        }
        report = reconcile_dependencies(inventory, str(tmp_path))["languages"]["python"]
        assert report["undeclared"] == ["click"]
        assert report["unused"] == []  # requests + pyyaml both used; pytest is optional
        assert sorted(report["used"]) == ["click", "pyyaml", "requests"]

    def test_imports_but_no_manifest_all_undeclared(self, tmp_path):
        inventory = {"a.py": _file("python", _imp("requests"), _imp("click"))}
        report = reconcile_dependencies(inventory, str(tmp_path))["languages"]["python"]
        assert report["undeclared"] == ["click", "requests"]
        assert report["unused"] == []

    def test_manifest_but_no_imports_all_unused(self, tmp_path):
        (tmp_path / "pyproject.toml").write_text(
            '[project]\nname = "x"\ndependencies = ["requests", "click"]\n',
            encoding="utf-8",
        )
        report = reconcile_dependencies({}, str(tmp_path))["languages"]["python"]
        assert report["undeclared"] == []
        assert report["unused"] == ["click", "requests"]

    def test_extra_dependency_satisfies_import(self, tmp_path):
        (tmp_path / "pyproject.toml").write_text(
            '[project]\n'
            'name = "x"\n'
            'dependencies = []\n'
            '[project.optional-dependencies]\n'
            'extra = ["rich"]\n',
            encoding="utf-8",
        )
        inventory = {"a.py": _file("python", _imp("rich"))}
        report = reconcile_dependencies(inventory, str(tmp_path))["languages"]["python"]
        assert report["undeclared"] == []  # satisfied by an extra

    def test_summary_aggregates_across_languages(self, tmp_path):
        (tmp_path / "pyproject.toml").write_text(
            '[project]\nname = "x"\ndependencies = ["requests"]\n', encoding="utf-8"
        )
        (tmp_path / "package.json").write_text(
            '{"dependencies": {"react": "^18"}}', encoding="utf-8"
        )
        inventory = {
            "a.py": _file("python", _imp("requests"), _imp("click")),
            "b.ts": _file("typescript", _imp("react"), _imp("axios")),
        }
        result = reconcile_dependencies(inventory, str(tmp_path))
        assert result["summary"]["languages"] == ["python", "typescript"]
        assert result["summary"]["undeclared_count"] == 2  # click + axios
        assert result["summary"]["external_count"] == 4

    def test_deterministic_regardless_of_input_order(self, tmp_path):
        (tmp_path / "pyproject.toml").write_text(
            '[project]\nname = "x"\ndependencies = ["requests"]\n', encoding="utf-8"
        )
        forward = {
            "a.py": _file("python", _imp("requests")),
            "b.py": _file("python", _imp("click")),
        }
        reverse = dict(reversed(list(forward.items())))
        assert reconcile_dependencies(forward, str(tmp_path)) == reconcile_dependencies(
            reverse, str(tmp_path)
        )
