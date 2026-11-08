"""Fast-forward delivery to an initialized sibling wiki, verified through Git readback."""

from __future__ import annotations

import base64
from contextlib import contextmanager
from dataclasses import dataclass, field
import os
from pathlib import Path
import re
import subprocess
from tempfile import TemporaryDirectory

from llm_wiki_cli.services.knowledge_evidence import hash_json, sha256_bytes
from llm_wiki_cli.services.publication_candidate import (
    MAX_FILE_BYTES,
    MAX_FILES,
    MAX_TREE_BYTES,
)
from llm_wiki_cli.services.publication_config import (
    publication_repository,
    validate_publication_config,
)
from llm_wiki_cli.services.publication_delivery import (
    CHECKPOINT_PATH,
    plan_delivery,
    plan_rollback,
    split_delivery_tree,
)
from llm_wiki_cli.services.validation import require_portable_relative_path


_OID = re.compile(r"(?:[0-9a-f]{40}|[0-9a-f]{64})")
# Git passes the ref advertisement used by its ensuing receive-pack transaction
# to pre-push. A plain fast-forward check alone permits branch recreation or a
# concurrent rewind. Reject both, without using a force refspec or a force flag.
_PRE_PUSH = """#!/bin/sh
set -eu
IFS=' ' read -r local_ref new_oid remote_ref old_oid
test "$new_oid" = "$WIKI_NEW_OID" && test "$remote_ref" = "$WIKI_DEST_REF" && test "$old_oid" = "$WIKI_OLD_OID" || exit 1
if IFS= read -r extra; then exit 1; fi
exit 0
"""


class DeliveryError(ValueError):
    """Delivery could not be verified; no local success checkpoint is available."""


def _oid(value):
    if not isinstance(value, str) or not _OID.fullmatch(value):
        raise DeliveryError("Expected a full lowercase Git object ID")
    return value


@dataclass(frozen=True)
class _Remote:
    url: str
    protocol: str
    token: str | None = field(repr=False)


def _remote(value, repository, *, wiki, token):
    publication_repository(repository, "repository")
    if isinstance(value, Path):
        # Only trusted local callers can opt into the bare-repository fixture
        # transport. Hosted entry points always construct an HTTPS string.
        if (
            token
            or not value.is_absolute()
            or not (value / "objects").is_dir()
            or not (value / "HEAD").is_file()
        ):
            raise DeliveryError(
                "Local transport requires an explicit absolute bare repository and no credential"
            )
        return _Remote(str(value.resolve(strict=True)), "file", None)
    expected = f"https://github.com/{repository}{'.wiki' if wiki else ''}.git"
    if value != expected:
        raise DeliveryError("Remote URL differs from the authorized GitHub repository")
    if token is not None and (
        not isinstance(token, str) or not token.isascii() or not token.isprintable()
    ):
        raise DeliveryError("Invalid GitHub transport credential")
    return _Remote(expected, "https", token)


def _git(directory, *arguments, remote=None, raw=None, extra_env=None, check=True):
    env = {
        key: os.environ[key]
        for key in ("PATH", "SystemRoot", "SYSTEMROOT", "TMP", "TEMP", "TMPDIR")
        if key in os.environ
    }
    env.update(
        {
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_CEILING_DIRECTORIES": str(directory.parent),
            "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_TERMINAL_PROMPT": "0",
            "GIT_ATTR_NOSYSTEM": "1",
            "GIT_ALLOW_PROTOCOL": remote.protocol if remote else "file:https",
            "GIT_AUTHOR_NAME": "Wiki delivery",
            "GIT_COMMITTER_NAME": "Wiki delivery",
            "GIT_AUTHOR_EMAIL": "wiki-delivery@users.noreply.github.com",
            "GIT_COMMITTER_EMAIL": "wiki-delivery@users.noreply.github.com",
            "LC_ALL": "C",
        }
    )
    if remote and remote.token:
        auth = base64.b64encode(("x-access-token:" + remote.token).encode()).decode()
        env.update(
            GIT_CONFIG_COUNT="1",
            GIT_CONFIG_KEY_0=f"http.{remote.url}.extraHeader",
            GIT_CONFIG_VALUE_0="Authorization: Basic " + auth,
        )
    if extra_env:
        env.update(extra_env)
    command = [
        "git",
        "--no-replace-objects",
        "--literal-pathspecs",
        "-c",
        "credential.helper=",
        "-c",
        "http.followRedirects=false",
        "-c",
        "gc.auto=0",
        "-C",
        str(directory),
        *arguments,
    ]
    try:
        result = subprocess.run(
            command,
            input=raw if raw is not None else b"",
            capture_output=True,
            env=env,
            timeout=180,
        )
    except (OSError, subprocess.TimeoutExpired):
        raise DeliveryError(
            "Git transport unavailable or timed out; reconcile the remote before retrying"
        ) from None
    if check and result.returncode:
        # Never relay Git/server-provided strings to logs, evidence, or the runner command parser.
        if any(
            x in result.stderr.lower()
            for x in (
                b"authentication failed",
                b"403",
                b"401",
                b"could not read username",
            )
        ):
            raise DeliveryError("Git authentication or authorization failed")
        raise DeliveryError(
            "Git operation failed; verify repository access, reference and connectivity"
        )
    return result


