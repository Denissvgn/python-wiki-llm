"""Portable publication policies reject ambiguous destinations and unsafe inputs."""

from copy import deepcopy
import json
from pathlib import Path

import pytest

from llm_wiki_cli.services.publication_config import (
    PUBLICATION_CONFIG_PATH,
    PUBLICATION_CONFIG_SCHEMA_VERSION,
    PublicationConfigError,
    load_publication_config,
    publication_path,
    read_publication_json,
    validate_publication_config,
)


def policy():
    return {
        "schema_version": PUBLICATION_CONFIG_SCHEMA_VERSION,
        "architecture": {"baseline": "existing-wiki", "root": "docs/llm_wiki"},
        "target": {"kind": "github-wiki", "repository": "self"},
        "enforcement": "advisory",
        "publish": False,
        "topics": [
            {
                "id": "command-reference",
                "owner": "maintainers",
                "wiki_page": "Command-Reference.md",
                "edit_at": "wiki",
                "depends_on": [
                    {"architecture_page": "modules/cli.md"},
                    {"source_file": "pyproject.toml"},
                ],
            }
        ],
    }


def write_policy(root: Path, payload=None):
    path = root / PUBLICATION_CONFIG_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(policy() if payload is None else payload), encoding="utf-8"
    )
    return path


def make_symlink(path: Path, target: Path, *, directory: bool = False):
    try:
        path.symlink_to(target, target_is_directory=directory)
    except (OSError, NotImplementedError):
        pytest.skip("symlinks are unavailable")


def test_load_is_explicit_portable_and_detached_from_cwd_and_input(
    tmp_path, monkeypatch
):
    consumer = tmp_path / "consumer"
    consumer.mkdir()
    write_policy(consumer)
    monkeypatch.chdir(tmp_path)
    normalized = load_publication_config(consumer)
    assert normalized["source_policy"] == "default-branch"
    assert normalized["exclusions"] == []
    assert normalized["topics"][0]["depends_on"][0]["facets"] == ["whole"]
    payload = policy()
    result = validate_publication_config(payload, consumer_root=consumer)
    result["topics"][0]["depends_on"][0]["facets"].append("semantic")
    assert "facets" not in payload["topics"][0]["depends_on"][0]
    assert not (tmp_path / PUBLICATION_CONFIG_PATH).exists()


def test_repository_topics_sections_exclusions_and_required_enforcement(tmp_path):
    payload = policy()
    payload.update(
        source_policy="release",
        enforcement="required",
        exclusions=[{"pattern": "entities/*.md", "reason": "Internal declarations"}],
    )
    payload["architecture"]["baseline"] = "bootstrap-source"
    payload["target"]["repository"] = "Example-org/user-docs"
    topic = payload["topics"][0]
    topic.update(
        edit_at="repository", source_document="docs/commands.md", anchor="sync"
    )
    topic["depends_on"][0].update(
        section="llm-wiki://modules/cli#section/Description~1",
        facets=["structural", "semantic"],
    )
    result = validate_publication_config(payload, consumer_root=tmp_path)
    assert result["target"]["repository"] == "Example-org/user-docs"
    assert result["topics"][0]["depends_on"][0]["facets"] == ["semantic", "structural"]
    assert result["publish"] is False
    assert result["exclusions"] == payload["exclusions"]


@pytest.mark.parametrize("value", [True, 0, None, "false", []])
def test_policy_never_grants_publication_authority(tmp_path, value):
    payload = policy()
    payload["publish"] = value
    with pytest.raises(PublicationConfigError) as error:
        validate_publication_config(payload, consumer_root=tmp_path)
    assert error.value.field == "publish"


@pytest.mark.parametrize(
    "path,value",
    [
        ((), {"unknown": True}),
        (("architecture",), {"unknown": True}),
        (("target",), {"unknown": True}),
        (("topics", 0), {"unknown": True}),
        (("topics", 0, "depends_on", 0), {"unknown": True}),
    ],
)
def test_unknown_fields_fail_at_every_object_boundary(tmp_path, path, value):
    payload = policy()
    selected = payload
    for key in path:
        selected = selected[key]
    selected.update(value)
    with pytest.raises(PublicationConfigError, match="unknown"):
        validate_publication_config(payload, consumer_root=tmp_path)


@pytest.mark.parametrize(
    "key,value",
    [
        ("schema_version", "llm-wiki-publication/v2"),
        ("source_policy", "HEAD"),
        ("enforcement", "optional"),
        ("exclusions", [{"pattern": "**/*.md", "reason": ""}]),
    ],
)
def test_versions_and_policy_enums_are_explicit(tmp_path, key, value):
    payload = policy()
    payload[key] = value
    with pytest.raises(PublicationConfigError):
        validate_publication_config(payload, consumer_root=tmp_path)


