"""Tests for deterministic release artifact construction."""

from __future__ import annotations

import gzip
import hashlib
import io
import tarfile
from pathlib import Path

import pytest

import release_build_backend


def _write_sdist(
    path: Path,
    *,
    gzip_mtime: int,
    member_mtime: int,
    reverse: bool,
) -> None:
    members = [
        ("agent_wiki_cli-1.5.0/", None, 0o700),
        ("agent_wiki_cli-1.5.0/README.md", b"# agent-wiki\n", 0o600),
        ("agent_wiki_cli-1.5.0/bin/helper", b"#!/bin/sh\n", 0o711),
    ]
    if reverse:
        members.reverse()
    with path.open("wb") as raw:
        with gzip.GzipFile(
            filename="input-name.tar",
            fileobj=raw,
            mode="wb",
            mtime=gzip_mtime,
        ) as compressed:
            with tarfile.open(fileobj=compressed, mode="w") as archive:
                for name, payload, mode in members:
                    member = tarfile.TarInfo(name)
                    member.mtime = member_mtime
                    member.uid = 501
                    member.gid = 20
                    member.uname = "developer"
                    member.gname = "staff"
                    member.mode = mode
                    if payload is None:
                        member.type = tarfile.DIRTYPE
                        archive.addfile(member)
                    else:
                        member.size = len(payload)
                        archive.addfile(member, io.BytesIO(payload))


def test_sdist_normalization_is_byte_reproducible(tmp_path, monkeypatch):
    first = tmp_path / "first.tar.gz"
    second = tmp_path / "second.tar.gz"
    _write_sdist(first, gzip_mtime=11, member_mtime=22, reverse=False)
    _write_sdist(second, gzip_mtime=33, member_mtime=44, reverse=True)
    monkeypatch.setenv("SOURCE_DATE_EPOCH", "946684800")

    release_build_backend._normalize_sdist(first)
    release_build_backend._normalize_sdist(second)

    assert hashlib.sha256(first.read_bytes()).digest() == hashlib.sha256(
        second.read_bytes()
    ).digest()
    with tarfile.open(first, mode="r:gz") as archive:
        members = archive.getmembers()
    assert [member.name for member in members] == sorted(
        member.name for member in members
    )
    assert {member.mtime for member in members} == {946684800}
    assert {(member.uid, member.gid) for member in members} == {(0, 0)}
    assert {(member.uname, member.gname) for member in members} == {("root", "root")}
    assert members[0].mode == 0o755
    assert next(member for member in members if member.name.endswith("README.md")).mode == (
        0o644
    )
    assert next(member for member in members if member.name.endswith("helper")).mode == (
        0o755
    )


@pytest.mark.parametrize("value", ["not-a-number", "-1", "4294967296"])
def test_sdist_normalization_rejects_invalid_source_date_epoch(
    tmp_path, monkeypatch, value
):
    archive = tmp_path / "input.tar.gz"
    _write_sdist(archive, gzip_mtime=1, member_mtime=2, reverse=False)
    monkeypatch.setenv("SOURCE_DATE_EPOCH", value)

    with pytest.raises(ValueError, match="SOURCE_DATE_EPOCH"):
        release_build_backend._normalize_sdist(archive)
