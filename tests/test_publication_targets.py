"""Publication targets: the registry, the built-in GitHub wiki and a custom target."""

from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any

import pytest

from llm_wiki_cli import api
from llm_wiki_cli.engine import Engine, NoProcessHost
from llm_wiki_cli.services import publication_candidate as candidate
from llm_wiki_cli.services import publication_delivery as delivery
from llm_wiki_cli.services import publication_links
from llm_wiki_cli.services.publication_config import (
    PublicationConfigError,
    validate_publication_config,
)
from llm_wiki_cli.services.publication_targets import (
    DEFAULT_PUBLICATION_TARGETS,
    GITHUB_WIKI_TARGET,
    GitHubWikiTarget,
    PublicationTarget,
    PublicationTargetRegistry,
    current_publication_targets,
    publication_target,
    using_publication_targets,
)
from tests.test_publication_candidate import configure
from tests.test_publication_delivery import BASE, SOURCE, checked, opt_in
from tests.test_publication_impact import consumer as consumer

KIND = "example/docs-site"
STAMP = "\n<!-- published by the docs site -->\n"


class DocsSiteTarget(PublicationTarget):
    """Stamps every page, needs ``Home.md`` and accepts ``group/sub/project`` names."""

    kind = KIND

    def __init__(self, stamp: str = STAMP) -> None:
        self.stamp = stamp

    def check_repository(self, value: object, field: str) -> str:
        if not isinstance(value, str) or value.count("/") < 2:
            raise ValueError("must be a group/subgroup/project path")
        return value

    def prepare_page(self, markdown: str, **_: Any) -> str:
        return markdown + self.stamp

    def check(self, files: Mapping[str, bytes]) -> dict[str, Any]:
        findings = [
            {"path": path, "kind": "unstamped", "message": "Page lacks the site stamp"}
            for path, raw in sorted(files.items())
            if path in {"Home.md", "Accounts.md"} and not raw.endswith(self.stamp.encode())
        ]
        return {"ok": not findings, "findings": findings}

    def identity(self) -> Any:
        return {"kind": self.kind, "stamp": self.stamp}


SITE = DEFAULT_PUBLICATION_TARGETS.with_target(DocsSiteTarget())


def _retarget(root, kind=KIND, repository="self") -> dict[str, Any]:
    path = root / ".llm-wiki/publication.json"
    policy = json.loads(path.read_text())
    policy["target"] = {**policy["target"], "kind": kind, "repository": repository}
    path.write_text(json.dumps(policy), encoding="utf-8")
    return policy


def test_default_registry_serves_only_the_github_wiki():
    assert current_publication_targets() is DEFAULT_PUBLICATION_TARGETS
    assert DEFAULT_PUBLICATION_TARGETS.kinds == ("github-wiki",)
    assert DEFAULT_PUBLICATION_TARGETS.identity() is None
    assert PublicationTargetRegistry((GitHubWikiTarget(),)).identity() is None
    assert publication_target("github-wiki") is GITHUB_WIKI_TARGET
    with pytest.raises(KeyError, match="no publication target"):
        publication_target(KIND)
    files = {"Home.md": b"# Home\n\n[Missing](Missing)\n"}
    assert GITHUB_WIKI_TARGET.check(files) == publication_links.check_github_wiki(files)
    assert GITHUB_WIKI_TARGET.check_repository("owner/repo", "f") == "owner/repo"
    with pytest.raises(PublicationConfigError, match="GitHub owner/repository"):
        GITHUB_WIKI_TARGET.check_repository("group/sub/project", "f")


def test_registry_refuses_ambiguous_or_foreign_targets():
    with pytest.raises(ValueError, match="at least one"):
        PublicationTargetRegistry(())
    with pytest.raises(ValueError, match="unique"):
        PublicationTargetRegistry((DocsSiteTarget(), DocsSiteTarget()))
    with pytest.raises(TypeError):
        PublicationTargetRegistry((object(),))  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="non-empty kind"):
        PublicationTargetRegistry((PublicationTarget(),))
    with pytest.raises(TypeError):
        with using_publication_targets(object()):  # type: ignore[arg-type]
            pass
    replaced = SITE.with_target(DocsSiteTarget("\n<!-- v2 -->\n"))
    assert replaced.kinds == SITE.kinds == ("github-wiki", KIND)
    assert replaced.identity() != SITE.identity() is not None