@pytest.mark.parametrize(
    "repository",
    [
        "https://github.com/o/r",
        "o/r/wiki",
        "../repo",
        "owner/..",
        "owner/",
        "_owner/repo",
        "owner/repo?token=secret",
    ],
)
def test_repository_is_an_identifier_not_a_transport_url(tmp_path, repository):
    payload = policy()
    payload["target"]["repository"] = repository
    with pytest.raises(PublicationConfigError) as error:
        validate_publication_config(payload, consumer_root=tmp_path)
    assert error.value.field == "target.repository"


@pytest.mark.parametrize(
    "path",
    [
        "../secret",
        "/absolute",
        "C:/secret",
        "docs\\secret",
        "docs/./secret",
        "docs//secret",
        "docs/../secret",
        "docs/CON.md",
        "docs/trailing. ",
        "docs/control\x7f.md",
    ],
)
@pytest.mark.parametrize(
    "field", ["root", "source_document", "source_file", "architecture_page"]
)
def test_policy_paths_are_canonical_and_portable(tmp_path, field, path):
    payload = policy()
    if field == "root":
        payload["architecture"]["root"] = path
    elif field == "source_document":
        payload["topics"][0]["source_document"] = path
    else:
        payload["topics"][0]["depends_on"] = [{field: path}]
    with pytest.raises(PublicationConfigError):
        validate_publication_config(payload, consumer_root=tmp_path)


@pytest.mark.parametrize(
    "page", ["guide", "nested/Guide.md", "../Guide.md", "Guide.MD", ".md"]
)
def test_wiki_destination_is_a_flat_markdown_filename(tmp_path, page):
    payload = policy()
    payload["topics"][0]["wiki_page"] = page
    with pytest.raises(PublicationConfigError):
        validate_publication_config(payload, consumer_root=tmp_path)


def test_distinct_anchors_can_share_a_page_but_cannot_overlap_whole_page(tmp_path):
    payload = policy()
    first = payload["topics"][0]
    first["anchor"] = "sync"
    second = deepcopy(first)
    second.update(id="bootstrap", anchor="bootstrap")
    payload["topics"].append(second)
    assert (
        len(validate_publication_config(payload, consumer_root=tmp_path)["topics"]) == 2
    )
    del second["anchor"]
    with pytest.raises(PublicationConfigError, match="overlaps"):
        validate_publication_config(payload, consumer_root=tmp_path)


@pytest.mark.parametrize(
    "change", ["id-case", "page-case", "page-space", "anchor-case"]
)
def test_case_and_wiki_slug_collisions_are_rejected(tmp_path, change):
    payload = policy()
    first = payload["topics"][0]
    second = deepcopy(first)
    second["id"] = "other"
    if change == "id-case":
        second.update(id=first["id"].upper(), wiki_page="Other.md")
    elif change == "page-case":
        second["wiki_page"] = "command-reference.md"
    elif change == "page-space":
        second["wiki_page"] = "Command Reference.md"
    else:
        first["anchor"] = "Sync"
        second["anchor"] = "sync"
    payload["topics"].append(second)
    with pytest.raises(PublicationConfigError):
        validate_publication_config(payload, consumer_root=tmp_path)


def test_repository_authorship_requires_its_source_document(tmp_path):
    payload = policy()
    payload["topics"][0]["edit_at"] = "repository"
    with pytest.raises(PublicationConfigError) as error:
        validate_publication_config(payload, consumer_root=tmp_path)
    assert error.value.field == "topics[0].source_document"


def test_empty_topics_support_retirement_and_explicit_exclusion_only_adoption(tmp_path):
    payload = policy()
    payload["topics"] = []
    payload["exclusions"] = [
        {"pattern": "**/*.md", "reason": "No public projection is maintained"}
    ]
    result = validate_publication_config(payload, consumer_root=tmp_path)
    assert result["topics"] == []
    assert result["exclusions"] == payload["exclusions"]


@pytest.mark.parametrize("baseline", ["existing-wiki", "bootstrap-source"])
def test_architecture_may_use_consumer_root_without_relaxing_dependency_paths(
    tmp_path, baseline
):
    payload = policy()
    payload["architecture"] = {"baseline": baseline, "root": "."}
    assert (
        validate_publication_config(payload, consumer_root=tmp_path)["architecture"][
            "root"
        ]
        == "."
    )
    assert publication_path(tmp_path, ".") == tmp_path
    payload["topics"][0]["depends_on"] = [{"source_file": "."}]
    with pytest.raises(PublicationConfigError):
        validate_publication_config(payload, consumer_root=tmp_path)