def _text(directory, *args):
    return _git(directory, *args).stdout.decode("ascii").strip()


def _resolve(directory, remote, requested=None):
    if requested is not None:
        if (
            "\x00" in requested
            or _git(directory, "check-ref-format", requested, check=False).returncode
        ):
            raise DeliveryError("Invalid source or target reference")
        patterns = [requested, requested + "^{}"]
    else:
        patterns = ["HEAD"]
    raw = _git(
        directory, "ls-remote", "--symref", "--", remote.url, *patterns, remote=remote
    ).stdout
    rows = {}
    symbolic = None
    for line in raw.decode("utf-8").splitlines():
        value, name = line.split("\t", 1)
        if value.startswith("ref: ") and name == "HEAD":
            symbolic = value[5:]
        else:
            rows[name] = _oid(value)
    if requested:
        if requested not in rows:
            raise DeliveryError(
                "Configured reference is absent from the accessible repository"
            )
        return requested, rows.get(requested + "^{}", rows[requested])
    if not symbolic or not symbolic.startswith("refs/heads/") or "HEAD" not in rows:
        raise DeliveryError("Accessible repository has no initialized default branch")
    if _git(directory, "check-ref-format", symbolic, check=False).returncode:
        raise DeliveryError("Invalid remote default branch advertisement")
    return symbolic, rows["HEAD"]


def _fetch(repo, remote, ref, expected, *, ancestry_only=False):
    args = ["fetch", "--no-tags", "--no-recurse-submodules"]
    if ancestry_only:
        args.append("--filter=tree:0")
    _git(repo, *args, "--", remote.url, ref, remote=remote)
    if _text(repo, "rev-parse", "--verify", "FETCH_HEAD^{commit}") != expected:
        raise DeliveryError("Remote revision changed during fetch")


def _new_repo(root, name, oid):
    directory = root / name
    directory.mkdir()
    _git(
        directory,
        "init",
        "--bare",
        "--quiet",
        "--initial-branch=wiki-verification",
        "--template=",
        "--object-format=" + ("sha1" if len(oid) == 40 else "sha256"),
    )
    return directory


