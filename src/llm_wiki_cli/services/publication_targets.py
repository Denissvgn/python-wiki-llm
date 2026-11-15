"""Publication targets: where a reviewed documentation candidate is delivered.

A :class:`PublicationTarget` owns the rules of one ``target.kind`` value in a
publication policy:

* :meth:`~PublicationTarget.check_repository` validates the policy's
  ``target.repository`` identifier and the repositories a delivery names;
* :meth:`~PublicationTarget.prepare_page` turns an authored Markdown page into
  the text the target publishes (rewriting links, for instance);
* :meth:`~PublicationTarget.check` checks a complete candidate tree without
  filesystem or network access and returns the ``{"ok", "findings"}`` report
  stored in a candidate receipt.

A :class:`PublicationTargetRegistry` maps kinds to targets. The default holds
:class:`GitHubWikiTarget` (``"github-wiki"``) only. A host adds targets with
:func:`using_publication_targets` or ``Engine(publication_targets=...)``; a
policy naming a kind no registered target serves is refused. A registry with
custom targets changes the candidate provider fingerprint, so a receipt
prepared under one set of targets is not trusted under another.

Delivery planning stays a pure composition of files: no target mutates a
remote inside the package. The policy shape (``kind``, ``repository``,
``branch``) and flat ``.md`` page names are fixed by the publication policy
format.
"""

from __future__ import annotations

from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass, replace
from typing import Any


class PublicationTarget:
    """The rules of one publication target kind.

    Subclasses set :attr:`kind` and implement the three hooks. Hooks must be
    deterministic: a candidate is rechecked by running them again.
    """

    kind: str = ""

    def check_repository(self, value: object, field: str) -> str:
        """Return ``value`` as a valid repository identifier or raise ``ValueError``."""
        raise NotImplementedError

    def prepare_page(
        self,
        markdown: str,
        *,
        source_path: str,
        source_pages: Mapping[str, str],
        source_assets: Mapping[str, str],
        repository_url: str | None,
        source_revision: str | None,
    ) -> str:
        """The published text of authored page ``source_path``.

        ``source_pages`` and ``source_assets`` map authored source paths to
        their published paths; ``repository_url`` and ``source_revision`` let
        links to unpublished sources point at the source repository.
        """
        raise NotImplementedError

    def check(self, files: Mapping[str, bytes]) -> dict[str, Any]:
        """Check a complete candidate tree.

        Return ``{"ok": bool, "findings": [{"path", "kind", "message"}, ...]}``
        with ``ok`` true exactly when there are no findings, in a stable order.
        """
        raise NotImplementedError

    def identity(self) -> Any:
        """A JSON-ready value that changes whenever this target's output may change."""
        return {"kind": self.kind, "class": f"{type(self).__module__}.{type(self).__qualname__}"}


class GitHubWikiTarget(PublicationTarget):
    """A GitHub wiki: flat Markdown pages, ``Home.md`` required, ``owner/repo`` names."""

    kind = "github-wiki"

    def check_repository(self, value: object, field: str) -> str:
        from .publication_config import publication_repository

        return publication_repository(value, field)

    def prepare_page(
        self,
        markdown: str,
        *,
        source_path: str,
        source_pages: Mapping[str, str],
        source_assets: Mapping[str, str],
        repository_url: str | None,
        source_revision: str | None,
    ) -> str:
        from . import publication_links

        return publication_links.prepare_wiki_markdown(
            markdown,
            source_path=source_path,
            source_pages=source_pages,
            source_assets=source_assets,
            repository_url=repository_url,
            source_revision=source_revision,
        )

    def check(self, files: Mapping[str, bytes]) -> dict[str, Any]:
        from . import publication_links

        return publication_links.check_github_wiki(files)


GITHUB_WIKI_TARGET = GitHubWikiTarget()


@dataclass(frozen=True)
class PublicationTargetRegistry:
    """The publication targets a policy may name, keyed by ``target.kind``."""

    targets: tuple[PublicationTarget, ...] = (GITHUB_WIKI_TARGET,)

    def __post_init__(self) -> None:
        targets = tuple(self.targets)
        if not targets:
            raise ValueError("a publication target registry needs at least one target")
        kinds = set()
        for target in targets:
            if not isinstance(target, PublicationTarget):
                raise TypeError("publication targets must be PublicationTarget values")
            if not isinstance(target.kind, str) or not target.kind:
                raise ValueError("a publication target needs a non-empty kind")
            if target.kind in kinds:
                raise ValueError(f"publication target kinds must be unique: {target.kind!r}")
            kinds.add(target.kind)
        object.__setattr__(self, "targets", targets)

    @property
    def kinds(self) -> tuple[str, ...]:
        return tuple(target.kind for target in self.targets)

    def get(self, kind: str) -> PublicationTarget:
        """The target serving ``kind``; ``KeyError`` when none is registered."""
        for target in self.targets:
            if target.kind == kind:
                return target
        raise KeyError(f"no publication target is registered for kind {kind!r}")

    def with_target(self, target: PublicationTarget) -> PublicationTargetRegistry:
        """A copy that also serves ``target``, replacing any target of the same kind."""
        kept = tuple(item for item in self.targets if item.kind != target.kind)
        return replace(self, targets=(*kept, target))

    def describe(self) -> dict[str, Any]:
        """A JSON-ready summary of the registered kinds."""
        return {"kinds": list(self.kinds)}

    def identity(self) -> Any:
        """``None`` for the built-in targets, else a value naming every target."""
        if all(type(target) is GitHubWikiTarget for target in self.targets):
            return None
        return [target.identity() for target in self.targets]


#: Only the built-in GitHub wiki target.
DEFAULT_PUBLICATION_TARGETS = PublicationTargetRegistry()

_ACTIVE_TARGETS: ContextVar[PublicationTargetRegistry | None] = ContextVar(
    "llm_wiki_publication_targets", default=None
)


def current_publication_targets() -> PublicationTargetRegistry:
    """The registry chosen for this context, or :data:`DEFAULT_PUBLICATION_TARGETS`."""
    return _ACTIVE_TARGETS.get() or DEFAULT_PUBLICATION_TARGETS


def publication_target(kind: str) -> PublicationTarget:
    """The target serving ``kind`` in this context."""
    return current_publication_targets().get(kind)


@contextmanager
def using_publication_targets(
    registry: PublicationTargetRegistry,
) -> Iterator[PublicationTargetRegistry]:
    """Publish to the targets of ``registry`` inside the block."""
    if not isinstance(registry, PublicationTargetRegistry):
        raise TypeError("registry must be a PublicationTargetRegistry")
    token = _ACTIVE_TARGETS.set(registry)
    try:
        yield registry
    finally:
        _ACTIVE_TARGETS.reset(token)


__all__ = [
    "DEFAULT_PUBLICATION_TARGETS",
    "GITHUB_WIKI_TARGET",
    "GitHubWikiTarget",
    "PublicationTarget",
    "PublicationTargetRegistry",
    "current_publication_targets",
    "publication_target",
    "using_publication_targets",
]
