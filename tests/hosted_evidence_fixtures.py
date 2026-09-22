"""Owned GitHub metadata and artifact ZIPs for provenance boundary controls."""

from copy import deepcopy
import io
import zipfile

from release import hosted_evidence as hosted


class HostedEvidence:
    def __init__(self, identity, run_id, source, layout="legacy"):
        self.identity = identity
        self.run_id = run_id
        self.layout = layout
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
        contract = hosted.artifact_contract(layout)
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
                archive.writestr(name, data)
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