def _read(repo, revision):
    # Inspect raw blobs, never a checkout. Attributes, smudge/clean filters and
    # platform checkout conversions must not change the bytes under review.
    listing = _git(
        repo, "ls-tree", "-r", "-z", "-l", "--full-tree", _oid(revision)
    ).stdout
    entries = {}
    total = 0
    for row in listing.split(b"\0"):
        if not row:
            continue
        metadata, name = row.split(b"\t", 1)
        mode, kind, blob, size = metadata.split()
        path = require_portable_relative_path(name.decode("utf-8"))
        if kind != b"blob" or mode not in {b"100644", b"100755"} or path in entries:
            raise DeliveryError(
                "Wiki Git trees must contain only uniquely named regular files"
            )
        if path == CHECKPOINT_PATH and mode != b"100644":
            raise DeliveryError("Invalid checkpoint file mode")
        length = int(size)
        total += length
        if (
            length > MAX_FILE_BYTES
            or total > MAX_TREE_BYTES + MAX_FILE_BYTES
            or len(entries) >= MAX_FILES + 1
        ):
            raise DeliveryError("Wiki Git tree exceeds publication limits")
        entries[path] = (mode, blob.decode("ascii"), length)

    files = {}
    objects = {oid: b"" for _, oid, _ in entries.values()}
    if objects:
        batch = _git(
            repo,
            "cat-file",
            "--batch",
            raw="".join(oid + "\n" for oid in objects).encode(),
        ).stdout
        offset = 0
        for oid in objects:
            end = batch.index(b"\n", offset)
            name, kind, size = batch[offset:end].split()
            stop = end + 1 + int(size)
            if (
                name.decode("ascii") != oid
                or kind != b"blob"
                or batch[stop : stop + 1] != b"\n"
            ):
                raise DeliveryError("Git blob readback is incomplete")
            objects[oid] = batch[end + 1 : stop]
            offset = stop + 1
    for path, (_, oid, length) in entries.items():
        raw = objects[oid]
        if len(raw) != length:
            raise DeliveryError("Git tree and blob sizes differ")
        files[path] = raw
    return files, entries


def _last_checkpoint_commit(repo, revision):
    return _text(
        repo,
        "log",
        "--first-parent",
        "-1",
        "--format=%H",
        revision,
        "--",
        CHECKPOINT_PATH,
    )


def _checkpoint(repo, revision, files):
    """Relate the observed marker to the commit and prior state it claims."""
    public, state = split_delivery_tree(files)
    introduced = _last_checkpoint_commit(repo, revision)
    if state is None:
        if introduced:
            raise DeliveryError(
                "A previous delivery checkpoint was removed; reconcile the wiki history"
            )
        return None
    if not introduced:
        raise DeliveryError("Checkpoint has no introducing commit")
    parent = state["target_base_revision"]
    if _text(repo, "show", "-s", "--format=%P", introduced).split() != [parent]:
        raise DeliveryError("Checkpoint differs from its introducing Git commit")
    if introduced != revision:
        original, _ = _read(repo, introduced)
        public, recorded = split_delivery_tree(original)
        if recorded != state:
            raise DeliveryError("Checkpoint differs from its committed content")
    if state["tree_hash"] != hash_json(
        {path: sha256_bytes(raw) for path, raw in public.items()}
    ):
        raise DeliveryError("Original delivery tree differs from its checkpoint")
    previous_files, _ = _read(repo, parent)
    _, previous = split_delivery_tree(previous_files)
    if previous is None and _last_checkpoint_commit(repo, parent):
        raise DeliveryError("Previous delivery checkpoint was removed")
    if state["previous_checkpoint_id"] != (
        previous["checkpoint_id"] if previous else None
    ):
        raise DeliveryError("Checkpoint predecessor differs from its Git parent")
    return state


def _tree(repo, parent, before, entries, desired, restore_modes):
    _git(repo, "read-tree", parent)
    updates = []
    for path in sorted(before.keys() - desired.keys()):
        updates.append(f"0 {'0' * len(parent)}\t{path}\0".encode())
    for path, raw in sorted(desired.items()):
        mode = restore_modes.get(
            path, entries[path][0] if path in entries else b"100644"
        )
        if path in entries and raw == before[path] and mode == entries[path][0]:
            continue
        blob = _git(
            repo, "hash-object", "-w", "--no-filters", "--stdin", raw=raw
        ).stdout.strip()
        updates.append(mode + b" " + blob + b"\t" + path.encode() + b"\0")
    if updates:
        _git(repo, "update-index", "-z", "--index-info", raw=b"".join(updates))
    return _oid(_text(repo, "write-tree"))


