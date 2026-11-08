"""Exercise actual Git ref transactions and readback using local, isolated bare repositories."""

from __future__ import annotations

import importlib
import json
import subprocess

import pytest

from llm_wiki_cli.services.knowledge_evidence import sha256_bytes
from llm_wiki_cli.services.publication_candidate import (
    _read_tree,
    check_publication_candidate,
    export_publication_candidate,
    review_publication_candidate,
)
from llm_wiki_cli.services.publication_delivery import (
    review_rollback,
    validate_rollback_review,
)
from tests.test_publication_candidate import accept_topics


transport = importlib.import_module(
    "integrations.wiki-candidate.delivery.git_transport"
)


def git(cwd, *args, raw=None):
    command = [
        "git",
        "-C",
        str(cwd),
        "-c",
        "user.name=Fixture",
        "-c",
        "user.email=fixture@example.invalid",
        "-c",
        "core.autocrlf=false",
        "-c",
        "commit.gpgsign=false",
        *args,
    ]
    return subprocess.run(command, input=raw, capture_output=True, check=True).stdout


def head(cwd):
    return git(cwd, "rev-parse", "HEAD").decode().strip()


def commit(cwd):
    git(cwd, "add", "-A")
    git(cwd, "commit", "-qm", "fixture")
    return head(cwd)


def create(cwd, branch):
    cwd.mkdir()
    git(cwd, "init", "-q", "-b", branch)


@pytest.fixture
def repos(tmp_path):
    source = tmp_path / "consumer"
    target = source / "wiki"
    create(source, "primary")
    create(target, "pages")
    (target / "Home.md").write_bytes(b"# Home\n\nOriginal manual text.\n")
    (target / "Notes.md").write_bytes(b"# Manual\n")
    (target / "tool.txt").write_bytes(b"preserve mode\n")
    git(target, "add", ".")
    git(target, "update-index", "--chmod=+x", "tool.txt")
    git(target, "commit", "-qm", "initial manual wiki")
    tr = tmp_path / "remote.wiki.git"
    git(tmp_path, "clone", "--bare", str(target), str(tr))
    (source / ".gitignore").write_text("wiki/\n", encoding="utf-8")
    (source / "project").mkdir()
    (source / "project/app.py").write_bytes(b"def account():\n    return 3\n")
    (source / "docs").mkdir()
    (source / "docs/home.md").write_bytes(b"# Home\n\nNew public text.\n")
    (source / ".llm-wiki").mkdir()
    policy = {
        "schema_version": "llm-wiki-publication/v2",
        "architecture": {"baseline": "bootstrap-source", "root": "project"},
        "target": {"repository": "self", "kind": "github-wiki"},
        "enforcement": "required",
        "publish": True,
        "content": {
            "root": "docs",
            "adoptions": [
                {
                    "path": "Home.md",
                    "expected_hash": sha256_bytes((target / "Home.md").read_bytes()),
                    "reason": "Adopt the reviewed manual page",
                },
            ],
        },
        "topics": [
            {
                "id": "home",
                "owner": "maintainers",
                "edit_at": "repository",
                "wiki_page": "Home.md",
                "source_document": "docs/home.md",
                "depends_on": [{"source_file": "project/app.py"}],
            }
        ],
        "exclusions": [{"pattern": "*", "reason": "Only the home page participates."}],
    }
    (source / ".llm-wiki/publication.json").write_text(
        json.dumps(policy), encoding="utf-8"
    )
    commit(source)
    sr = tmp_path / "remote.git"
    git(tmp_path, "clone", "--bare", str(source), str(sr))
    return source, {
        "policy": policy,
        "source_repository": "example/project",
        "target_repository": "example/project",
        "source_remote": sr,
        "target_remote": tr,
    }


def prepare(source, tmp_path, previous=None):
    options = {
        "target_dir": "wiki",
        "previous_receipt": previous,
        "source_revision": head(source),
        "target_revision": head(source / "wiki"),
    }
    output = tmp_path / ("next-candidate" if previous else "candidate")
    receipt = export_publication_candidate(source, output_dir=output, **options)
    approval = review_publication_candidate(
        receipt, reviewer="reviewer", reason="Reviewed exact candidate"
    )
    ready = check_publication_candidate(
        source,
        candidate_dir=output,
        receipt=receipt,
        **options,
        reviews=accept_topics(receipt),
        candidate_review=approval,
    )
    assert ready["ready"]
    return {"receipt": ready, "files": _read_tree(output)}


