"""A distinct final-bundle reader never widens ordinary producer admission."""

from copy import deepcopy
import io
import stat
import zipfile

import pytest

from release import hosted_evidence as h, qualification_automation as qa


def zipped(files, compression=zipfile.ZIP_STORED):
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w", compression=compression) as archive:
        for name, raw in files.items():
            entry = zipfile.ZipInfo(name)
            # Preserve deliberately malformed headers even on Windows, where
            # construction rewrites separators and truncates embedded NULs.
            entry.filename = name
            archive.writestr(entry, raw, compress_type=compression)
    return stream.getvalue()


@pytest.mark.parametrize("name", ["a\\b", "a\0b"])
def test_zip_fixture_preserves_raw_names_before_inventory(monkeypatch, name):
    original = zipfile.ZipInfo.__init__

    def windows_name(info, filename="NoName", date_time=(1980, 1, 1, 0, 0, 0)):
        original(info, filename, date_time)
        info.filename = info.filename.replace("\\", "/")

    # Exercise Windows constructor normalization on every test host.
    monkeypatch.setattr(zipfile.ZipInfo, "__init__", windows_name)
    raw = zipped({name: b"owned"})
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        member, = archive.infolist()
        assert member.orig_filename == name
    with pytest.raises(h.EvidenceError, match="artifact member"):
        inventory(raw)


def binding(raw):
    run = {"id": 123, "run_attempt": 1, "head_sha": "a" * 40,
           "repository": {"id": 44, "full_name": "owner/project"},
           "head_repository": {"id": 44, "full_name": "owner/project"},
           "workflow_id": 90, "path": h.WORKFLOW, "name": "Release qualification",
           "event": "workflow_dispatch", "status": "completed", "conclusion": "success"}
    artifact = {"id": 321, "name": "qualified-release", "expired": False,
                "size_in_bytes": len(raw), "digest": "sha256:" + h.sha256(raw),
                "created_at": "2026-01-01T01:10:00Z", "updated_at": "2026-01-01T01:11:00Z",
                "workflow_run": {"id": 123, "head_sha": "a" * 40,
                                 "repository_id": 44, "head_repository_id": 44}}
    producer = {"id": 78, "name": "Assemble immutable qualified release",
                "run_id": 123, "run_attempt": 1, "head_sha": "a" * 40,
                "status": "completed", "conclusion": "success",
                "started_at": "2026-01-01T01:00:00Z", "completed_at": "2026-01-01T01:20:00Z"}
    return artifact, run, producer


def inventory(raw, values=None):
    artifact, run, producer = binding(raw) if values is None else values
    return h.qualified_bundle_inventory(raw, repository="owner/project",
                                        artifact=artifact, run=run, producer=producer)


def test_final_inventory_uses_existing_envelope_without_widening_generic_limit(monkeypatch):
    raw = zipped({"dist/wheel.whl": b"wheel", "dist/source.tar.gz": b"source"})
    ordinary = h.zip_inventory(raw)
    assert inventory(raw) == ordinary
    monkeypatch.setattr(h, "MAX_ARCHIVE", len(raw) - 1)
    with pytest.raises(h.EvidenceError, match="archive exceeds byte limit"):
        h.zip_inventory(raw)
    assert inventory(raw) == ordinary


def test_existing_global_limits_are_unchanged():
    assert h.MAX_ARCHIVE == 64 * 1024 * 1024
    assert h.MAX_EXPANDED == 256 * 1024 * 1024


def test_legacy_repository_spelling_and_workflow_ref_are_accepted():
    raw = zipped({"file": b"owned"})
    artifact, run, producer = binding(raw)
    run["repository"]["full_name"] = "Owner/Project"
    run["head_repository"]["full_name"] = "OWNER/PROJECT"
    run["path"] += "@refs/heads/main"
    assert inventory(raw, (artifact, run, producer)) == {"file": h.sha256(b"owned")}