@pytest.mark.parametrize(
    "dependency",
    [
        {},
        {"architecture_page": "modules/cli.md", "source_file": "cli.py"},
        {"source_file": "cli.py", "section": "arbitrary"},
        {"source_file": "cli.py", "facets": ["whole"]},
        {"architecture_page": "modules/cli.md", "facets": []},
        {"architecture_page": "modules/cli.md", "facets": ["semantic", "semantic"]},
        {"architecture_page": "modules/cli.md", "facets": ["whole", "structural"]},
        {"architecture_page": "modules/cli.md", "facets": ["unknown"]},
        {"architecture_page": "modules/cli.md", "facets": ["semantic"]},
        {"architecture_page": "modules/cli.md", "facets": ["structural"]},
        {
            "architecture_page": "modules/cli.md",
            "section": "llm-wiki://modules/cli#description",
        },
        {
            "architecture_page": "modules/cli.md",
            "section": "llm-wiki://modules/cli#section/Description~0",
        },
        {
            "architecture_page": "modules/cli.md",
            "section": "llm-wiki://modules/cli#section/Description~01",
        },
        {
            "architecture_page": "modules/cli.md",
            "section": "llm-wiki://modules/cli#section/%44escription~1",
        },
    ],
)
def test_dependency_discriminators_facets_and_native_sections_are_strict(
    tmp_path, dependency
):
    payload = policy()
    payload["topics"][0]["depends_on"] = [dependency]
    with pytest.raises(PublicationConfigError):
        validate_publication_config(payload, consumer_root=tmp_path)


def test_duplicate_dependencies_and_inconsistent_path_spelling_fail(tmp_path):
    payload = policy()
    topic = payload["topics"][0]
    topic["depends_on"].append(
        {"architecture_page": "modules/cli.md", "facets": ["whole"]}
    )
    with pytest.raises(PublicationConfigError, match="duplicates"):
        validate_publication_config(payload, consumer_root=tmp_path)
    topic["depends_on"] = [
        {"source_file": "src/cli.py"},
        {"source_file": "Src/model.py"},
    ]
    with pytest.raises(PublicationConfigError, match="collides"):
        validate_publication_config(payload, consumer_root=tmp_path)


@pytest.mark.parametrize(
    "location", ["architecture", "dependency", "source-document", "exclusion"]
)
def test_config_references_cannot_traverse_symlinks(tmp_path, location):
    outside = tmp_path / "outside"
    outside.mkdir()
    consumer = tmp_path / "consumer"
    consumer.mkdir()
    payload = policy()
    if location == "architecture":
        make_symlink(consumer / "docs", outside, directory=True)
    elif location == "dependency":
        make_symlink(consumer / "src", outside, directory=True)
        payload["topics"][0]["depends_on"] = [{"source_file": "src/secret.py"}]
    elif location == "source-document":
        make_symlink(consumer / "authored", outside, directory=True)
        payload["topics"][0]["source_document"] = "authored/commands.md"
    else:
        (consumer / "docs/llm_wiki").mkdir(parents=True)
        make_symlink(consumer / "docs/llm_wiki/linked", outside, directory=True)
        payload["exclusions"] = [{"pattern": "linked/*.md", "reason": "Not owned"}]
    with pytest.raises(PublicationConfigError, match="symlink"):
        validate_publication_config(payload, consumer_root=consumer)


def test_publication_path_allows_absent_paths_without_following_existing_links(
    tmp_path,
):
    assert publication_path(tmp_path, "absent/file.md") == tmp_path / "absent/file.md"
    make_symlink(tmp_path / "linked", tmp_path, directory=True)
    with pytest.raises(PublicationConfigError, match="symlink"):
        publication_path(tmp_path, "linked/file.md")
    with pytest.raises(PublicationConfigError):
        publication_path(tmp_path, "../outside")


def test_imported_policy_validation_is_pure_and_retains_lexical_guards(
    tmp_path, monkeypatch
):
    make_symlink(tmp_path / "docs", tmp_path, directory=True)
    monkeypatch.chdir(tmp_path)
    payload = policy()
    assert (
        validate_publication_config(payload, consumer_root=None)["architecture"]
        == payload["architecture"]
    )
    with pytest.raises(PublicationConfigError, match="symlink"):
        validate_publication_config(payload, consumer_root=tmp_path)
    payload["architecture"]["root"] = "../outside"
    with pytest.raises(PublicationConfigError):
        validate_publication_config(payload, consumer_root=None)


@pytest.mark.parametrize(
    "raw",
    [
        b'{"a":1,"a":2}',
        b'{"a":{"b":1,"b":2}}',
        b'{"a":NaN}',
        b'{"a":Infinity}',
        b"[]",
        b"\xff",
        b"{",
    ],
)
def test_json_reader_rejects_noncanonical_or_unbounded_inputs(tmp_path, raw):
    path = tmp_path / "config.json"
    path.write_bytes(raw)
    with pytest.raises(PublicationConfigError):
        read_publication_json(path)
    path.write_bytes(b'{"x":"large"}')
    with pytest.raises(PublicationConfigError, match="at most 5"):
        read_publication_json(path, max_bytes=5)


def test_loader_rejects_config_symlinks_wrong_case_and_missing_file(tmp_path):
    with pytest.raises(PublicationConfigError):
        load_publication_config(tmp_path)
    actual = write_policy(tmp_path)
    make_symlink(tmp_path / "linked.json", actual)
    with pytest.raises(PublicationConfigError, match="symlink"):
        load_publication_config(tmp_path, config_path="linked.json")
    with pytest.raises(PublicationConfigError, match="case"):
        load_publication_config(tmp_path, config_path=".llm-wiki/Publication.json")
    with pytest.raises(PublicationConfigError):
        load_publication_config(tmp_path, config_path=actual)
