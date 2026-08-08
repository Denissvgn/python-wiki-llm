"""Tests for the Haskell helper executable contract."""

from __future__ import annotations

import ast
import inspect
import json
import shutil
import subprocess
import textwrap
from pathlib import Path

import pytest

from llm_wiki_cli.commands import extract_cmd
from llm_wiki_cli.extractors import common as extractor_common
from llm_wiki_cli.extractors.haskell_extractor import (
    HaskellExtractionRequest,
    HaskellExtractor,
)
from llm_wiki_cli.services.extractor_helpers import (
    SUPPORTED_GHC_MAJOR,
    SUPPORTED_GHC_MINOR,
    _ghc_support_error,
    _ghc_version,
    _parse_ghc_version,
)
from llm_wiki_cli.services.inventory_cache import InventoryCacheOptions


PROJECT_ROOT = Path(__file__).parents[1]
HASKELL_SCRIPTS_DIR = (
    PROJECT_ROOT / "src" / "llm_wiki_cli" / "extractors" / "haskell_scripts"
)


@pytest.fixture(scope="session")
def haskell_helper(tmp_path_factory: pytest.TempPathFactory) -> Path:
    ghc = shutil.which("ghc")
    if ghc is None:
        pytest.skip("GHC is not available")

    toolchain, version_error = _ghc_version(ghc)
    if toolchain is None:
        pytest.skip(f"GHC is not usable: {version_error}")
    support_error = _ghc_support_error(toolchain)
    if support_error is not None:
        pytest.skip(support_error)
    ghc_version = _parse_ghc_version(toolchain)
    assert ghc_version is not None

    build_root = tmp_path_factory.mktemp("haskell-helper")
    binary = build_root / "llm-wiki-haskell-extractor"
    output_dir = build_root / "build"
    try:
        subprocess.run(
            [
                ghc,
                "-Wall",
                "-Werror",
                "-package",
                "ghc",
                "-outputdir",
                str(output_dir),
                f"-i{HASKELL_SCRIPTS_DIR}",
                "-o",
                str(binary),
                str(HASKELL_SCRIPTS_DIR / "Main.hs"),
            ],
            capture_output=True,
            text=True,
            check=True,
            timeout=180,
            cwd=str(HASKELL_SCRIPTS_DIR),
        )
    except subprocess.CalledProcessError as exc:
        stderr = exc.stderr.strip() or exc.stdout.strip() or str(exc)
        major, minor, _patch = ghc_version
        if major == SUPPORTED_GHC_MAJOR and minor == SUPPORTED_GHC_MINOR:
            raise AssertionError(
                f"Supported {toolchain} failed to build Haskell helper:\n{stderr}"
            ) from exc
        pytest.skip(
            f"Haskell helper build failed with best-effort {toolchain}: {stderr}"
        )
    except subprocess.TimeoutExpired as exc:
        major, minor, _patch = ghc_version
        if major == SUPPORTED_GHC_MAJOR and minor == SUPPORTED_GHC_MINOR:
            raise AssertionError(
                f"Supported {toolchain} timed out building Haskell helper"
            ) from exc
        pytest.skip(f"Haskell helper build timed out with best-effort {toolchain}")
    return binary


def _write_haskell(root: Path, rel_path: str, content: str) -> Path:
    path = root / rel_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(content), encoding="utf-8")
    return path


def _write_owned_package_sentinels(root: Path) -> None:
    for rel_path in (
        "src/llm_wiki_cli/__init__.py",
        "src/llm_wiki_cli/cli.py",
        "src/llm_wiki_cli/extractors/__init__.py",
        "src/llm_wiki_cli/extractors/common.py",
    ):
        _write_haskell(root, rel_path, "# package source\n")


