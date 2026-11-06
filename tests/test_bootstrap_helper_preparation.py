"""Helper setup failures never begin an interrupted wiki publication."""

from contextlib import contextmanager
import errno
from pathlib import Path

import pytest

from llm_wiki_cli import api
from llm_wiki_cli.services import bootstrap_recovery as recovery
from llm_wiki_cli.services import helper_cache
from llm_wiki_cli.services import knowledge_governance as governance
from llm_wiki_cli.services.helper_runtime import PreparedHelperHandle
from llm_wiki_cli.services.wiki_write_basis import ACTIVE_BOOTSTRAP_JOURNAL


@pytest.fixture
def target(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    source = tmp_path / "src"
    source.mkdir()
    (source / "main.ts").write_text("export function value() { return 1; }\n")
    return source, tmp_path / "wiki"


@pytest.mark.parametrize("cancelled", [False, True], ids=["setup-failed", "cancelled"])
def test_helper_failure_precedes_journal_and_retry_needs_no_recovery(target, monkeypatch, cancelled):
    source, wiki = target
    acquired = set()
    attempts = []

    def tracked_lock(name, original):
        @contextmanager
        def lock(root):
            with original(root):
                acquired.add(name)
                try:
                    yield
                finally:
                    acquired.remove(name)
        return lock

    for name in ("governance_writer_lock", "storage_writer_lock"):
        monkeypatch.setattr(recovery, name, tracked_lock(name, getattr(recovery, name)))

    def fail(language, *args, **kwargs):
        attempts.append(language)
        assert acquired == {"governance_writer_lock", "storage_writer_lock"}
        assert ACTIVE_BOOTSTRAP_JOURNAL.get() is None
        assert not recovery._record_path(wiki).exists()
        if cancelled:
            raise KeyboardInterrupt("cancelled helper setup")
        raise helper_cache.HelperPreparationError(language, "controlled missing runtime")

    monkeypatch.setattr(helper_cache, "ensure_helper", fail)
    expected = KeyboardInterrupt if cancelled else api.WorkspaceStateError
    with pytest.raises(expected, match="cancelled helper setup|controlled missing runtime"):
        api.bootstrap_wiki(str(source), str(wiki))
    assert attempts == ["typescript"]
    assert not recovery.pending_bootstrap(wiki)
    assert not recovery._record_path(wiki).exists()
    assert {path.name for path in wiki.iterdir()} == recovery.LOCK_FILES

    # The target remains pristine: a later valid bootstrap takes its normal
    # first-use route, rather than recovering a never-started publication.
    (source / "main.ts").unlink()
    (source / "main.py").write_text("class Item:\n    pass\n")
    api.bootstrap_wiki(str(source), str(wiki))
    assert not recovery.pending_bootstrap(wiki)
    assert (wiki / "modules/main.md").is_file()


@pytest.mark.parametrize("invalid", ["existing-wiki", "source-selection", "governance"])
def test_validation_precedes_helper_setup_and_journal(target, monkeypatch, invalid):
    source, wiki = target
    kwargs = {}
    if invalid == "existing-wiki":
        wiki.mkdir()
        (wiki / "authored.md").write_text("User-authored page.\n")
    elif invalid == "source-selection":
        selection = source / "selection.json"
        selection.write_text('{"schema_version": "invalid"}\n')
        kwargs["source_selection"] = str(selection)
    else:
        # Governance validation also runs before helper preparation for a
        # pristine target with control metadata.
        monkeypatch.setattr(
            governance, "load_governance",
            lambda *args, **kwargs: (_ for _ in ()).throw(
                governance.GovernanceError("ledger", "controlled invalid governance")
            ),
        )
        from llm_wiki_cli.services import bootstrap_runtime
        monkeypatch.setattr(bootstrap_runtime, "load_governance", governance.load_governance)
    monkeypatch.setattr(helper_cache, "ensure_helper", lambda *a, **k: pytest.fail("invalid bootstrap prepared a helper"))
    with pytest.raises(api.LlmWikiApiError):
        api.bootstrap_wiki(str(source), str(wiki), **kwargs)
    assert not recovery.pending_bootstrap(wiki)
    assert not recovery._record_path(wiki).exists()


@pytest.mark.parametrize("filename", sorted(recovery.LOCK_FILES))
def test_writer_lock_denial_precedes_helper_setup(target, monkeypatch, filename):
    source, wiki = target
    original = governance.os.open

    def denied(path, flags, *args, **kwargs):
        if Path(path).name == filename:
            raise PermissionError(errno.EACCES, "controlled lock denial", str(path))
        return original(path, flags, *args, **kwargs)

    monkeypatch.setattr(governance.os, "open", denied)
    monkeypatch.setattr(helper_cache, "ensure_helper", lambda *a, **k: pytest.fail("unlocked bootstrap prepared a helper"))
    with pytest.raises(api.LlmWikiApiError, match="lock-open-failed"):
        api.bootstrap_wiki(str(source), str(wiki))
    assert not recovery.pending_bootstrap(wiki)
    assert not recovery._record_path(wiki).exists()


def test_content_added_during_helper_setup_is_not_adopted_as_first_use(target, monkeypatch):
    source, wiki = target
    authored = wiki / "authored.md"
    content = "A user added this page while helper setup was running.\n"

    def prepare(language, *args, **kwargs):
        authored.write_text(content)
        cache_root = source.parent / "helper-cache"
        root = cache_root / language / ("a" * 64)
        return PreparedHelperHandle(language, cache_root, "a" * 64, root, root / "artifact", {})

    monkeypatch.setattr(helper_cache, "ensure_helper", prepare)
    with pytest.raises(api.WorkspaceStateError, match="Existing wiki content"):
        api.bootstrap_wiki(str(source), str(wiki))
    assert authored.read_text() == content
    assert not recovery.pending_bootstrap(wiki)
    assert not recovery._record_path(wiki).exists()
