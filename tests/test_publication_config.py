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
    publication_input_controls,
    publication_control_overlap,
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


def test_implicit_publication_inputs_are_reserved_even_when_absent(tmp_path):
    value = policy()
    value["architecture"] = {"baseline": "bootstrap-source", "root": "project"}
    controls = publication_input_controls(
        tmp_path, value, ".llm-wiki/custom-publication.json"
    )
    assert controls == {
        tmp_path / ".gitignore",
        tmp_path / ".llm-wiki/source-selection.json",
        tmp_path / "project/.gitignore",
        tmp_path / "project/.llm-wiki/source-selection.json",
        tmp_path / ".llm-wiki/custom-publication.json",
    }
    assert not any(path.exists() for path in controls)


@pytest.mark.parametrize(
    "output",
    [
        "project/.LLM-WIKI/SOURCE-SELECTION.JSON",
        "PROJECT/.gitignore/receipt.json",
        "project/.llm-wiki",
    ],
)
def test_reserved_control_overlap_is_portable_before_creation(tmp_path, output):
    control = tmp_path / "project/.llm-wiki/source-selection.json"
    if "gitignore" in output:
        control = tmp_path / "project/.gitignore"
    assert publication_control_overlap(tmp_path / output, control)
    assert publication_control_overlap(control, tmp_path / output)
    assert not publication_control_overlap(tmp_path / "reports/control.json", control)


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


def test_legacy_normalization_does_not_add_reference_provider_state():
    payload = policy()
    normalized = validate_publication_config(payload, consumer_root=None)
    assert "reference_providers" not in normalized
    assert normalized["topics"][0]["depends_on"] == [
        {"architecture_page": "modules/cli.md", "facets": ["whole"]},
        {"source_file": "pyproject.toml"},
    ]
    assert validate_publication_config(normalized, consumer_root=None) == normalized


def content_policy():
    payload = policy()
    payload["topics"][0].update(
        edit_at="repository", source_document="docs/public/commands.md"
    )
    payload["content"] = {
        "root": "docs/public",
        "assets": [
            {
                "source_document": "docs/public/images/overview.png",
                "wiki_path": "assets/overview.png",
                "owner": "documentation-maintainers",
            }
        ],
        "adoptions": [
            {
                "path": "Command-Reference.md",
                "expected_hash": None,
                "reason": "New owned page",
            }
        ],
        "removals": [
            {
                "path": "Former-Commands.md",
                "expected_hash": "sha256:" + "a" * 64,
                "reason": "Reviewed rename",
            }
        ],
        "repository_url": "https://git.example.test:8443/Example-org/project",
    }
    return payload


def test_content_profile_is_opt_in_detached_and_consumer_relative(tmp_path):
    legacy = validate_publication_config(policy(), consumer_root=None)
    assert "content" not in legacy
    payload = content_policy()
    result = validate_publication_config(payload, consumer_root=tmp_path)
    assert result["content"] == payload["content"]
    result["content"]["assets"][0]["owner"] = "other"
    assert payload["content"]["assets"][0]["owner"] == "documentation-maintainers"
    minimal = content_policy()
    minimal["content"] = {"root": "docs/public"}
    assert validate_publication_config(minimal, consumer_root=None)["content"] == {
        "root": "docs/public"
    }


@pytest.mark.parametrize("root", [".", "docs/public"])
def test_content_root_can_select_the_consumer_or_a_subdirectory(root):
    payload = content_policy()
    payload["content"]["root"] = root
    assert (
        validate_publication_config(payload, consumer_root=None)["content"]["root"]
        == root
    )


@pytest.mark.parametrize(
    "damage",
    [
        "unknown",
        "root-escape",
        "source-outside",
        "source-native",
        "source-not-markdown",
        "asset-outside",
        "asset-code",
        "asset-metadata",
        "asset-output-escape",
        "asset-extension",
        "asset-case",
        "asset-prefix",
        "asset-owner",
        "adoption-extra",
        "adoption-hash",
        "adoption-reason",
        "operation-duplicate",
        "operation-overlap",
        "remove-active",
        "native-control-output",
        "operation-metadata",
    ],
)
def test_content_profile_rejects_unsafe_or_ambiguous_public_inputs(damage):
    payload = content_policy()
    profile = payload["content"]
    asset = profile["assets"][0]
    if damage == "unknown":
        profile["command"] = ["run", "application"]
    elif damage == "root-escape":
        profile["root"] = "../public"
    elif damage == "source-outside":
        payload["topics"][0]["source_document"] = "README.md"
    elif damage == "source-native":
        profile["root"] = "."
        payload["topics"][0]["source_document"] = "docs/llm_wiki/modules/cli.md"
    elif damage == "source-not-markdown":
        payload["topics"][0]["source_document"] = "docs/public/app.py"
    elif damage == "asset-outside":
        asset["source_document"] = "private/overview.png"
    elif damage == "asset-code":
        asset["source_document"] = "docs/public/app.js"
        asset["wiki_path"] = "assets/app.js"
    elif damage == "asset-metadata":
        asset["source_document"] = "docs/public/.llm-wiki-knowledge/image.png"
    elif damage == "asset-output-escape":
        asset["wiki_path"] = "../overview.png"
    elif damage == "asset-extension":
        asset["wiki_path"] = "assets/overview.pdf"
    elif damage == "asset-case":
        profile["assets"].append({**asset, "wiki_path": "Assets/another.png"})
    elif damage == "asset-prefix":
        profile["assets"].append(
            {**asset, "wiki_path": "assets/overview.png/nested.png"}
        )
    elif damage == "asset-owner":
        asset["owner"] = ""
    elif damage == "adoption-extra":
        profile["adoptions"][0]["force"] = True
    elif damage == "adoption-hash":
        profile["adoptions"][0]["expected_hash"] = True
    elif damage == "adoption-reason":
        profile["adoptions"][0]["reason"] = ""
    elif damage == "operation-duplicate":
        profile["adoptions"].append({**profile["adoptions"][0]})
    elif damage == "operation-overlap":
        profile["removals"][0]["path"] = profile["adoptions"][0]["path"]
    elif damage == "remove-active":
        profile["removals"][0]["path"] = "assets/overview.png"
    elif damage == "native-control-output":
        asset["wiki_path"] = ".git/overview.png"
    else:
        profile["removals"][0]["path"] = ".llm-wiki-manifest.json"
    with pytest.raises(PublicationConfigError):
        validate_publication_config(payload, consumer_root=None)