@dataclass
class _Session:
    root: Path
    source: _Remote
    target: _Remote
    repo: Path
    source_ref: str | None
    source_line: str
    source_sha: str
    branch_choice: str | None
    branch: str
    head: str

    def verify_source(self):
        if _resolve(self.root, self.source, self.source_ref) != (
            self.source_line,
            self.source_sha,
        ):
            raise DeliveryError(
                "Source revision is stale; prepare and review a fresh candidate"
            )

    def verify_target(self, expected):
        if _resolve(self.root, self.target, self.branch_choice) != (
            self.branch,
            expected,
        ):
            raise DeliveryError(
                "Wiki target branch or revision changed; fetch and review the new base"
            )

    def check_high_water(self, checkpoint):
        if checkpoint and checkpoint["source_revision"] != self.source_sha:
            source_ref, sha = _resolve(self.root, self.source, self.source_ref)
            if (source_ref, sha) != (self.source_line, self.source_sha):
                raise DeliveryError("Source revision is stale")
            source_repo = _new_repo(self.root, "source", sha)
            _fetch(source_repo, self.source, source_ref, sha, ancestry_only=True)
            ancestor = _oid(checkpoint["source_revision"])
            if _git(
                source_repo, "merge-base", "--is-ancestor", ancestor, sha, check=False
            ).returncode:
                raise DeliveryError(
                    "Source does not descend from the last published source revision"
                )

    def readback(self, revision, expected_tree, desired):
        # New object database: local post-push objects cannot satisfy this proof.
        self.verify_target(revision)
        read = _new_repo(self.root, "readback", revision)
        _fetch(read, self.target, self.branch, revision)
        actual, _ = _read(read, revision)
        if (
            _text(read, "rev-parse", revision + "^{tree}") != expected_tree
            or actual != desired
        ):
            raise DeliveryError(
                "Wiki readback differs from the proposed tree; reconcile before retrying"
            )
        self.verify_target(revision)
        self.verify_source()


@contextmanager
def _session(
    *,
    policy,
    source_repository,
    target_repository,
    source_remote,
    target_remote,
    source_revision,
    source_ref=None,
    source_token=None,
    target_token=None,
):
    policy = validate_publication_config(policy, consumer_root=None)
    target_config = policy["target"]
    expected_target = (
        source_repository
        if target_config["repository"] == "self"
        else target_config["repository"]
    )
    if target_repository.lower() != expected_target.lower():
        raise DeliveryError("Target repository differs from policy")
    source = _remote(source_remote, source_repository, wiki=False, token=source_token)
    target = _remote(target_remote, target_repository, wiki=True, token=target_token)
    if source.url == target.url or (
        source.protocol == target.protocol == "https"
        and source.url.lower() == target.url.lower()
    ):
        raise DeliveryError("The wiki target and source must be separate repositories")
    if policy["source_policy"] == "release":
        expected = "refs/tags/" + policy.get("release_tag", "")
        if not policy.get("release_tag") or source_ref not in (None, expected):
            raise DeliveryError("Release delivery requires the configured exact tag")
        source_ref = expected
    with TemporaryDirectory(prefix="wiki-delivery-") as tmp:
        root = Path(tmp)
        # Default-branch eligibility always follows remote HEAD, including
        # when a caller also supplies the expected triggering branch.
        lookup = source_ref if policy["source_policy"] == "release" else None
        actual_ref, actual_sha = _resolve(root, source, lookup)
        if (source_ref is not None and source_ref != actual_ref) or actual_sha != _oid(
            source_revision
        ):
            raise DeliveryError("Source revision or branch is stale or ineligible")
        branch_choice = (
            "refs/heads/" + target_config["branch"]
            if "branch" in target_config
            else None
        )
        branch, head = _resolve(root, target, branch_choice)
        repo = _new_repo(root, "wiki", head)
        _fetch(repo, target, branch, head)
        yield _Session(
            root,
            source,
            target,
            repo,
            lookup,
            actual_ref,
            actual_sha,
            branch_choice,
            branch,
            head,
        )


def _push(session, commit):
    hooks = session.root / "hooks"
    hooks.mkdir()
    hook = hooks / "pre-push"
    hook.write_bytes(_PRE_PUSH.encode())
    hook.chmod(0o700)
    return _git(
        session.repo,
        "-c",
        f"core.hooksPath={hooks.as_posix()}",
        "push",
        "--porcelain",
        "--",
        session.target.url,
        f"{commit}:{session.branch}",
        remote=session.target,
        check=False,
        extra_env={
            "WIKI_NEW_OID": commit,
            "WIKI_DEST_REF": session.branch,
            "WIKI_OLD_OID": session.head,
        },
    )