def _body_line_count(function) -> int:
    source = textwrap.dedent(inspect.getsource(function))
    function_node = ast.parse(source).body[0]
    assert isinstance(function_node, ast.FunctionDef)
    body = function_node.body
    if (
        body
        and isinstance(body[0], ast.Expr)
        and isinstance(body[0].value, ast.Constant)
        and isinstance(body[0].value.value, str)
    ):
        body = body[1:]

    first_body_line = min(stmt.lineno for stmt in body)
    last_body_line = max(stmt.end_lineno or stmt.lineno for stmt in body)
    return last_body_line - first_body_line + 1


def _run_helper(
    helper: Path,
    src_dir: Path,
    *,
    only_files: list[str] | None = None,
    deep: bool = False,
) -> subprocess.CompletedProcess[str]:
    cmd = [str(helper), "--src-dir", str(src_dir)]
    if only_files is not None:
        cmd.extend(["--only-files", ",".join(only_files)])
    if deep:
        cmd.append("--deep")
    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )


class TestHaskellExtractorWrapper:
    def test_missing_helper_returns_empty_and_reports_prepare_command(
        self, tmp_path, monkeypatch, capsys
    ):
        _write_haskell(tmp_path, "Main.hs", "module Main where\n")

        monkeypatch.setattr(
            "llm_wiki_cli.extractors.haskell_extractor.get_prepared_binary",
            lambda *args, **kwargs: None,
        )

        extractor = HaskellExtractor()
        inventory = extractor.extract(str(tmp_path))

        assert inventory == {}
        assert extractor.last_error is not None
        assert "prepare-extractors --language haskell" in extractor.last_error
        assert "prepare-extractors --language haskell" in capsys.readouterr().err

    def test_no_haskell_files_skips_helper_probe(self, tmp_path, monkeypatch):
        helper_calls = []

        monkeypatch.setattr(
            "llm_wiki_cli.extractors.haskell_extractor.get_prepared_binary",
            lambda *args, **kwargs: helper_calls.append(args),
        )

        inventory = HaskellExtractor().extract(str(tmp_path))

        assert inventory == {}
        assert helper_calls == []

    def test_normalization_filters_checkout_helper_but_not_unrelated_suffix(
        self, tmp_path
    ):
        _write_owned_package_sentinels(tmp_path)
        bundled = "src/llm_wiki_cli/extractors/haskell_scripts/Main.hs"
        unrelated = "vendor/llm_wiki_cli/extractors/haskell_scripts/Main.hs"
        _write_haskell(tmp_path, bundled, "module Main where\n")
        _write_haskell(tmp_path, unrelated, "module Consumer where\n")
        inventory = {
            bundled: {"classes": [], "functions": []},
            unrelated: {"classes": [], "functions": []},
        }

        normalized = HaskellExtractor()._normalize_inventory(
            str(tmp_path), inventory
        )

        assert list(normalized) == [unrelated]

    def test_relative_external_helper_suffix_fails_open_across_both_filter_stages(
        self, tmp_path, monkeypatch
    ):
        external_root = tmp_path / "external-consumer"
        relative_path = "src/llm_wiki_cli/extractors/haskell_scripts/Main.hs"
        _write_haskell(external_root, relative_path, "module Consumer where\n")
        monkeypatch.chdir(Path(__file__).parents[1])
        result = subprocess.CompletedProcess(
            args=["haskell-helper"],
            returncode=0,
            stdout=json.dumps(
                {relative_path: {"classes": [], "functions": []}}
            ),
            stderr="",
        )
        extractor = HaskellExtractor()

        loaded = extractor._load_inventory(result)
        normalized = extractor._normalize_inventory(str(external_root), loaded)

        assert list(loaded) == [relative_path]
        assert list(normalized) == [relative_path]

    def test_request_object_passes_source_files_cache_dir_and_deep_to_helper(
        self, tmp_path, monkeypatch
    ):
        _write_haskell(tmp_path, "src/App.hs", "module App where\n")
        monkeypatch.setenv("LLM_WIKI_EXTRACTOR_TIMEOUT", "40")
        helper_calls = []
        commands = []

        def fake_get_prepared_binary(language, src_dir, helper_cache_dir):
            helper_calls.append((language, src_dir, helper_cache_dir))
            return Path("/tmp/haskell-helper")

        def fake_run(cmd, *args, **kwargs):
            commands.append((cmd, kwargs))
            return subprocess.CompletedProcess(
                cmd,
                0,
                stdout='{"src/App.hs":{"classes":[],"functions":[]}}',
                stderr="",
            )

        monkeypatch.setattr(
            "llm_wiki_cli.extractors.haskell_extractor.get_prepared_binary",
            fake_get_prepared_binary,
        )
        monkeypatch.setattr(
            "llm_wiki_cli.extractors.haskell_extractor.subprocess.run", fake_run
        )

        inventory = HaskellExtractor().extract(
            HaskellExtractionRequest(
                src_dir=str(tmp_path),
                deep=True,
                source_files=["src/App.hs"],
                helper_cache_dir="cache-dir",
            )
        )

        assert list(inventory) == ["src/App.hs"]
        assert helper_calls == [("haskell", str(tmp_path), "cache-dir")]
        command, kwargs = commands[0]
        assert command[command.index("--only-files") + 1] == "src/App.hs"
        assert "--deep" in command
        assert kwargs["timeout"] == 40
        assert kwargs["cwd"] == str(Path("/tmp/haskell-helper").parent)

    def test_full_scan_passes_gitignore_filtered_files_to_subprocess(
        self, tmp_path, monkeypatch
    ):
        _write_haskell(tmp_path, "real.hs", "module Real where\n")
        _write_haskell(tmp_path, "ignored.hs", "module Ignored where\n")
        (tmp_path / ".gitignore").write_text("ignored.hs\n", encoding="utf-8")
        commands = []

        def fake_run(cmd, *args, **kwargs):
            commands.append(cmd)
            return subprocess.CompletedProcess(
                cmd,
                0,
                stdout='{"real.hs":{"classes":[],"functions":[]}}',
                stderr="",
            )

        monkeypatch.setattr(
            "llm_wiki_cli.extractors.haskell_extractor.get_prepared_binary",
            lambda *args, **kwargs: Path("/tmp/haskell-helper"),
        )
        monkeypatch.setattr(
            "llm_wiki_cli.extractors.haskell_extractor.subprocess.run", fake_run
        )

        HaskellExtractor().extract(str(tmp_path))

        assert commands[0][commands[0].index("--only-files") + 1] == "real.hs"

    def test_only_files_respects_excluded_dirs(self, tmp_path, monkeypatch):
        _write_haskell(tmp_path, "dist/Generated.hs", "module Generated where\n")

        monkeypatch.setattr(
            "llm_wiki_cli.extractors.haskell_extractor.get_prepared_binary",
            lambda *args, **kwargs: pytest.fail("helper should not be probed"),
        )

        inventory = HaskellExtractor().extract(
            str(tmp_path), only_files=["dist/Generated.hs"]
        )

        assert inventory == {}

    def test_large_file_selection_is_split_across_subprocess_calls(
        self, tmp_path, monkeypatch
    ):
        paths = ["src/A.hs", "src/B.hs", "src/C.hs"]
        for rel_path in paths:
            _write_haskell(tmp_path, rel_path, "module Fixture where\n")
        commands = []

        def fake_run(cmd, *args, **kwargs):
            commands.append(cmd)
            only_files = cmd[cmd.index("--only-files") + 1].split(",")
            payload = {
                rel_path: {"classes": [], "functions": []} for rel_path in only_files
            }
            return subprocess.CompletedProcess(
                cmd,
                0,
                stdout=json.dumps(payload),
                stderr="",
            )

        monkeypatch.setattr(extractor_common, "MAX_ONLY_FILES_ARG_CHARS", 10)
        monkeypatch.setattr(
            "llm_wiki_cli.extractors.haskell_extractor.get_prepared_binary",
            lambda *args, **kwargs: Path("/tmp/haskell-helper"),
        )
        monkeypatch.setattr(
            "llm_wiki_cli.extractors.haskell_extractor.subprocess.run", fake_run
        )

        inventory = HaskellExtractor().extract(str(tmp_path))

        assert set(inventory) == set(paths)
        assert len(commands) > 1
        for command in commands:
            only_arg = command[command.index("--only-files") + 1]
            assert len(only_arg) <= extractor_common.MAX_ONLY_FILES_ARG_CHARS

    def test_successful_output_is_normalized_stamped_filtered_and_forwards_stderr(
        self, tmp_path, monkeypatch, capsys
    ):
        source = _write_haskell(tmp_path, "pkg/Client.hs", "module Client where\n")
        bundled = HASKELL_SCRIPTS_DIR / "Main.hs"
        output = {
            source.as_posix(): {"classes": [], "functions": []},
            "pkg\\Windows.hs": {"classes": [], "functions": []},
            bundled.as_posix(): {"classes": [], "functions": []},
        }

        monkeypatch.setattr(
            "llm_wiki_cli.extractors.haskell_extractor.get_prepared_binary",
            lambda *args, **kwargs: Path("/tmp/haskell-helper"),
        )
        monkeypatch.setattr(
            "llm_wiki_cli.extractors.haskell_extractor.subprocess.run",
            lambda cmd, *args, **kwargs: subprocess.CompletedProcess(
                cmd,
                0,
                stdout=json.dumps(output),
                stderr="Warning: skipped Bad.hs\n",
            ),
        )

        inventory = HaskellExtractor().extract(
            HaskellExtractionRequest(
                src_dir=str(tmp_path),
                source_files=["pkg/Client.hs", "pkg/Windows.hs"],
            )
        )

        assert sorted(inventory) == ["pkg/Client.hs", "pkg/Windows.hs"]
        assert inventory["pkg/Client.hs"]["language"] == "haskell"
        assert inventory["pkg/Windows.hs"]["language"] == "haskell"
        assert "Main.hs" not in inventory
        assert "Warning: skipped Bad.hs" in capsys.readouterr().err

    def test_source_and_helper_cache_roots_with_spaces_are_passed_as_single_args(
        self, tmp_path, monkeypatch
    ):
        source_root = tmp_path / "source root"
        helper_cache = tmp_path / "helper cache"
        _write_haskell(source_root, "pkg/App.hs", "module App where\n")
        commands = []

        def fake_run(cmd, *args, **kwargs):
            commands.append((cmd, kwargs))
            return subprocess.CompletedProcess(
                cmd,
                0,
                stdout=json.dumps({"pkg/App.hs": {"classes": [], "functions": []}}),
                stderr="",
            )

        helper_calls = []
        monkeypatch.setattr(
            "llm_wiki_cli.extractors.haskell_extractor.get_prepared_binary",
            lambda language, src_dir, cache_dir: (
                helper_calls.append((language, src_dir, cache_dir))
                or Path("/tmp/helper cache/haskell-helper")
            ),
        )
        monkeypatch.setattr(
            "llm_wiki_cli.extractors.haskell_extractor.subprocess.run", fake_run
        )

        inventory = HaskellExtractor().extract(
            HaskellExtractionRequest(
                src_dir=str(source_root),
                source_files=["pkg/App.hs"],
                helper_cache_dir=str(helper_cache),
            )
        )

        assert sorted(inventory) == ["pkg/App.hs"]
        assert helper_calls == [("haskell", str(source_root), str(helper_cache))]
        command, kwargs = commands[0]
        assert command[command.index("--src-dir") + 1] == str(source_root.resolve())
        assert command[command.index("--only-files") + 1] == "pkg/App.hs"
        assert Path(kwargs["cwd"]) == Path("/tmp/helper cache")

    def test_windows_absolute_helper_paths_normalize_under_source_root(
        self, tmp_path, monkeypatch
    ):
        source_root = tmp_path / "source root"
        source = _write_haskell(source_root, "pkg/Windows.hs", "module Windows where\n")
        windows_absolute = str(source.resolve()).replace("/", "\\")

        monkeypatch.setattr(
            "llm_wiki_cli.extractors.haskell_extractor.get_prepared_binary",
            lambda *args, **kwargs: Path("/tmp/haskell-helper"),
        )
        monkeypatch.setattr(
            "llm_wiki_cli.extractors.haskell_extractor.subprocess.run",
            lambda cmd, *args, **kwargs: subprocess.CompletedProcess(
                cmd,
                0,
                stdout=json.dumps({windows_absolute: {"classes": [], "functions": []}}),
                stderr="",
            ),
        )

        inventory = HaskellExtractor().extract(
            HaskellExtractionRequest(
                src_dir=str(source_root),
                source_files=["pkg/Windows.hs"],
            )
        )

        assert sorted(inventory) == ["pkg/Windows.hs"]

    def test_malformed_json_returns_empty_and_sets_last_error(
        self, tmp_path, monkeypatch, capsys
    ):
        _write_haskell(tmp_path, "Main.hs", "module Main where\n")

        monkeypatch.setattr(
            "llm_wiki_cli.extractors.haskell_extractor.get_prepared_binary",
            lambda *args, **kwargs: Path("/tmp/haskell-helper"),
        )
        monkeypatch.setattr(
            "llm_wiki_cli.extractors.haskell_extractor.subprocess.run",
            lambda cmd, *args, **kwargs: subprocess.CompletedProcess(
                cmd, 0, stdout="{not-json", stderr=""
            ),
        )

        extractor = HaskellExtractor()
        inventory = extractor.extract(str(tmp_path))

        assert inventory == {}
        assert extractor.last_error == "malformed JSON output"
        assert "malformed JSON" in capsys.readouterr().err

    def test_helper_failure_timeout_and_missing_executable_set_last_error(
        self, tmp_path, monkeypatch, capsys
    ):
        _write_haskell(tmp_path, "Main.hs", "module Main where\n")
        monkeypatch.setenv("LLM_WIKI_EXTRACTOR_TIMEOUT", "41")

        monkeypatch.setattr(
            "llm_wiki_cli.extractors.haskell_extractor.get_prepared_binary",
            lambda *args, **kwargs: Path("/tmp/haskell-helper"),
        )

        cases = [
            (
                subprocess.CalledProcessError(2, ["haskell"], stderr="parse failed"),
                "extraction failed",
            ),
            (subprocess.TimeoutExpired(["haskell"], 41), "timed out"),
            (FileNotFoundError(), "prepared Haskell helper executable not found"),
        ]
        for error, expected in cases:
            monkeypatch.setattr(
                "llm_wiki_cli.extractors.haskell_extractor.subprocess.run",
                lambda *args, _error=error, **kwargs: (_ for _ in ()).throw(_error),
            )

            extractor = HaskellExtractor()
            inventory = extractor.extract(str(tmp_path))

            assert inventory == {}
            assert extractor.last_error is not None
            assert expected in extractor.last_error
            if isinstance(error, subprocess.TimeoutExpired):
                assert "LLM_WIKI_EXTRACTOR_TIMEOUT" in extractor.last_error
                assert "LLM_WIKI_EXTRACTOR_TIMEOUT" in capsys.readouterr().err

    def test_extract_remains_short_orchestrator(self):
        source = textwrap.dedent(inspect.getsource(HaskellExtractor.extract))

        assert len(source.splitlines()) <= 30
        assert _body_line_count(HaskellExtractor.extract) <= 25

    def test_extract_signature_stays_protocol_sized(self):
        signature = inspect.signature(HaskellExtractor.extract)
        public_parameters = [
            param.name
            for param in signature.parameters.values()
            if param.name != "self"
        ]

        assert public_parameters == ["src_dir", "only_files", "deep"]


