"""Tests for private runtime file writes."""

from pathlib import Path

from llm_wiki_cli.services import secure_file


def test_write_private_text_creates_parent_writes_text_and_restricts_permissions(
    tmp_path, monkeypatch
):
    chmod_calls = []

    def fake_chmod(path, mode):
        chmod_calls.append((Path(path), mode))

    monkeypatch.setattr(secure_file.os, "chmod", fake_chmod)

    path = tmp_path / "nested" / "prompt.txt"

    result = secure_file.write_private_text(str(path), "secret prompt")

    assert result == path
    assert path.read_text(encoding="utf-8") == "secret prompt"
    assert chmod_calls == [(path, 0o600)]


def test_write_private_text_uses_requested_encoding(tmp_path, monkeypatch):
    monkeypatch.setattr(secure_file.os, "chmod", lambda *_args: None)

    path = tmp_path / "prompt.txt"

    secure_file.write_private_text(path, "agent prompt", encoding="utf-16")

    assert path.read_text(encoding="utf-16") == "agent prompt"


def test_write_private_text_ignores_chmod_oserror(tmp_path, monkeypatch):
    chmod_calls = []

    def fail_chmod(path, mode):
        chmod_calls.append((Path(path), mode))
        raise OSError("chmod unsupported")

    monkeypatch.setattr(secure_file.os, "chmod", fail_chmod)

    path = tmp_path / "prompt.txt"

    result = secure_file.write_private_text(path, "prompt")

    assert result == path
    assert path.read_text(encoding="utf-8") == "prompt"
    assert chmod_calls == [(path, 0o600)]
