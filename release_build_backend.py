"""Setuptools build backend with deterministic source-distribution metadata."""

from __future__ import annotations

import copy
import gzip
import os
import tarfile
import tempfile
from pathlib import Path
from typing import Any, BinaryIO, cast

from setuptools import build_meta as _setuptools


def _source_date_epoch() -> int:
    raw_value = os.environ.get("SOURCE_DATE_EPOCH", "0")
    try:
        epoch = int(raw_value)
    except ValueError as exc:
        raise ValueError("SOURCE_DATE_EPOCH must be a non-negative integer") from exc
    if not 0 <= epoch <= 0xFFFFFFFF:
        raise ValueError("SOURCE_DATE_EPOCH must fit in an unsigned 32-bit timestamp")
    return epoch


def _normalized_member(member: tarfile.TarInfo, *, epoch: int) -> tarfile.TarInfo:
    normalized = copy.copy(member)
    normalized.uid = 0
    normalized.gid = 0
    normalized.uname = "root"
    normalized.gname = "root"
    normalized.mtime = epoch
    normalized.pax_headers = {}
    if normalized.isdir():
        normalized.mode = 0o755
    elif normalized.isfile():
        normalized.mode = 0o755 if member.mode & 0o111 else 0o644
    else:
        normalized.mode = 0o755
    return normalized


def _member_payload(
    archive: tarfile.TarFile, member: tarfile.TarInfo
) -> bytes | None:
    if not member.isfile():
        return None
    extracted = archive.extractfile(member)
    if extracted is None:
        raise ValueError(f"sdist member could not be read: {member.name}")
    return extracted.read()


def _write_normalized_tar(
    output: BinaryIO,
    members: list[tuple[tarfile.TarInfo, bytes | None]],
    *,
    epoch: int,
) -> None:
    with gzip.GzipFile(
        filename="",
        fileobj=output,
        mode="wb",
        compresslevel=9,
        mtime=epoch,
    ) as compressed:
        with tarfile.open(
            fileobj=compressed,
            mode="w",
            format=tarfile.PAX_FORMAT,
        ) as normalized_archive:
            for member, payload in sorted(members, key=lambda item: item[0].name):
                normalized = _normalized_member(member, epoch=epoch)
                if payload is None:
                    normalized_archive.addfile(normalized)
                    continue
                normalized.size = len(payload)
                with tempfile.SpooledTemporaryFile() as source:
                    source.write(payload)
                    source.seek(0)
                    normalized_archive.addfile(normalized, source)


def _normalize_sdist(path: Path) -> None:
    epoch = _source_date_epoch()
    with tarfile.open(path, mode="r:gz") as source:
        members = [
            (member, _member_payload(source, member))
            for member in source.getmembers()
        ]

    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as output:
            temporary = Path(output.name)
            _write_normalized_tar(cast(BinaryIO, output), members, epoch=epoch)
        os.replace(temporary, path)
        temporary = None
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def build_sdist(
    sdist_directory: str,
    config_settings: dict[str, Any] | None = None,
) -> str:
    filename = _setuptools.build_sdist(sdist_directory, config_settings)
    _normalize_sdist(Path(sdist_directory) / filename)
    return filename


build_wheel = _setuptools.build_wheel
build_editable = _setuptools.build_editable
get_requires_for_build_sdist = _setuptools.get_requires_for_build_sdist
get_requires_for_build_wheel = _setuptools.get_requires_for_build_wheel
get_requires_for_build_editable = _setuptools.get_requires_for_build_editable
prepare_metadata_for_build_wheel = _setuptools.prepare_metadata_for_build_wheel
prepare_metadata_for_build_editable = _setuptools.prepare_metadata_for_build_editable