def refresh_checkout(repo, remote, branch):
    git(repo, "fetch", str(remote), "refs/heads/" + branch)
    git(repo, "merge", "--ff-only", "--quiet", "FETCH_HEAD")


def change_source(source, options, *, new_text=None):
    options["policy"]["content"].pop("adoptions", None)
    (source / ".llm-wiki/publication.json").write_text(
        json.dumps(options["policy"]), encoding="utf-8"
    )
    if new_text:
        (source / "docs/home.md").write_bytes(new_text)
    commit(source)
    git(source, "push", str(options["source_remote"]), "HEAD:refs/heads/primary")


def change_manual(source, options):
    wiki = source / "wiki"
    refresh_checkout(wiki, options["target_remote"], "pages")
    (wiki / "Notes.md").write_bytes(b"# Manual\n\nLater editorial work.\n")
    result = commit(wiki)
    git(wiki, "push", str(options["target_remote"]), "HEAD:refs/heads/pages")
    return result


def test_fast_forward_readback_retry_and_stale_target(repos, tmp_path):
    source, options = repos
    candidate = prepare(source, tmp_path)
    target = options["target_remote"]
    base = head(target)
    result = transport.deliver(**candidate, **options)
    revision = head(target)
    assert result["readback_verified"] and result["target_revision"] == revision
    assert result["status"] == "delivered" and result["target_branch"] == "pages"
    assert git(target, "rev-parse", "HEAD^").decode().strip() == base
    assert git(target, "show", "HEAD:Home.md") == (source / "docs/home.md").read_bytes()
    assert git(target, "ls-tree", "HEAD", "tool.txt").startswith(b"100755 ")
    assert (
        json.loads(git(target, "show", "HEAD:" + transport.CHECKPOINT_PATH))
        == result["checkpoint"]
    )
    assert transport.deliver(**candidate, **options)["status"] == "already-delivered"
    assert head(target) == revision

    changed = change_manual(source, options)
    with pytest.raises(ValueError, match="(target|delivered|Delivered)"):
        transport.deliver(**candidate, **options)
    assert head(target) == changed


def test_reviewed_rollback_preserves_later_manual_changes(repos, tmp_path):
    source, options = repos
    first_candidate = prepare(source, tmp_path)
    first = transport.deliver(**first_candidate, **options)
    wiki = source / "wiki"
    refresh_checkout(wiki, options["target_remote"], "pages")
    change_source(source, options, new_text=b"# Home\n\nSecond reviewed text.\n")
    next_candidate = prepare(source, tmp_path, first_candidate["receipt"])
    second = transport.deliver(**next_candidate, **options)
    assert second["target_revision"] != first["target_revision"]
    target = options["target_remote"]
    live = change_manual(source, options)
    args = {
        **options,
        "source_revision": head(source),
        "target_revision": live,
        "restore_revision": first["target_revision"],
    }
    proposal = transport.preview_rollback(**args)
    assert "Second reviewed text" in proposal["diff"] and head(target) == live
    approval = review_rollback(
        proposal, reviewer="maintainer", reason="Reviewed the bound restoration diff"
    )
    validate_rollback_review(approval, rollback_id=proposal["rollback_id"])
    with pytest.raises(ValueError, match="approval"):
        transport.rollback(**args, accepted_rollback_id="sha256:" + "0" * 64)
    assert head(target) == live
    result = transport.rollback(**args, accepted_rollback_id=proposal["rollback_id"])
    assert result["status"] == "rolled-back" and result["readback_verified"]
    assert git(target, "rev-parse", "HEAD^").decode().strip() == live
    assert git(target, "show", "HEAD:Home.md") == first_candidate["files"]["Home.md"]
    assert (
        git(target, "show", "HEAD:Notes.md") == b"# Manual\n\nLater editorial work.\n"
    )
    assert (
        transport.rollback(**args, accepted_rollback_id=proposal["rollback_id"])[
            "status"
        ]
        == "already-delivered"
    )