def test_policy_target_kind_and_repository_follow_the_registry(consumer):
    policy = _retarget(consumer, repository="group/sub/project")
    with pytest.raises(PublicationConfigError, match="target.kind: must be one of github-wiki"):
        validate_publication_config(policy, consumer_root=None)
    with using_publication_targets(SITE):
        assert validate_publication_config(policy, consumer_root=None)["target"]["kind"] == KIND
        bad = {**policy, "target": {**policy["target"], "repository": "owner/repo"}}
        with pytest.raises(PublicationConfigError) as caught:
            validate_publication_config(bad, consumer_root=None)
    assert caught.value.field == "target.repository"
    assert "group/subgroup/project" in caught.value.message


def test_custom_target_prepares_and_checks_the_candidate(consumer):
    configure(consumer)
    _retarget(consumer)
    with using_publication_targets(SITE):
        receipt = candidate.export_publication_candidate(
            consumer, output_dir="reports/candidate", target_dir="public"
        )
    default_provider = candidate._provider()
    files = candidate._read_tree(consumer / "reports/candidate")
    assert files["Home.md"].endswith(STAMP.encode())
    assert receipt["checks"] == {"ok": True, "findings": []}
    assert receipt["provider"]["fingerprint"] != default_provider["fingerprint"]

    # The receipt is rechecked by the same target kind, under the same targets only.
    with using_publication_targets(SITE):
        candidate.validate_candidate_tree(consumer, "reports/candidate", receipt)
        candidate.check_publication_candidate(
            consumer, candidate_dir="reports/candidate", receipt=receipt, target_dir="public"
        )
    with pytest.raises(ValueError, match="Invalid portable publication document"):
        candidate.check_publication_candidate(
            consumer, candidate_dir="reports/candidate", receipt=receipt, target_dir="public"
        )
    changed = DEFAULT_PUBLICATION_TARGETS.with_target(DocsSiteTarget("\n<!-- v2 -->\n"))
    with using_publication_targets(changed), pytest.raises(ValueError):
        candidate.check_publication_candidate(
            consumer, candidate_dir="reports/candidate", receipt=receipt, target_dir="public"
        )


def test_engine_grants_publication_targets(consumer):
    configure(consumer)
    _retarget(consumer)
    engine = Engine(host=NoProcessHost(), publication_targets=SITE)
    assert engine.capabilities()["publication_targets"] == {"kinds": ["github-wiki", KIND]}
    receipt = engine.call(
        api.export_publication_candidate,
        consumer,
        output_dir="reports/candidate",
        target_dir="public",
    )
    assert receipt["basis"]["config"]["target"]["kind"] == KIND
    with pytest.raises(TypeError):
        Engine(publication_targets=object())  # type: ignore[arg-type]
    with engine.operation() as operation:
        assert operation.publication_targets is SITE
        assert current_publication_targets() is SITE
    assert current_publication_targets() is DEFAULT_PUBLICATION_TARGETS


def test_delivery_uses_the_target_repository_rules(consumer):
    policy = opt_in(consumer)
    policy["target"]["kind"] = KIND
    (consumer / ".llm-wiki/publication.json").write_text(json.dumps(policy), encoding="utf-8")
    scope = {
        "source_repository": "group/sub/project",
        "target_repository": "group/sub/project",
        "target_branch": "wiki/main",
    }
    with using_publication_targets(SITE):
        receipt, files = checked(consumer, "first", SOURCE, BASE)
        before = candidate._read_tree(consumer / "public", target_snapshot=True)
        output, state = delivery.plan_delivery(
            receipt, files, before, policy=policy, target_revision=BASE, **scope
        )
        assert state and state["target_repository"] == "group/sub/project"
        assert delivery.split_delivery_tree(output) == (files, state)
        with pytest.raises(PublicationConfigError, match="group/subgroup/project"):
            delivery.plan_delivery(
                receipt, files, before, policy=policy, target_revision=BASE,
                **{**scope, "target_repository": "owner/repo"},
            )
    # Without the custom target, its checkpoint names an unknown repository form.
    with pytest.raises(ValueError, match="GitHub owner/repository"):
        delivery.split_delivery_tree(output)
