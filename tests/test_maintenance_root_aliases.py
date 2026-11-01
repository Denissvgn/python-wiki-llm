"""Canonical root comparisons retain adoption and recovery path boundaries."""

from pathlib import PureWindowsPath
from types import SimpleNamespace

import pytest

from llm_wiki_cli.services import maintenance_service as service
from llm_wiki_cli.services.maintenance_protocol import MaintenanceProtocolError


class AliasedRoot(PureWindowsPath):
    def resolve(self):
        return PureWindowsPath(*(part.replace("RUNNER~1", "runneradmin") for part in self.parts))


@pytest.mark.parametrize("alias_location", ["capture", "target", "both"])
def test_adoption_accepts_equivalent_source_and_wiki_spellings(alias_location):
    capture_user = "RUNNER~1" if alias_location in {"capture", "both"} else "runneradmin"
    target_user = "RUNNER~1" if alias_location in {"target", "both"} else "runneradmin"
    captured = SimpleNamespace(
        source_snapshot=SimpleNamespace(root=AliasedRoot(f"C:/Users/{capture_user}/src")),
        wiki_root=AliasedRoot(f"C:/Users/{capture_user}/wiki"),
    )
    service._validate_capture_roots(captured, AliasedRoot(f"C:/Users/{target_user}/src"),
                                    AliasedRoot(f"C:/Users/{target_user}/wiki"))


@pytest.mark.parametrize("wrong_root", ["source", "wiki"])
def test_adoption_rejects_a_different_root_even_with_aliases(wrong_root):
    captured = SimpleNamespace(
        source_snapshot=SimpleNamespace(root=AliasedRoot("C:/Users/runneradmin/src")),
        wiki_root=AliasedRoot("C:/Users/runneradmin/wiki"),
    )
    if wrong_root == "source":
        captured.source_snapshot.root = AliasedRoot("C:/other/src")
    else:
        captured.wiki_root = AliasedRoot("C:/other/wiki")
    with pytest.raises(MaintenanceProtocolError) as error:
        service._validate_capture_roots(captured, AliasedRoot("C:/Users/RUNNER~1/src"),
                                        AliasedRoot("C:/Users/RUNNER~1/wiki"))
    assert error.value.reason == wrong_root + "-mismatch"


@pytest.mark.parametrize("directory", ["wiki", "wiki/recovery", "", "src", "src/recovery"])
def test_recovery_rejects_aliased_wiki_source_and_ancestor_paths(monkeypatch, directory):
    monkeypatch.setattr(service, "_absolute_path", lambda path: path)
    with pytest.raises(MaintenanceProtocolError) as error:
        service._outside_recovery(AliasedRoot("C:/Users/RUNNER~1") / directory,
                                  AliasedRoot("C:/Users/runneradmin/wiki"),
                                  AliasedRoot("C:/Users/runneradmin/src"))
    assert error.value.reason == "recovery-path"


def test_external_recovery_retains_its_guarded_absolute_spelling(monkeypatch):
    monkeypatch.setattr(service, "_absolute_path", lambda path: path)
    recovery = AliasedRoot("C:/Users/RUNNER~1/recovery")
    assert service._outside_recovery(recovery, AliasedRoot("C:/Users/runneradmin/wiki"),
                                     AliasedRoot("C:/Users/runneradmin/src")) is recovery