@pytest.mark.parametrize(
    "url",
    [
        "http://github.com/org/repo",
        "https://user:secret@github.com/org/repo",
        "https://github.com/org/repo?ref=main",
        "https://github.com/org/repo#fragment",
        "https://github.com/org/repo/",
        "https://GitHub.com/org/repo",
        "https://github.com:443/org/repo",
        "https://github.com/org/repo.git",
        "https://github.com/org/repo/extra",
        "https://github.com/org/%2Frepo",
        "https://github.com:0/org/repo",
        "https://bad_host/org/repo",
    ],
)
def test_content_repository_url_is_explicit_canonical_https(url):
    payload = content_policy()
    payload["content"]["repository_url"] = url
    with pytest.raises(PublicationConfigError, match="repository_url"):
        validate_publication_config(payload, consumer_root=None)


def test_content_sources_keep_exact_case_and_directory_checks(tmp_path):
    payload = content_policy()
    source = tmp_path / "docs/public/images/overview.png"
    source.parent.mkdir(parents=True)
    source.write_bytes(b"public image")
    payload["content"]["assets"][0]["source_document"] = (
        "docs/public/images/Overview.png"
    )
    with pytest.raises(PublicationConfigError, match="case"):
        validate_publication_config(payload, consumer_root=tmp_path)
    payload = content_policy()
    payload["content"]["root"] = "docs/public/images/overview.png"
    with pytest.raises(PublicationConfigError, match="directory"):
        validate_publication_config(payload, consumer_root=tmp_path)


@pytest.mark.parametrize("count", [335, 336])
def test_contract_file_paths_retain_the_utf8_byte_bound(count):
    payload = policy()
    path = "docs/" + "é/" * count + "reference.json"
    assert len(path) < 1024
    payload["reference_providers"] = {"app": {"kind": "contract-file", "path": path}}
    if count == 335:
        assert len(path.encode("utf-8")) == 1024
        assert (
            validate_publication_config(payload, consumer_root=None)[
                "reference_providers"
            ]["app"]["path"]
            == path
        )
    else:
        with pytest.raises(PublicationConfigError, match="1024 UTF-8 bytes"):
            validate_publication_config(payload, consumer_root=None)


def test_reference_providers_are_explicit_sorted_detached_data_contracts(tmp_path):
    payload = policy()
    payload["reference_providers"] = {
        "project.v1": {"kind": "contract-file", "path": "docs/commands.json"},
        "cli.v1": {"kind": "llm-wiki-cli"},
    }
    payload["topics"][0]["depends_on"] = [
        {"reference": "cli.v1", "command": ["docs", "impact"]},
        {"reference": "project.v1"},
    ]
    normalized = validate_publication_config(payload, consumer_root=tmp_path)
    assert list(normalized["reference_providers"]) == ["cli.v1", "project.v1"]
    assert normalized["topics"][0]["depends_on"] == [
        {"reference": "cli.v1", "command": ["docs", "impact"]},
        {"reference": "project.v1", "command": []},
    ]
    normalized["reference_providers"]["project.v1"]["path"] = "other.json"
    normalized["topics"][0]["depends_on"][0]["command"].append("resolve")
    assert payload["reference_providers"]["project.v1"]["path"] == "docs/commands.json"
    assert payload["topics"][0]["depends_on"][0]["command"] == ["docs", "impact"]


def test_explicit_empty_provider_map_is_preserved():
    payload = policy()
    payload["reference_providers"] = {}
    assert (
        validate_publication_config(payload, consumer_root=None)["reference_providers"]
        == {}
    )