def test_final_transport_boundary_reuses_existing_expanded_envelope():
    artifact, run, producer = binding(zipped({"file": b"owned"}))
    artifact["size_in_bytes"] = h.MAX_EXPANDED
    assert h.qualified_bundle_metadata("owner/project", artifact, run, producer) == h.MAX_EXPANDED
    artifact["size_in_bytes"] += 1
    with pytest.raises(h.EvidenceError, match="transport byte limit"):
        h.qualified_bundle_metadata("owner/project", artifact, run, producer)


@pytest.mark.parametrize("target,path,value", [
    ("artifact", "id", True), ("artifact", "name", "candidate-source"),
    ("artifact", "expired", True), ("artifact", "size_in_bytes", None),
    ("artifact", "size_in_bytes", True), ("artifact", "size_in_bytes", 0),
    ("artifact", "size_in_bytes", -1), ("artifact", "size_in_bytes", 256 * 1024 * 1024 + 1),
    ("artifact", "digest", "missing"), ("artifact", "workflow_run.id", 124),
    ("artifact", "workflow_run.head_sha", "b" * 40),
    ("artifact", "workflow_run.repository_id", 45),
    ("artifact", "workflow_run.head_repository_id", 45),
    ("run", "id", False), ("run", "run_attempt", 0), ("run", "workflow_id", True),
    ("run", "path", ".github/workflows/ci.yml"), ("run", "name", "CI"),
    ("run", "event", "push"), ("run", "status", "in_progress"),
    ("run", "conclusion", "cancelled"), ("run", "repository.full_name", "foreign/repo"),
    ("run", "head_repository.id", 45), ("producer", "id", False),
    ("producer", "run_id", 124), ("producer", "run_attempt", 2),
    ("producer", "head_sha", "b" * 40), ("producer", "conclusion", "failure"),
    ("producer", "status", "queued"), ("producer", "name", "Other producer"),
    ("producer", "completed_at", "2026-01-01T01:09:00Z"),
    ("artifact", "updated_at", "2026-01-01T01:21:00Z"),
    ("artifact", "created_at", "invalid"),
])
def test_wrong_binding_refuses_before_transport(monkeypatch, target, path, value):
    raw = zipped({"file": b"owned"})
    artifact, run, producer = deepcopy(binding(raw))
    node = {"artifact": artifact, "run": run, "producer": producer}[target]
    keys = path.split(".")
    for name in keys[:-1]:
        node = node[name]
    node[keys[-1]] = value
    monkeypatch.setenv("GITHUB_TOKEN", "fixture-secret")
    monkeypatch.setattr(h, "_http", lambda *a: pytest.fail("invalid metadata downloaded"))
    with pytest.raises(h.EvidenceError):
        h.GitHub("owner/project").qualified_bundle_archive(artifact, run, producer)


@pytest.mark.parametrize("difference", [-1, 1])
def test_exact_transport_length_is_checked(monkeypatch, difference):
    raw = zipped({"file": b"owned"})
    artifact, run, producer = binding(raw)
    artifact["size_in_bytes"] += difference
    monkeypatch.setenv("GITHUB_TOKEN", "fixture-secret")
    monkeypatch.setattr(h, "_http", lambda url, token, limit: (200, {}, raw))
    with pytest.raises(h.EvidenceError, match="length differs"):
        h.GitHub("owner/project").qualified_bundle_archive(artifact, run, producer)


@pytest.mark.parametrize("typed", [False, True])
def test_http_never_reads_past_the_selected_transport_budget(monkeypatch, typed):
    raw = zipped({"file": b"owned"})
    maximum = len(raw) if typed else 8
    reads = []

    class Response:
        status = 200
        headers = {}

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return None

        def read(self, count):
            reads.append(count)
            return b"x" * count

    class Opener:
        def open(self, request, timeout):
            return Response()

    monkeypatch.setenv("GITHUB_TOKEN", "fixture-secret")
    monkeypatch.setattr(h, "MAX_ARCHIVE", 8)
    monkeypatch.setattr(h.urllib.request, "build_opener", lambda *a: Opener())
    client = h.GitHub("owner/project")
    with pytest.raises(h.EvidenceError, match="response exceeds byte limit"):
        if typed:
            client.qualified_bundle_archive(*binding(raw))
        else:
            client.archive(321)
    assert reads == [maximum + 1]