class TestHaskellExtractorInventoryPipeline:
    def test_warm_inventory_cache_skips_haskell_helper(self, tmp_path, monkeypatch):
        _write_haskell(tmp_path, "App.hs", "module App where\n")
        calls = []

        class FakeHaskellExtractor:
            last_error = None

            def extract(self, src_dir, only_files=None, deep=False):
                calls.append(list(src_dir.source_files))
                return {
                    "App.hs": {
                        "language": "haskell",
                        "classes": [{"name": "App", "kind": "data"}],
                        "functions": [],
                    }
                }

        monkeypatch.setattr(
            extract_cmd,
            "get_extractor_registry",
            lambda: {"haskell": extract_cmd.EXTRACTOR_REGISTRY["haskell"]},
        )
        monkeypatch.setattr(
            extract_cmd, "_load_extractor", lambda _entry: FakeHaskellExtractor()
        )
        options = InventoryCacheOptions(
            enabled=True,
            cache_dir=str(tmp_path / "inventory-cache"),
        )

        first = extract_cmd.get_inventory_result(
            str(tmp_path), deep=True, cache_options=options
        )
        second = extract_cmd.get_inventory_result(
            str(tmp_path), deep=True, cache_options=options
        )

        assert calls == [["App.hs"]]
        assert first.inventory["App.hs"]["language"] == "haskell"
        assert second.inventory["App.hs"]["classes"][0]["name"] == "App"
        assert second.cache_stats is not None
        assert second.cache_stats.hits == 1
        assert second.cache_stats.fresh_extracted == 0

    def test_helper_cache_dir_is_independent_from_inventory_cache(
        self, tmp_path, monkeypatch
    ):
        _write_haskell(tmp_path, "App.hs", "module App where\n")
        requests = []

        class FakeHaskellExtractor:
            last_error = None

            def extract(self, src_dir, only_files=None, deep=False):
                requests.append(src_dir)
                return {
                    "App.hs": {
                        "language": "haskell",
                        "classes": [],
                        "functions": [],
                    }
                }

        monkeypatch.setattr(
            extract_cmd,
            "get_extractor_registry",
            lambda: {"haskell": extract_cmd.EXTRACTOR_REGISTRY["haskell"]},
        )
        monkeypatch.setattr(
            extract_cmd, "_load_extractor", lambda _entry: FakeHaskellExtractor()
        )

        result = extract_cmd.get_inventory_result(
            str(tmp_path),
            deep=True,
            cache_options=InventoryCacheOptions(
                enabled=True,
                cache_dir=str(tmp_path / "inventory-cache"),
            ),
            helper_cache_dir=str(tmp_path / "helper-cache"),
        )

        assert result.inventory["App.hs"]["language"] == "haskell"
        assert requests[0].helper_cache_dir == str(tmp_path / "helper-cache")

    def test_paths_and_changed_restrict_haskell_source_files(
        self, tmp_path, monkeypatch
    ):
        _write_haskell(tmp_path, "A.hs", "module A where\n")
        _write_haskell(tmp_path, "B.hs", "module B where\n")
        requests = []

        class FakeHaskellExtractor:
            last_error = None

            def extract(self, src_dir, only_files=None, deep=False):
                requests.append(list(src_dir.source_files))
                return {
                    rel_path: {
                        "language": "haskell",
                        "classes": [],
                        "functions": [],
                    }
                    for rel_path in src_dir.source_files
                }

        monkeypatch.chdir(tmp_path)
        monkeypatch.setattr(
            extract_cmd,
            "get_extractor_registry",
            lambda: {"haskell": extract_cmd.EXTRACTOR_REGISTRY["haskell"]},
        )
        monkeypatch.setattr(
            extract_cmd, "_load_extractor", lambda _entry: FakeHaskellExtractor()
        )
        monkeypatch.setattr(extract_cmd, "_git_changed_files", lambda _src: ["B.hs"])

        paths_result = extract_cmd.build_extract_payload(
            ".", paths=["A.hs"], summary=True
        )
        changed_result = extract_cmd.build_extract_payload(
            ".", changed=True, summary=True
        )

        assert requests == [["A.hs"], ["B.hs"]]
        assert sorted(paths_result.payload["inventory"]) == ["A.hs"]
        assert sorted(changed_result.payload["inventory"]) == ["B.hs"]

    def test_parallel_jobs_schedule_haskell_with_fresh_builtin_instances(
        self, tmp_path, monkeypatch
    ):
        _write_haskell(tmp_path, "App.hs", "module App where\n")
        (tmp_path / "app.py").write_text("class App: pass\n", encoding="utf-8")
        registry = {
            "python": extract_cmd.EXTRACTOR_REGISTRY["python"],
            "haskell": extract_cmd.EXTRACTOR_REGISTRY["haskell"],
        }
        created = []

        class FakeExtractor:
            def __init__(self, language):
                self.language = language
                self.last_error = None

            def extract(self, src_dir, only_files=None, deep=False, **kwargs):
                created.append(self.language)
                source_files = (
                    src_dir.source_files
                    if isinstance(src_dir, HaskellExtractionRequest)
                    else kwargs["source_files"]
                )
                assert source_files is not None
                return {
                    source_files[0]: {
                        "language": self.language,
                        "classes": [],
                        "functions": [],
                    }
                }

        def fake_instantiate(entry_point):
            language = "haskell" if "haskell_extractor" in entry_point else "python"
            return FakeExtractor(language)

        monkeypatch.setattr(extract_cmd, "get_extractor_registry", lambda: registry)
        monkeypatch.setattr(extract_cmd, "_instantiate_extractor", fake_instantiate)
        monkeypatch.setattr(
            extract_cmd,
            "_load_extractor",
            lambda _entry: pytest.fail("parallel built-ins should use fresh instances"),
        )

        result = extract_cmd.get_inventory_result(str(tmp_path), parallel_jobs=2)

        assert sorted(created) == ["haskell", "python"]
        assert sorted(result.inventory) == ["App.hs", "app.py"]