def test_verified_noop_first_restore_and_older_source_refusal(repos, tmp_path):
    source, options = repos
    initial = head(source / "wiki")
    candidate = prepare(source, tmp_path)
    first = transport.deliver(**candidate, **options)
    wiki = source / "wiki"
    refresh_checkout(wiki, options["target_remote"], "pages")
    change_source(source, options)
    second = prepare(source, tmp_path, candidate["receipt"])
    unchanged = transport.deliver(**second, **options)
    assert unchanged["status"] == "unchanged"
    assert unchanged["target_revision"] == first["target_revision"]
    with pytest.raises(ValueError, match="stale"):
        transport.deliver(**candidate, **options)
    restore = {
        **options,
        "source_revision": head(source),
        "target_revision": head(options["target_remote"]),
        "restore_revision": initial,
    }
    proposal = transport.preview_rollback(**restore)
    result = transport.rollback(**restore, accepted_rollback_id=proposal["rollback_id"])
    assert result["checkpoint"]["owned"] == {} and result["checkpoint"][
        "source_revision"
    ] == head(source)
    assert (
        git(options["target_remote"], "show", "HEAD:Home.md")
        == b"# Home\n\nOriginal manual text.\n"
    )
    # Even if the eligible ref itself is rewound, the durable high-water check rejects the older source.
    git(
        options["source_remote"],
        "update-ref",
        "refs/heads/primary",
        candidate["receipt"]["context"]["source_revision"],
    )
    with pytest.raises(ValueError, match="last published source"):
        transport.deliver(**candidate, **options)


@pytest.mark.parametrize("race", ["delete", "rewind", "advance"])
def test_normal_push_requires_the_reviewed_advertised_old_tip(
    repos, tmp_path, monkeypatch, race
):
    source, options = repos
    target = options["target_remote"]
    wiki = source / "wiki"
    original = head(wiki)
    (wiki / "Notes.md").write_bytes(b"# Manual\n\nReview basis\n")
    base = commit(wiki)
    git(wiki, "push", str(target), "HEAD:refs/heads/pages")
    candidate = prepare(source, tmp_path)
    push = transport._push

    def change_advertisement(session, commit_id):
        if race == "delete":
            git(target, "update-ref", "-d", "refs/heads/pages", base)
        elif race == "rewind":
            git(target, "update-ref", "refs/heads/pages", original, base)
        else:
            (wiki / "Notes.md").write_bytes(b"# Manual\n\nConcurrent\n")
            commit(wiki)
            git(wiki, "push", str(target), "HEAD:refs/heads/pages")
        return push(session, commit_id)

    monkeypatch.setattr(transport, "_push", change_advertisement)
    with pytest.raises(ValueError):
        transport.deliver(**candidate, **options)
    if race == "delete":
        assert (
            git(target, "for-each-ref", "--format=%(refname)", "refs/heads/pages")
            == b""
        )
    elif race == "rewind":
        assert head(target) == original
    else:
        assert git(target, "show", "HEAD:Notes.md") == b"# Manual\n\nConcurrent\n"


def test_failed_readback_requires_reconciliation_and_never_repushes(
    repos, tmp_path, monkeypatch
):
    source, options = repos
    candidate = prepare(source, tmp_path)
    fetch = transport._fetch

    def unavailable(repo, *args, **kwargs):
        if repo.name == "readback":
            raise transport.DeliveryError("readback unavailable")
        return fetch(repo, *args, **kwargs)

    with monkeypatch.context() as patch:
        patch.setattr(transport, "_fetch", unavailable)
        with pytest.raises(transport.DeliveryError, match="readback unavailable"):
            transport.deliver(**options, **candidate)
    landed = head(options["target_remote"])
    monkeypatch.setattr(
        transport, "_push", lambda *args: pytest.fail("An ambiguous push was repeated")
    )
    assert transport.deliver(**options, **candidate)["target_revision"] == landed


