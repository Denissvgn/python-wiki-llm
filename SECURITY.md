# Security Policy

## Supported Versions

LLM Wiki CLI is currently alpha-stage software. Security fixes target the latest
released package and the `main` branch. Older versions may not receive separate
patch releases.

## Reporting a Vulnerability

Please do not report security vulnerabilities in a public issue.

Preferred reporting path:

1. Use GitHub private vulnerability reporting if it is enabled for the
   repository.
2. Otherwise contact the maintainer listed in `pyproject.toml` and include
   `SECURITY` in the subject.

Include:

- Affected version or commit.
- Operating system and Python version.
- A minimal reproduction or proof of concept.
- Impact and whether the issue requires a malicious repository, local user
  access, or remote input.
- Any logs or generated files needed to understand the issue, with secrets
  removed.

You should receive an initial response when the maintainer has had time to
review the report. If the issue is accepted, the fix will normally be developed
privately or in a minimally revealing public PR, then documented after release.

## Security Model and High-Risk Areas

LLM Wiki CLI runs locally on developer machines and intentionally integrates
with source trees, git hooks, and external coding-agent CLIs. The highest-risk
areas are:

- Headless agent execution from post-commit hooks.
- Prompt files generated from git diffs and source inventory.
- Path handling for `--src-dir`, `--wiki-dir`, and generated page links.
- Subprocess execution for TypeScript, Go, and Rust extractors.
- Preservation and migration of existing wiki content.

Do not run automated sync against untrusted repositories or untrusted agent
CLIs. Review generated prompts and wiki diffs when working with sensitive code.

## Handling Secrets

Generated prompt files are filtered before they are written using best-effort
credential-pattern matching. This is not secret detection: unfamiliar formats,
split or encoded values, and other sensitive source text can remain. Review
generated prompts before sharing them.

Current releases do not create background sync logs. Older installations may
still have local runtime artifacts. Avoid committing or sharing:

- `.git/llm-wiki-prompt.txt`
- `.git/llm-wiki-sync.log`
- `.git/llm-wiki-breaker.json`
- Other local hook/runtime artifacts

The project attempts to ignore these local files, but users remain responsible
for reviewing generated artifacts and commits before publishing them.