def test_transport_digest_is_checked_before_zip_parse(monkeypatch):
    raw = zipped({"file": b"owned"})
    artifact, run, producer = binding(raw)
    artifact["digest"] = "sha256:" + "0" * 64
    monkeypatch.setattr(h.zipfile, "ZipFile", lambda *a: pytest.fail("corrupt transport parsed"))
    with pytest.raises(h.EvidenceError, match="archive digest differs"):
        inventory(raw, (artifact, run, producer))


def test_typed_download_redirect_is_exactly_bounded_and_drops_credentials(monkeypatch):
    raw = zipped({"file": b"owned"})
    values = binding(raw)
    calls = []

    def request(url, token, limit):
        calls.append((url, token, limit))
        return (302, {"Location": "https://signed.invalid/archive"}, b"") if len(calls) == 1 else (200, {}, raw)

    monkeypatch.setattr(qa.hosted, "_http", request)
    client = qa.GitHubClient("owner/project", "fixture-secret")
    assert client.qualified_bundle_archive(*values) == raw
    assert [row[1] for row in calls] == ["fixture-secret", None]
    assert [row[2] for row in calls] == [len(raw), len(raw)]
    assert inventory(raw) == {"file": h.sha256(b"owned")}


def test_typed_redirect_count_is_unchanged(monkeypatch):
    raw = zipped({"file": b"owned"})
    calls = []

    def loop(url, token, limit):
        calls.append(token)
        return 302, {"Location": "https://signed.invalid/loop"}, b""

    monkeypatch.setenv("GITHUB_TOKEN", "fixture-secret")
    monkeypatch.setattr(h, "_http", loop)
    with pytest.raises(h.EvidenceError, match="redirect bound"):
        h.GitHub("owner/project").qualified_bundle_archive(*binding(raw))
    assert calls == ["fixture-secret", None, None, None, None]


@pytest.mark.parametrize("name", ["../escape", "/absolute", "C:/drive", "a\\b", "a\0b", "a//b", "."])
def test_typed_inventory_keeps_canonical_path_guards(name):
    with pytest.raises(h.EvidenceError, match="artifact member"):
        inventory(zipped({name: b"owned"}))


@pytest.mark.parametrize("mode", [stat.S_IFLNK, stat.S_IFIFO, stat.S_IFSOCK, stat.S_IFDIR])
def test_nonregular_zip_members_are_refused(mode):
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w") as archive:
        entry = zipfile.ZipInfo("file")
        entry.external_attr = (mode | 0o600) << 16
        archive.writestr(entry, b"owned")
    with pytest.raises(h.EvidenceError):
        inventory(stream.getvalue())


@pytest.mark.parametrize("files", [{"File": b"a", "file": b"b"}, {"dir": b"a", "dir/file": b"b"}])
def test_portable_collisions_refuse_before_extraction(files):
    with pytest.raises(h.EvidenceError):
        inventory(zipped(files))


def test_expanded_budget_is_unchanged(monkeypatch):
    raw = zipped({"file": b"a" * 1024}, zipfile.ZIP_DEFLATED)
    assert len(raw) < 512
    monkeypatch.setattr(h, "MAX_EXPANDED", 512)
    with pytest.raises(h.EvidenceError, match="expansion bound"):
        inventory(raw)


def test_member_budget_is_unchanged():
    raw = zipped({str(i): b"" for i in range(10_001)})
    with pytest.raises(h.EvidenceError, match="expansion bound"):
        inventory(raw)