@pytest.mark.parametrize("operation", ["deliver", "rollback"])
def test_replay_reconstructs_the_reviewed_git_tree_including_file_modes(
    repos, tmp_path, monkeypatch, operation
):
    source, options = repos
    candidate = prepare(source, tmp_path)
    target = options["target_remote"]
    base = head(target)
    delivered = transport.deliver(**options, **candidate)
    retry_options = {**options, **candidate}
    if operation == "rollback":
        restore = {
            **options, "source_revision": head(source),
            "target_revision": delivered["target_revision"], "restore_revision": base,
        }
        plan = transport.preview_rollback(**restore)
        transport.rollback(**restore, accepted_rollback_id=plan["rollback_id"])
        retry_options = {**restore, "accepted_rollback_id": plan["rollback_id"]}

    landed = head(target)
    parent = git(target, "rev-parse", f"{landed}^").decode().strip()
    # Rebuild the same direct child of the reviewed base with identical blobs
    # and checkpoint, but a different mode for an owned/restored page.
    listing = git(target, "ls-tree", "-z", landed).split(b"\0")
    changed = [row.replace(b"100644 ", b"100755 ", 1) if row.endswith(b"\tHome.md") else row for row in listing]
    assert listing != changed
    tree = git(target, "mktree", "-z", raw=b"\0".join(changed)).decode().strip()
    replacement = git(target, "commit-tree", tree, "-p", parent, raw=b"Mode correction\n").decode().strip()
    git(target, "update-ref", "refs/heads/pages", replacement, landed)
    monkeypatch.setattr(transport, "_push", lambda *args: pytest.fail("A replay wrote to the wiki"))
    with pytest.raises(transport.DeliveryError, match="reviewed Git tree"):
        getattr(transport, operation)(**retry_options)
    assert head(target) == replacement


def test_read_only_qualification_default_branches_and_exact_release_tag(repos):
    source, options = repos
    target = options["target_remote"]
    initial = head(target)
    args = {**options, "source_revision": head(source)}
    result = transport.qualify(**args)
    assert result["status"] == "reachable" and result["target_branch"] == "pages"
    assert not result["write_verified"] and head(target) == initial
    with pytest.raises(ValueError, match="ineligible"):
        transport.qualify(**args, source_ref="refs/heads/not-default")
    git(
        options["source_remote"],
        "-c",
        "user.name=Fixture",
        "tag",
        "-a",
        "release-1",
        "-m",
        "release",
        head(source),
    )
    args["policy"] = {
        **options["policy"],
        "source_policy": "release",
        "release_tag": "release-1",
        "target": {
            "kind": "github-wiki",
            "repository": "self",
            "branch": "custom/wiki",
        },
    }
    git(target, "update-ref", "refs/heads/custom/wiki", initial)
    assert (
        transport.qualify(**args, source_ref="refs/tags/release-1")["target_branch"]
        == "custom/wiki"
    )
    with pytest.raises(ValueError, match="exact tag"):
        transport.qualify(**args, source_ref="refs/tags/another")


def test_qualification_distinguishes_empty_target_and_rejects_untrusted_url(
    repos, tmp_path
):
    source, options = repos
    empty = tmp_path / "empty.git"
    git(tmp_path, "init", "--bare", "-q", str(empty))
    args = {**options, "source_revision": head(source), "target_remote": empty}
    with pytest.raises(ValueError, match="no initialized default"):
        transport.qualify(**args)
    args["target_remote"] = "https://example.invalid/not-the-wiki"
    with pytest.raises(ValueError, match="authorized GitHub repository"):
        transport.qualify(**args)


def test_source_rechecked_after_tree_construction_before_push(
    repos, tmp_path, monkeypatch
):
    source, options = repos
    candidate = prepare(source, tmp_path)
    target = options["target_remote"]
    base = head(target)
    write_tree = transport._tree

    def source_advanced(*args):
        tree = write_tree(*args)
        change_source(source, options, new_text=b"# Home\n\nChanged source\n")
        return tree

    monkeypatch.setattr(transport, "_tree", source_advanced)
    with pytest.raises(transport.DeliveryError, match="Source revision is stale"):
        transport.deliver(**candidate, **options)
    assert head(target) == base


