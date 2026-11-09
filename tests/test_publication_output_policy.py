"""Publication outputs cannot become the next source-bootstrap input."""

import json

import pytest

from llm_wiki_cli.services.publication_snapshot import assert_bootstrap_output_excluded
from llm_wiki_cli.services.source_selection import SOURCE_SELECTION_SCHEMA_VERSION


@pytest.fixture
def source(tmp_path):
    project = tmp_path / "project"
    project.mkdir()
    (project / "app.py").write_text("class Application:\n    pass\n", encoding="utf-8")
    return tmp_path


def test_root_bootstrap_blocks_selected_code_attachments_before_writing(source):
    destination = source / "reports/candidate"
    with pytest.raises(ValueError, match="excluded output location"):
        assert_bootstrap_output_excluded(
            source, destination, {"example.py": b"value = 1\n"}
        )
    assert not destination.exists()


@pytest.mark.parametrize(
    "path",
    [
        "example.py",
        "example.ts",
        "example.js",
        "example.go",
        "example_test.go",
        "example.rs",
        "example.hs",
        "example.sh",
        "example.java",
        "example.cpp",
        "config.yml",
        "config.yaml",
        "Dockerfile",
        "Dockerfile.public",
        "app.dockerfile",
        "compose.yaml",
        "Kustomization",
        "package.json",
        "go.mod",
        "requirements.txt",
        "pyproject.toml",
        "Cargo.lock",
        ".gitignore",
    ],
)
def test_future_producer_families_require_explicit_exclusion(source, path):
    with pytest.raises(ValueError, match="bootstrap source input"):
        assert_bootstrap_output_excluded(
            source, source / "reports/candidate", {path: b"public attachment"}
        )


def test_builtin_derived_directory_excludes_code_without_policy_mutation(source):
    assert_bootstrap_output_excluded(
        source, source / "out/candidate", {"example.py": b"value = 1\n"}
    )
    assert not (source / "out").exists()
    assert not (source / ".gitignore").exists()


def test_consumer_gitignore_can_exclude_the_future_output(source):
    ignore = source / ".gitignore"
    ignore.write_text("reports/\n", encoding="utf-8")
    before = ignore.read_bytes()
    assert_bootstrap_output_excluded(
        source, source / "reports/candidate", {"example.py": b"value = 1\n"}
    )
    assert ignore.read_bytes() == before
    assert not (source / "reports").exists()


def test_explicit_project_only_selection_excludes_other_future_paths(source):
    controls = source / ".llm-wiki"
    controls.mkdir()
    profile = controls / "source-selection.json"
    profile.write_text(
        json.dumps(
            {
                "schema_version": SOURCE_SELECTION_SCHEMA_VERSION,
                "include": ["project"],
                "exclude": [],
            }
        ),
        encoding="utf-8",
    )
    before = profile.read_bytes()
    assert_bootstrap_output_excluded(
        source, source / "reports/candidate", {"example.py": b"value = 1\n"}
    )
    assert profile.read_bytes() == before
    assert not (source / "reports").exists()


@pytest.mark.parametrize("destination", ["reports/candidate", "public-candidate", "."])
def test_normal_markdown_and_media_do_not_need_source_exclusions(source, destination):
    assert_bootstrap_output_excluded(
        source,
        source / destination,
        {
            "Home.md": b"# Public home\n",
            "assets/logo.png": b"public image",
            "limits.txt": b"10\n",
        },
    )


def test_output_outside_source_root_cannot_contaminate_it(source):
    assert_bootstrap_output_excluded(
        source / "project", source / "reports/candidate", {"example.py": b"value = 1\n"}
    )


def test_root_lib_ignore_does_not_hide_rescued_typescript_inputs(source):
    (source / ".gitignore").write_text("lib/\n", encoding="utf-8")
    with pytest.raises(ValueError, match="bootstrap source input"):
        assert_bootstrap_output_excluded(
            source,
            source / "src/lib/candidate",
            {"example.ts": b"export const value = 1;\n"},
        )


def test_anchored_lib_ignore_is_an_actual_exclusion(source):
    (source / ".gitignore").write_text("/src/lib/\n", encoding="utf-8")
    assert_bootstrap_output_excluded(
        source,
        source / "src/lib/candidate",
        {"example.ts": b"export const value = 1;\n"},
    )


def test_existing_source_root_case_alias_does_not_bypass_the_guard(source):
    actual = source / "project"
    alias = source / "PROJECT"
    if alias.exists():
        with pytest.raises(ValueError, match="bootstrap source input"):
            assert_bootstrap_output_excluded(
                actual, alias / "candidate", {"example.py": b"value = 1\n"}
            )
    else:
        assert_bootstrap_output_excluded(
            actual, alias / "candidate", {"example.py": b"value = 1\n"}
        )


@pytest.mark.parametrize("path", ["../outside.py", "/outside.py", "C:/outside.py"])
def test_future_path_validation_remains_confined(source, path):
    with pytest.raises(ValueError):
        assert_bootstrap_output_excluded(
            source, source / "reports/candidate", {path: b"value = 1\n"}
        )
