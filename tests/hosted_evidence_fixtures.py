"""Owned GitHub metadata and artifact ZIPs for provenance boundary controls."""

from copy import deepcopy
import io
from pathlib import Path
import tarfile
import zipfile

from release import hosted_evidence as hosted


def source_archive(files):
    """Build deterministic frozen-source bytes, including real TAR headers."""
    stream = io.BytesIO()
    with tarfile.open(fileobj=stream, mode="w", format=tarfile.PAX_FORMAT) as archive:
        for name, data in sorted(files.items()):
            member = tarfile.TarInfo(name)
            member.size = len(data)
            archive.addfile(member, io.BytesIO(data))
    return stream.getvalue()


class HostedEvidence:
    def __init__(
        self, identity, run_id, source, layout="legacy", core_layout="unsharded", maintenance=False
    ):
        self.identity = identity
        self.run_id = run_id
        self.layout = layout
        self.core_layout = core_layout
        self.run = {
            "id": run_id,
            "run_attempt": 1,
            "head_sha": identity["source"]["sha"],
            "event": "workflow_dispatch",
            "path": hosted.WORKFLOW,
            "status": "completed",
            "conclusion": "success",
            "repository": {"id": 10, "full_name": identity["repository"]},
            "head_repository": {"id": 10, "full_name": identity["repository"]},
        }
        contract = hosted.artifact_contract(layout, core_layout)
        if maintenance:
            contract["RD-10:maintenance"] = (
                "knowledge-maintenance-verification", "Repository knowledge maintenance", ("verification.json",),
            )
        self.contract = contract
        self.jobs = [
            {
                "id": number,
                "run_id": run_id,
                "run_attempt": 1,
                "head_sha": identity["source"]["sha"],
                "name": name,
                "status": "completed",
                "conclusion": "success",
                "started_at": "2026-09-22T10:00:00Z",
                "completed_at": "2026-09-22T10:10:00Z",
            }
            for number, name in enumerate(
                sorted({row[1] for row in contract.values()} | hosted.REQUIRED_JOBS), 1
            )
        ]
        self.artifacts = []
        self.archives = {}
        self.files = {}
        for number, (binding, (name, _job, required)) in enumerate(
            sorted(contract.items()), 100
        ):
            files = {filename: self.file_bytes(filename) for filename in required}
            files["producer-diagnostic.json"] = b'{"owned":true}\n'
            if name == "evidence-rd-07":
                # govulncheck -json writes multiple top-level JSON records.
                files["govulncheck.json"] = (
                    b'{"config":{"protocol_version":"v1.0.0"}}\n'
                    b'{"progress":{"message":"owned diagnostic"}}\n'
                )
            if name == "candidate-source":
                files = {p.name: p.read_bytes() for p in source.iterdir()}
            if name == "qualification-harnesses":
                files = {"qualification-harnesses.tar": b"owned frozen harness"}
            raw = self.zip(files)
            self.files[binding] = files
            self.archives[number] = raw
            self.artifacts.append(
                {
                    "id": number,
                    "name": name,
                    "digest": "sha256:" + hosted.sha256(raw),
                    "expired": False,
                    "created_at": "2026-09-22T10:05:00Z",
                    "updated_at": "2026-09-22T10:05:00Z",
                    "workflow_run": {
                        "id": run_id,
                        "head_sha": identity["source"]["sha"],
                        "repository_id": 10,
                        "head_repository_id": 10,
                    },
                }
            )
        self.context = {
            "suite_layout": layout,
            "run_attempt": 1,
            "harness_sha256": hosted.sha256(b"owned frozen harness"),
        }
        if core_layout != "unsharded":
            self.context["core_layout"] = core_layout

    @staticmethod
    def file_bytes(name):
        if name.startswith("coverage-"):
            return b'<coverage line-rate="1.0" />'
        if name.endswith(".xml"):
            return b'<testsuite><testcase classname="tests.test_owned" name="test_owned" /></testsuite>'
        return b'{"owned":true}\n'

    @staticmethod
    def zip(files):
        stream = io.BytesIO()
        with zipfile.ZipFile(stream, "w", zipfile.ZIP_DEFLATED) as archive:
            for name, data in sorted(files.items()):
                member = zipfile.ZipInfo(name)
                # Preserve adversarial header names on every host. ZipInfo's
                # constructor otherwise rewrites Windows separators and NULs.
                member.filename = name
                archive.writestr(member, data, compress_type=zipfile.ZIP_DEFLATED)
        return stream.getvalue()

    def specs(self, root):
        specs = []
        for binding, files in self.files.items():
            directory = root / binding.replace(":", "/")
            directory.mkdir(parents=True)
            for name, raw in files.items():
                path = directory / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(raw)
            specs.append(f"{binding}={directory}")
        return specs

    def replace_files(self, binding, files):
        self.files[binding] = files
        name = self.contract[binding][0]
        artifact = next(row for row in self.artifacts if row["name"] == name)
        raw = self.zip(files)
        self.archives[artifact["id"]] = raw
        artifact["digest"] = "sha256:" + hosted.sha256(raw)

    def client(self, repository):
        assert repository == self.identity["repository"]
        return self

    def get(self, path):
        assert path == f"/actions/runs/{self.run_id}"
        return deepcopy(self.run)

    def list(self, path, key):
        assert path in {
            f"/actions/runs/{self.run_id}/artifacts",
            f"/actions/runs/{self.run_id}/attempts/1/jobs",
        }
        return deepcopy(self.jobs if key == "jobs" else self.artifacts)

    def archive(self, artifact_id):
        return self.archives[artifact_id]