def test_lost_push_acknowledgement_reconciled_by_fresh_readback(
    repos, tmp_path, monkeypatch
):
    source, options = repos
    candidate = prepare(source, tmp_path)
    push = transport._push
    attempts = []

    def lose_response(session, commit_id):
        attempts.append(commit_id)
        assert push(session, commit_id).returncode == 0
        raise transport.DeliveryError("transport timed out")

    monkeypatch.setattr(transport, "_push", lose_response)
    result = transport.deliver(**candidate, **options)
    assert result["readback_verified"] and attempts == [result["target_revision"]]
    assert head(options["target_remote"]) == result["target_revision"]


@pytest.mark.parametrize("change", ["removed", "rewritten"])
def test_manual_checkpoint_change_never_establishes_a_new_delivery_base(
    repos, tmp_path, change
):
    from llm_wiki_cli.services.knowledge_evidence import canonical_json_bytes, hash_json

    source, options = repos
    transport.deliver(**prepare(source, tmp_path), **options)
    wiki = source / "wiki"
    refresh_checkout(wiki, options["target_remote"], "pages")
    marker = wiki / transport.CHECKPOINT_PATH
    if change == "removed":
        marker.unlink()
    else:
        fields = json.loads(marker.read_bytes())
        fields.pop("checkpoint_id")
        fields["provider_fingerprint"] = "sha256:" + "1" * 64
        fields["checkpoint_id"] = hash_json(fields)
        marker.write_bytes(canonical_json_bytes(fields) + b"\n")
    commit(wiki)
    git(wiki, "push", str(options["target_remote"]), "HEAD:refs/heads/pages")
    with pytest.raises(
        transport.DeliveryError,
        match="(previous delivery checkpoint|introducing Git commit)",
    ):
        transport.qualify(**options, source_revision=head(source))


def test_rollback_rejects_an_unpublished_side_parent(repos, tmp_path):
    source, options = repos
    deployed = transport.deliver(**prepare(source, tmp_path), **options)
    target = options["target_remote"]
    original = deployed["target_revision"]
    side = (
        git(target, "commit-tree", "HEAD^{tree}", "-p", original, raw=b"Side history\n")
        .decode()
        .strip()
    )
    merged = (
        git(
            target,
            "commit-tree",
            "HEAD^{tree}",
            "-p",
            original,
            "-p",
            side,
            raw=b"Merge\n",
        )
        .decode()
        .strip()
    )
    git(target, "update-ref", "refs/heads/pages", merged, original)
    with pytest.raises(ValueError, match="first-parent"):
        transport.preview_rollback(
            **options,
            source_revision=head(source),
            target_revision=merged,
            restore_revision=side,
        )


def test_https_credentials_are_scoped_to_one_remote_and_ambient_git_settings_are_excluded(
    tmp_path, monkeypatch
):
    import base64

    url = "https://github.com/example/project.wiki.git"
    secret = "delivery-fixture-token"
    remote = transport._remote(url, "example/project", wiki=True, token=secret)
    monkeypatch.setenv("GIT_CONFIG_COUNT", "50")
    monkeypatch.setenv("GIT_CONFIG_KEY_2", "ignored")
    monkeypatch.setenv("GIT_ASKPASS", "ignored")
    monkeypatch.setenv("SOURCE_TOKEN", "source-fixture-token")

    def inspect(command, **kwargs):
        env = kwargs["env"]
        assert secret not in repr(command) and "source-fixture-token" not in repr(env)
        assert "GIT_ASKPASS" not in env and "GIT_CONFIG_KEY_2" not in env
        assert env["GIT_CONFIG_COUNT"] == "1"
        assert env["GIT_CONFIG_KEY_0"] == f"http.{url}.extraHeader"
        assert (
            env["GIT_CONFIG_VALUE_0"]
            == "Authorization: Basic "
            + base64.b64encode(f"x-access-token:{secret}".encode()).decode()
        )
        assert "http.followRedirects=false" in command
        return subprocess.CompletedProcess(command, 0, b"", b"")

    monkeypatch.setattr(subprocess, "run", inspect)
    transport._git(tmp_path, "ls-remote", "--", url, remote=remote)