@pytest.mark.parametrize(
    "providers",
    [
        None,
        [],
        {"": {"kind": "llm-wiki-cli"}},
        {"cli/v1": {"kind": "llm-wiki-cli"}},
        {"cli.v1": "llm-wiki-cli"},
        {"cli.v1": {"kind": "executable", "path": "cli.py"}},
        {"cli.v1": {"kind": "llm-wiki-cli", "path": "cli.json"}},
        {"cli.v1": {"kind": "llm-wiki-cli", "entrypoint": "os:system"}},
        {"cli.v1": {"kind": "contract-file"}},
        {"cli.v1": {"kind": "contract-file", "path": "commands.py"}},
        {"cli.v1": {"kind": "contract-file", "path": "../commands.json"}},
        {"cli.v1": {"kind": "contract-file", "path": "/commands.json"}},
        {"cli.v1": {"kind": "contract-file", "path": "docs\\commands.json"}},
        {"cli.v1": {"kind": "llm-wiki-cli"}, "CLI.v1": {"kind": "llm-wiki-cli"}},
        {f"provider-{i}": {"kind": "llm-wiki-cli"} for i in range(65)},
    ],
)
def test_provider_definitions_reject_unsafe_unknown_and_ambiguous_contracts(providers):
    payload = policy()
    payload["reference_providers"] = providers
    with pytest.raises(PublicationConfigError):
        validate_publication_config(payload, consumer_root=None)


@pytest.mark.parametrize(
    "dependency",
    [
        {"reference": "not-declared"},
        {"reference": "CLI.v1"},
        {"reference": "cli.v1", "source_file": "cli.py"},
        {"reference": "cli.v1", "architecture_page": "modules/cli.md"},
        {"reference": "cli.v1", "section": "llm-wiki://modules/cli#section/@preamble"},
        {"reference": "cli.v1", "facets": ["whole"]},
        {"reference": "cli.v1", "command": "docs impact"},
        {"reference": "cli.v1", "command": [""]},
        {"reference": "cli.v1", "command": ["--help"]},
        {"reference": "cli.v1", "command": ["../impact"]},
        {"reference": "cli.v1", "command": ["docs impact"]},
        {"reference": "cli.v1", "command": ["impact\n"]},
        {"reference": "cli.v1", "command": [True]},
        {"reference": "cli.v1", "command": ["x" * 129]},
        {"reference": "cli.v1", "command": ["impact"] * 33},
        {"source_file": "cli.py", "command": []},
        {"architecture_page": "modules/cli.md", "command": []},
    ],
)
def test_reference_dependencies_require_a_declared_provider_and_literal_command_path(
    dependency,
):
    payload = policy()
    payload["reference_providers"] = {"cli.v1": {"kind": "llm-wiki-cli"}}
    payload["topics"][0]["depends_on"] = [dependency]
    with pytest.raises(PublicationConfigError):
        validate_publication_config(payload, consumer_root=None)


def test_reference_provider_is_never_implicitly_enabled():
    payload = policy()
    payload["topics"][0]["depends_on"] = [{"reference": "llm-wiki-cli"}]
    with pytest.raises(PublicationConfigError, match="declared reference provider"):
        validate_publication_config(payload, consumer_root=None)


def test_duplicate_reference_paths_share_the_existing_dependency_duplicate_guard():
    payload = policy()
    payload["reference_providers"] = {"cli.v1": {"kind": "llm-wiki-cli"}}
    payload["topics"][0]["depends_on"] = [
        {"reference": "cli.v1"},
        {"reference": "cli.v1", "command": []},
    ]
    with pytest.raises(PublicationConfigError, match="duplicates a dependency"):
        validate_publication_config(payload, consumer_root=None)
    payload["topics"][0]["depends_on"][1]["command"] = ["docs", "impact"]
    assert (
        len(
            validate_publication_config(payload, consumer_root=None)["topics"][0][
                "depends_on"
            ]
        )
        == 2
    )


def test_provider_contract_paths_use_consumer_root_and_shared_spelling_guards(
    tmp_path, monkeypatch
):
    payload = policy()
    payload["reference_providers"] = {
        "project.v1": {"kind": "contract-file", "path": "docs/commands.json"}
    }
    payload["topics"][0]["depends_on"] = [{"reference": "project.v1"}]
    outside = tmp_path / "outside"
    outside.mkdir()
    consumer = tmp_path / "consumer"
    consumer.mkdir()
    make_symlink(consumer / "docs", outside, directory=True)
    monkeypatch.chdir(outside)
    with pytest.raises(PublicationConfigError, match="symlink"):
        validate_publication_config(payload, consumer_root=consumer)
    assert (
        validate_publication_config(payload, consumer_root=None)["reference_providers"]
        == payload["reference_providers"]
    )
    payload["reference_providers"] = {
        "one.v1": {"kind": "contract-file", "path": "contracts/one.json"},
        "two.v1": {"kind": "contract-file", "path": "Contracts/two.json"},
    }
    payload["topics"][0]["depends_on"] = [{"reference": "one.v1"}]
    with pytest.raises(PublicationConfigError, match="collides"):
        validate_publication_config(payload, consumer_root=None)