def qualifying_union(directory, identity, harness):
    import xml.etree.ElementTree as ET
    from release import ubuntu_suites as suites, qualification as q

    directory.mkdir(parents=True)
    registry_path = Path(suites.__file__).with_name("ubuntu-suites.json")
    registry = suites.registry(registry_path)
    nodes = set()
    for selectors in registry["gates"].values():
        for selector in selectors:
            node = selector.replace("*", "owned").replace("?", "x")
            nodes.add(node if "::" in node else node + "::test_owned")
    inventory = suites.resolve(sorted(nodes), registry)
    q.write_json(directory / "identity.json", identity)
    q.write_json(directory / "registry.json", registry)
    for name in ["inventory.json", "observed.json"]:
        q.write_json(directory / name, inventory)
    q.write_json(directory / "started.json", inventory["union"])
    xml = ET.Element("testsuite")
    for node in inventory["union"]:
        file, *names = node.split("::")
        classname = file[:-3].replace("/", ".")
        if len(names) > 1:
            classname += "." + ".".join(names[:-1])
        ET.SubElement(xml, "testcase", classname=classname, name=names[-1])
    ET.ElementTree(xml).write(directory / "union.xml", encoding="utf-8")
    execution = {
        "schema_version": suites.SCHEMA,
        "mode": "union",
        "purpose": "qualification",
        "complete": True,
        "identity": identity,
        "identity_sha256": q.sha256_file(directory / "identity.json"),
        "harness_sha256": harness,
        "registry_sha256": q.sha256_file(registry_path),
        "environment": {
            "profile": suites.PROFILE,
            "python": "3.13.15",
            "machine": "x86_64",
            "runner_image": "owned-runner",
            "packages": {
                "agent-wiki-cli": identity["version"],
                "pytest": "9.1.1",
                "pytest-cov": "7.1.0",
            },
        },
        "runs": {
            "collection": {"exit_code": 0, "seconds": 1.0},
            "union": {"exit_code": 0, "seconds": 2.0},
        },
        "setup_seconds": 1.0,
        "execution_seconds": 3.0,
        "files": {p.name: q.sha256_file(p) for p in directory.iterdir()},
    }
    q.write_json(directory / "execution.json", execution)
    for lane in suites.LANES:
        suites.projection(
            directory, lane, directory / "identity.json", inventory, execution
        )
    return directory