def _publish(
    session,
    before,
    entries,
    desired,
    checkpoint,
    *,
    action,
    restore_modes=None,
    replay=False,
):
    tree = _tree(
        session.repo, session.head, before, entries, desired, restore_modes or {}
    )
    current_tree = _text(session.repo, "rev-parse", session.head + "^{tree}")
    revision = session.head
    status = "already-delivered" if replay else "unchanged"
    push_uncertain = False
    if tree != current_tree:
        revision = _oid(
            _git(
                session.repo,
                "commit-tree",
                tree,
                "-p",
                session.head,
                raw=("Reviewed wiki " + action + "\n").encode(),
            )
            .stdout.decode()
            .strip()
        )
        session.verify_target(session.head)
        session.verify_source()
        # Even an unsuccessful/ambiguous client exit can follow an accepted
        # receive-pack transaction. Never retry the push; inspect the remote.
        try:
            push_uncertain = _push(session, revision).returncode != 0
        except DeliveryError:
            push_uncertain = True
        status = action
    try:
        session.readback(revision, tree, desired)
    except DeliveryError as exc:
        if push_uncertain:
            raise DeliveryError(
                f"Push outcome unverified. Reconcile {session.branch} with proposed commit {revision} before retrying"
            ) from exc
        raise
    return {
        "status": status,
        "target_revision": revision,
        "source_revision": session.source_sha,
        "target_branch": session.branch.removeprefix("refs/heads/"),
        "target_tree": tree,
        "checkpoint": checkpoint,
        "readback_verified": True,
    }


def deliver(
    *,
    receipt,
    files,
    policy,
    source_repository,
    target_repository,
    source_remote,
    target_remote,
    source_ref=None,
    source_token=None,
    target_token=None,
):
    """Publish one already checked and accepted artifact, with a fresh remote proof."""
    if policy.get("publish") is not True:
        raise DeliveryError("Wiki delivery is disabled")
    with _session(
        policy=policy,
        source_repository=source_repository,
        target_repository=target_repository,
        source_remote=source_remote,
        target_remote=target_remote,
        source_ref=source_ref,
        source_revision=receipt["context"]["source_revision"],
        source_token=source_token,
        target_token=target_token,
    ) as session:
        before, entries = _read(session.repo, session.head)
        prior = _checkpoint(session.repo, session.head, before)
        session.check_high_water(prior)
        desired, checkpoint = plan_delivery(
            receipt,
            files,
            before,
            policy=policy,
            source_repository=source_repository,
            target_repository=target_repository,
            target_branch=session.branch.removeprefix("refs/heads/"),
            target_revision=session.head,
        )
        replay = prior is not None and prior["receipt_id"] == receipt["receipt_id"]
        if replay:
            _verify_replay(session, receipt["context"]["target_revision"])
        return _publish(
            session,
            before,
            entries,
            desired,
            checkpoint,
            action="delivered",
            replay=replay,
        )


def _verify_replay(session, base):
    parents = _text(session.repo, "show", "-s", "--format=%P", session.head).split()
    if parents != [_oid(base)]:
        raise DeliveryError(
            "Target moved beyond the exact delivered commit; reconcile before retrying"
        )


def qualify(
    *,
    policy,
    source_repository,
    target_repository,
    source_remote,
    target_remote,
    source_revision,
    source_ref=None,
    source_token=None,
    target_token=None,
):
    """Probe reachability of receive-pack without modifying the wiki or treating that as a write proof."""
    with _session(
        policy=policy,
        source_repository=source_repository,
        target_repository=target_repository,
        source_remote=source_remote,
        target_remote=target_remote,
        source_ref=source_ref,
        source_revision=source_revision,
        source_token=source_token,
        target_token=target_token,
    ) as s:
        before, _ = _read(s.repo, s.head)
        checkpoint = _checkpoint(s.repo, s.head, before)
        s.check_high_water(checkpoint)
        s.verify_source()
        s.verify_target(s.head)
        _git(
            s.repo,
            "push",
            "--dry-run",
            "--porcelain",
            "--",
            s.target.url,
            f"{s.head}:{s.branch}",
            remote=s.target,
        )
        s.verify_target(s.head)
        s.verify_source()
        return {
            "status": "reachable",
            "source_revision": s.source_sha,
            "target_branch": s.branch.removeprefix("refs/heads/"),
            "target_revision": s.head,
            "write_verified": False,
            "readback_verified": False,
        }