def test_haskell_helper_extracts_syntax_inventory(haskell_helper: Path, tmp_path):
    _write_haskell(
        tmp_path,
        "hls-analysis/src/HLSAnalysis/API.hs",
        """\
        {-# LANGUAGE FlexibleInstances #-}
        module HLSAnalysis.API where

        import Data.Text (Text)
        import qualified Data.Map as Map

        type UserId = Int

        data User = User { userName :: Text }

        newtype Token = Token Text

        class Renderable a where
          render :: a -> Text

        instance Renderable User where
          render _ = "user"

        apiName :: Text
        apiName = "api"

        loadUser :: UserId -> Maybe User
        loadUser userId = Nothing
        """,
    )

    result = _run_helper(
        haskell_helper,
        tmp_path,
        only_files=["hls-analysis/src/HLSAnalysis/API.hs"],
        deep=True,
    )

    assert result.returncode == 0, result.stderr
    assert result.stderr == ""
    inventory = json.loads(result.stdout)
    assert sorted(inventory) == ["hls-analysis/src/HLSAnalysis/API.hs"]

    entry = inventory["hls-analysis/src/HLSAnalysis/API.hs"]
    assert entry["language"] == "haskell"
    assert entry["module"] == "HLSAnalysis.API"
    assert entry["language_pragmas"] == ["FlexibleInstances"]
    assert {
        "module": "Data.Map",
        "qualified": True,
        "alias": "Map",
        "line": 5,
    } in entry["imports"]
    assert {
        "module": "Data.Text",
        "qualified": False,
        "alias": None,
        "line": 4,
    } in entry["imports"]

    classes_by_name = {item["name"]: item for item in entry["classes"]}
    assert classes_by_name["User"]["kind"] == "data"
    assert classes_by_name["Token"]["kind"] == "newtype"
    assert classes_by_name["UserId"]["kind"] == "type"
    assert classes_by_name["Renderable"]["kind"] == "class"
    assert classes_by_name["instance Renderable User"]["kind"] == "instance"

    functions_by_name = {
        (item["name"], item["kind"]): item for item in entry["functions"]
    }
    assert functions_by_name[("apiName", "signature")]["signature"] == "Text"
    assert functions_by_name[("apiName", "value")]["line"] == 20
    assert (
        functions_by_name[("loadUser", "signature")]["signature"]
        == "UserId -> Maybe User"
    )
    assert functions_by_name[("loadUser", "function")]["line"] == 23


