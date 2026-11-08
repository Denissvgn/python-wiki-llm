"""Mapped public edits follow author, reviewer and supervisor workspace boundaries."""

import json

import pytest

from llm_wiki_cli.services.documentation_policy import hash_bytes
from llm_wiki_cli.services.documentation_run import (
    DocumentationIntegrityError,
    DocumentationTransitionError,
    build_documentation_agent_packet,
    get_documentation_run_status,
    prepare_documentation_run,
    record_documentation_agent_result,
    verify_documentation_run,
)
from llm_wiki_cli.services.documentation_run.publication import (
    bind_publication_workspace,
    collect_reviewed_publication_edits,
)
from llm_wiki_cli.services.knowledge_evidence import hash_json
from tests.test_documentation_protocol import _agent_result


@pytest.fixture
def mapped(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    (source / "app.py").write_text(
        '"""Public API."""\ndef run():\n    return "yes"\n', encoding="utf-8"
    )
    workspace = tmp_path / "workspace"
    run = prepare_documentation_run(workspace, source_root=source, site_name="Consumer")
    original = b"# Overview\n\nSupported command: old.\n"
    name = "public/readme.md"
    topic = {
        "id": "overview",
        "wiki_page": "Home.md",
        "source_document": name,
        "before_hash": hash_bytes(original),
    }
    binding = {
        "schema_version": "llm-wiki-publication-maintenance-binding/v1",
        "topics": [topic],
    }
    binding["binding_id"] = hash_json(binding)
    bind_publication_workspace(workspace, binding=binding, documents={name: original})
    packet = build_documentation_agent_packet(workspace, stage="wiki-enrichment")
    assert packet.to_dict()["mapped_publication"]["binding_id"] == binding["binding_id"]
    work = json.loads((workspace / run.evidence["semantic_worklist"]).read_bytes())[
        "items"
    ]
    cited = sorted({item["canonical_path"] for item in work})
    record_documentation_agent_result(
        workspace,
        _agent_result(
            run.run_id,
            "wiki-enrichment",
            completed=[item["id"] for item in work],
            claims=cited,
        ),
        actor="researcher",
    )
    packet = build_documentation_agent_packet(workspace, stage="user-docs")
    assert packet.to_dict()["allowed_writes"] == [
        "mapped-docs/" + name,
        ".llm-wiki-docs/results/user-docs.json",
    ]
    return workspace, run.run_id, name, binding


def _author(mapped):
    workspace, run_id, name, _ = mapped
    (workspace / "mapped-docs" / name).write_bytes(
        b"# Overview\n\nSupported command: run.\n"
    )
    result = _agent_result(run_id, "user-docs", claims=["modules/app.md"])
    result["changed_document_paths"] = [name]
    return record_documentation_agent_result(workspace, result, actor="author")


def test_mapped_publication_accepts_exact_independently_reviewed_bytes(mapped):
    workspace, run_id, name, binding = mapped
    _author(mapped)
    with pytest.raises(DocumentationTransitionError):
        collect_reviewed_publication_edits(workspace, binding=binding)
    packet = build_documentation_agent_packet(workspace, stage="review")
    assert not any("mapped-docs" in p for p in packet.to_dict()["allowed_writes"])
    review = _agent_result(run_id, "review", claims=["modules/app.md"])
    for actor in ("Author", "researcher"):
        with pytest.raises(DocumentationTransitionError, match="reviewer"):
            record_documentation_agent_result(workspace, review, actor=actor)
    record_documentation_agent_result(workspace, review, actor="reader")
    with pytest.raises(DocumentationTransitionError):
        collect_reviewed_publication_edits(workspace, binding=binding)
    assert verify_documentation_run(workspace).ok
    assert verify_documentation_run(workspace).ok
    assert "docs wiki patch" in get_documentation_run_status(workspace).next_actions[0]
    with pytest.raises(DocumentationTransitionError, match="hand off"):
        build_documentation_agent_packet(workspace, stage="review")
    identity, files = collect_reviewed_publication_edits(workspace, binding=binding)
    assert (identity["author"], identity["reviewer"]) == ("author", "reader")
    assert files[name] == (workspace / "mapped-docs" / name).read_bytes()
    (workspace / "mapped-docs" / name).write_bytes(b"Unreviewed replacement")
    with pytest.raises(DocumentationIntegrityError):
        collect_reviewed_publication_edits(workspace, binding=binding)


@pytest.mark.parametrize(
    "path",
    ["mapped-docs/extra.md", ".llm-wiki-docs/evidence/extra.json", "site/copied.md"],
)
def test_mapped_stage_blocks_writes_beyond_the_assigned_document(mapped, path):
    workspace = mapped[0]
    (workspace / path).write_bytes(b"unexpected")
    with pytest.raises(DocumentationIntegrityError):
        _author(mapped)


def test_out_of_stage_edit_cannot_enter_the_review_packet(mapped):
    workspace, _, name, _ = mapped
    _author(mapped)
    (workspace / "mapped-docs" / name).write_bytes(b"edited after result")
    with pytest.raises(DocumentationIntegrityError):
        build_documentation_agent_packet(workspace, stage="review")


def test_partial_binding_rolls_back_and_can_be_retried(tmp_path, monkeypatch):
    from llm_wiki_cli.services.documentation_run import publication

    source = tmp_path / "repo"
    source.mkdir()
    (source / "app.py").write_text("def public(): pass\n", encoding="utf-8")
    root = tmp_path / "workspace"
    prepare_documentation_run(root, source_root=source, site_name="Consumer")
    documents = {"guide.md": b"# Original\n"}
    topic = {
        "id": "guide",
        "wiki_page": "Guide.md",
        "source_document": "guide.md",
        "before_hash": hash_bytes(documents["guide.md"]),
    }
    binding = {
        "schema_version": "llm-wiki-publication-maintenance-binding/v1",
        "topics": [topic],
    }
    binding["binding_id"] = hash_json(binding)
    original = publication.atomic_write_private_bytes
    run_path = root / ".llm-wiki-docs/run.json"
    saved = run_path.read_bytes()

    def fail_commit(path, *args, **kwargs):
        if path == run_path:
            raise OSError("injected commit failure")
        return original(path, *args, **kwargs)

    with monkeypatch.context() as edits:
        edits.setattr(publication, "atomic_write_private_bytes", fail_commit)
        with pytest.raises(OSError, match="commit failure"):
            bind_publication_workspace(root, binding=binding, documents=documents)
    assert run_path.read_bytes() == saved
    assert not (root / publication.MAPPED).exists()
    assert not (root / publication.BINDING).exists()
    bind_publication_workspace(root, binding=binding, documents=documents)
    bind_publication_workspace(root, binding=binding, documents=documents)
    (root / publication.MAPPED / "guide.md").write_text("unexpected", encoding="utf-8")
    with pytest.raises(DocumentationIntegrityError, match="outside"):
        bind_publication_workspace(root, binding=binding, documents=documents)