def _roll(
    *,
    policy,
    source_repository,
    target_repository,
    source_remote,
    target_remote,
    source_revision,
    target_revision,
    restore_revision,
    accepted_rollback_id,
    source_ref=None,
    source_token=None,
    target_token=None,
):
    if policy.get("publish") is not True:
        raise DeliveryError("Wiki delivery is disabled")
    base, restore = _oid(target_revision), _oid(restore_revision)
    with _session(
        policy=policy,
        source_repository=source_repository,
        target_repository=target_repository,
        source_remote=source_remote,
        target_remote=target_remote,
        source_ref=source_ref,
        source_revision=source_revision,
        source_token=source_token,
        target_token=target_token,
    ) as s:
        live, entries = _read(s.repo, s.head)
        checkpoint = _checkpoint(s.repo, s.head, live)
        s.check_high_water(checkpoint)
        replay = base != s.head
        before = live
        if replay:
            if (
                not accepted_rollback_id
                or not checkpoint
                or checkpoint["rollback_id"] != accepted_rollback_id
            ):
                raise DeliveryError("Rollback target revision is stale")
            _verify_replay(s, base)
            before, _ = _read(s.repo, base)
        if (
            restore == base
            or _git(
                s.repo, "merge-base", "--is-ancestor", restore, base, check=False
            ).returncode
        ):
            raise DeliveryError(
                "Rollback must reference an earlier commit in this wiki's history"
            )
        distance = int(
            _text(s.repo, "rev-list", "--first-parent", "--count", f"{restore}..{base}")
        )
        if _text(s.repo, "rev-parse", f"{base}~{distance}") != restore:
            raise DeliveryError(
                "Rollback must name an earlier state on the target branch's first-parent history"
            )
        historical, old_entries = _read(s.repo, restore)
        _checkpoint(s.repo, restore, historical)
        desired, plan = plan_rollback(
            before,
            historical,
            policy=policy,
            source_repository=source_repository,
            target_repository=target_repository,
            target_branch=s.branch.removeprefix("refs/heads/"),
            source_revision=s.source_sha,
            target_revision=base,
            restore_revision=restore,
        )
        if accepted_rollback_id is None:
            s.verify_target(base)
            s.verify_source()
            return plan
        if accepted_rollback_id != plan["rollback_id"]:
            raise DeliveryError(
                "Rollback approval differs from the exact current proposal"
            )
        _, next_checkpoint = split_delivery_tree(desired)
        if replay and desired != live:
            raise DeliveryError(
                "Rollback readback no longer matches the accepted rollback"
            )
        touched = {
            p for p in before.keys() | desired.keys() if before.get(p) != desired.get(p)
        }
        modes = {
            p: old_entries[p][0]
            for p in touched
            if p in old_entries and p != CHECKPOINT_PATH
        }
        return _publish(
            s,
            live,
            entries,
            desired,
            next_checkpoint,
            action="rolled-back",
            restore_modes=modes,
            replay=replay,
        )


def preview_rollback(**options):
    """Read the exact proposed restoration and its review ID without writing."""
    return _roll(**options, accepted_rollback_id=None)


def rollback(*, accepted_rollback_id, **options):
    """Publish a new forward commit restoring only the reviewed owned outputs."""
    if not isinstance(accepted_rollback_id, str) or not re.fullmatch(
        r"sha256:[0-9a-f]{64}", accepted_rollback_id
    ):
        raise DeliveryError("Rollback requires a separately accepted exact rollback ID")
    return _roll(**options, accepted_rollback_id=accepted_rollback_id)