def test_literate_haskell_helper_preserves_inventory_shape(
    haskell_helper: Path, tmp_path
):
    _write_haskell(
        tmp_path,
        "docs/Literate.lhs",
        """\
        This prose should be ignored.

        > module Docs.Literate where
        > import qualified Data.Text as Text
        >
        > data Page = Page
        >
        > title :: Text.Text
        > title = Text.pack "hello"

        More prose should also be ignored.
        """,
    )

    result = _run_helper(
        haskell_helper,
        tmp_path,
        only_files=["docs/Literate.lhs"],
    )

    assert result.returncode == 0, result.stderr
    entry = json.loads(result.stdout)["docs/Literate.lhs"]
    assert entry["language"] == "haskell"
    assert entry["module"] == "Docs.Literate"
    assert entry["imports"] == [
        {"module": "Data.Text", "qualified": True, "alias": "Text", "line": 4}
    ]
    assert entry["classes"] == [{"name": "Page", "kind": "data", "line": 6}]
    assert {
        "name": "title",
        "kind": "signature",
        "signature": "Text.Text",
        "line": 8,
    } in entry["functions"]
    assert {"name": "title", "kind": "value", "line": 9} in entry["functions"]


def test_literate_haskell_code_blocks_are_extracted(haskell_helper: Path, tmp_path):
    _write_haskell(
        tmp_path,
        "docs/Block.lhs",
        """\
        Narrative.

        \\begin{code}
        module Docs.Block where

        blockValue :: Int
        blockValue = 1
        \\end{code}
        """,
    )

    result = _run_helper(
        haskell_helper,
        tmp_path,
        only_files=["docs/Block.lhs"],
    )

    assert result.returncode == 0, result.stderr
    entry = json.loads(result.stdout)["docs/Block.lhs"]
    assert entry["module"] == "Docs.Block"
    assert {
        "name": "blockValue",
        "kind": "signature",
        "signature": "Int",
        "line": 6,
    } in entry["functions"]
    assert {"name": "blockValue", "kind": "value", "line": 7} in entry["functions"]


def test_haskell_helper_rejects_outside_root_only_files(haskell_helper: Path, tmp_path):
    project = tmp_path / "project"
    project.mkdir()
    _write_haskell(tmp_path, "outside.hs", "module Outside where\n")

    result = _run_helper(haskell_helper, project, only_files=["../outside.hs"])

    assert result.returncode != 0
    assert result.stdout == ""
    assert "outside --src-dir" in result.stderr


def test_haskell_helper_reports_parse_errors_without_stdout(
    haskell_helper: Path, tmp_path
):
    _write_haskell(tmp_path, "Bad.hs", "module Bad where\n\nbad =\n")

    result = _run_helper(haskell_helper, tmp_path, only_files=["Bad.hs"])

    assert result.returncode != 0
    assert result.stdout == ""
    assert "Bad.hs" in result.stderr
    assert "parse" in result.stderr.lower()


def test_haskell_helper_requires_src_dir_argument(haskell_helper: Path):
    result = subprocess.run(
        [str(haskell_helper), "--only-files", "Main.hs"],
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )

    assert result.returncode != 0
    assert result.stdout == ""
    assert "--src-dir" in result.stderr
