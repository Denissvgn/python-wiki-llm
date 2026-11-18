"""Independent file images, source-affine roots and retained failed fixture state."""

import os

import pytest

from tests.prepared_workspaces import Pool, _snapshot


def pool(tmp_path, *, enabled=True):
    root = tmp_path / "pool"
    root.mkdir()
    return Pool(root, enabled=enabled)


def build(root):
    (root / "source").mkdir()
    (root / "source/input.py").write_bytes(b"VALUE = 1\r\n")
    (root / "empty").mkdir()
    (root / "control.json").write_bytes(str(root).encode())
    return {"limit": 123, "nested": [1]}


def test_reuse_retains_exact_absolute_source_and_fresh_isolated_files(tmp_path):
    store = pool(tmp_path)
    first = store.reserve("input/v1")
    root = first.populate(build)
    image = _snapshot(root)
    # Retain a distinct link so the filesystem cannot reuse the old file ID.
    sentinel = tmp_path / "sentinel.py"
    os.link(root / "source/input.py", sentinel)
    (root / "extra").write_text("foreign test output")
    (root / "source/input.py").write_bytes(b"case-local mutation")
    first.active = False
    second = store.reserve("input/v1")
    assert second.root == root
    second.populate(lambda _: pytest.fail("prepared input rebuilt"))
    assert _snapshot(root) == image
    assert sentinel.read_bytes() == b"case-local mutation"
    assert not (root / "source/input.py").samefile(sentinel)
    assert store.builds == {"input/v1": 1} and store.restores == {"input/v1": 1}


def test_metadata_is_not_shared_mutable_state(tmp_path):
    store = pool(tmp_path)
    lease = store.reserve("input")
    lease.populate(build)
    metadata = lease.metadata
    metadata["nested"].append(2)
    assert lease.metadata == {"limit": 123, "nested": [1]}


def test_disabled_reuse_always_runs_real_builder(tmp_path):
    store = pool(tmp_path, enabled=False)
    for _ in range(2):
        lease = store.reserve("input")
        lease.populate(build)
        lease.active = False
    assert store.builds == {"input": 2} and not store.images and not store.restores


def test_active_or_occupied_lease_cannot_be_replaced(tmp_path):
    store = pool(tmp_path)
    lease = store.reserve("input")
    lease.populate(build)
    with pytest.raises(ValueError, match="still owns"):
        store.reserve("input")
    with pytest.raises(ValueError, match="occupied"):
        lease.populate(build)
    assert (lease.root / "source/input.py").read_bytes() == b"VALUE = 1\r\n"


def test_failed_case_is_preserved_before_the_next_test_reuses_the_root(tmp_path):
    store = pool(tmp_path)
    lease = store.reserve("input", failed=lambda: True)
    lease.populate(build)
    (lease.root / "control.json").write_bytes(b"failure evidence")
    lease.active = False
    following = store.reserve("input")
    following.populate(build)
    assert (store.failures[0] / "control.json").read_bytes() == b"failure evidence"
    assert (following.root / "control.json").read_bytes() == str(
        following.root
    ).encode()


def test_variants_cannot_borrow_each_others_namespace(tmp_path):
    store = pool(tmp_path)
    left, right = store.reserve("full"), store.reserve("inventory")
    left.populate(build)
    right.populate(build)
    assert left.root != right.root
    assert (left.root / "control.json").read_bytes() != (
        right.root / "control.json"
    ).read_bytes()


@pytest.mark.parametrize("kind", ["symbolic", "hard"])
def test_redirected_or_shared_builder_files_never_enter_a_template(tmp_path, kind):
    store = pool(tmp_path)
    original = tmp_path / "outside"
    original.write_bytes(b"preserve")

    def unsafe(root):
        if kind == "symbolic":
            (root / "link").symlink_to(original)
        else:
            os.link(original, root / "link")

    lease = store.reserve("unsafe")
    with pytest.raises(ValueError):
        lease.populate(unsafe)
    assert not store.images and original.read_bytes() == b"preserve"


def test_rebound_root_is_not_followed_or_removed(tmp_path):
    import shutil

    store = pool(tmp_path)
    lease = store.reserve("input")
    lease.populate(build)
    lease.active = False
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "preserve").write_bytes(b"unrelated")
    shutil.rmtree(lease.root)
    lease.root.symlink_to(outside, target_is_directory=True)
    with pytest.raises(ValueError, match="redirected"):
        store.reserve("input")
    assert (outside / "preserve").read_bytes() == b"unrelated"


def test_rebound_root_is_rejected_before_populating_a_template(tmp_path):
    store = pool(tmp_path)
    lease = store.reserve("input")
    lease.root.rmdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    lease.root.symlink_to(outside, target_is_directory=True)
    with pytest.raises(ValueError, match="redirected"):
        lease.populate(build)
    assert not list(outside.iterdir())


@pytest.mark.parametrize("owner", [True, False])
def test_nested_pytest_cannot_publish_into_its_parents_fixture_report(tmp_path, owner):
    import json
    import subprocess
    import sys
    from pathlib import Path

    root = Path(__file__).parents[1]
    project = tmp_path / "project"
    project.mkdir()
    (project / "conftest.py").write_text(
        'pytest_plugins = ["tests.prepared_workspaces"]\n'
    )
    (project / "test_probe.py").write_text("def test_actual_probe(): assert True\n")
    report = tmp_path / "workspace-profile.json"
    if not owner:
        report.write_bytes(b"parent evidence")
    script = 'import os,sys;sys.path.insert(0,sys.argv[1]);import pytest;os.environ["LLM_WIKI_TEST_PREPARED_REPORT_PID"]=str(os.getpid()) if sys.argv[3]=="owner" else "another-process";raise SystemExit(pytest.main([sys.argv[2],"-q","-p","no:cacheprovider"]))'
    process = subprocess.run(
        [
            sys.executable,
            "-I",
            "-c",
            script,
            str(root),
            str(project),
            "owner" if owner else "child",
        ],
        env={
            **os.environ,
            "LLM_WIKI_TEST_PREPARED_WORKSPACES": "0",
            "LLM_WIKI_TEST_PREPARED_WORKSPACE_REPORT": str(report),
        },
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert process.returncode == 0, process.stdout + process.stderr
    if owner:
        value = json.loads(report.read_bytes())
        assert value["enabled"] is False and value["shared_mutable_files"] is False
    else:
        assert report.read_bytes() == b"parent evidence"
