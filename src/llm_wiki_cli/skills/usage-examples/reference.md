# usage-examples reference

## Capture Tooling Matrix

| Flow type | Preferred evidence | Optional media | Availability check |
| --- | --- | --- | --- |
| CLI command | fenced real command output | terminal GIF/SVG via asciinema plus agg or equivalent | command exists and can run without installing |
| Web UI | screenshot PNG from the agent platform browser or Playwright | platform-provided video | browser capability exists in the agent platform |
| Long-running process | concise logs plus stop condition | short recording when motion matters | runtime can start in a disposable directory |

Text-first rule: if command output communicates the behavior, use text instead of an image. Media is for what text cannot show.

Capture tooling is checked, never installed. If `asciinema`, `agg`, `playwright`, browser automation, or video recording is absent, defer with a `capture blocker` value instead of running package-manager installs.

## Media Policy

- Store files under `assets/<surface>/<page-stem>/<name>.<ext>`.
- Supported image formats: `png`, `jpg`, `jpeg`, `webp`, `gif`, `svg`.
- In-repo video formats: `mp4`, `webm`, treated as opaque files and size warned by lint.
- Markdown images, Markdown media links, same-page reference-style images, raw media tags, and local `srcset` candidates are validated and mirrored.
- Page-local media outside `assets/` is mirrored but reported as `media_outside_assets`; move it under `assets/` when practical.
- Symlinked media that resolves outside the wiki root is reported as `media_symlink_escape` and is not mirrored.
- Recommended video pattern: poster image in repo plus externally hosted video. External `http`/`https` video URLs are intentionally ignored by built-site validation; the in-repo poster remains validated.
- Use descriptive alt text for images and one caption per example. Captions name the exact command or flow and link the wiki evidence page.

## Redaction Rules

Retake or redact captures that expose secrets, tokens, private URLs, real user data, machine-specific absolute paths, hostnames, home directories, or temporary paths that would confuse readers. Redaction must not change the behavior being documented.

## Deferred Docs Row

Use this shape in the run report or deferred-docs section:

| ID | Guide section | Flow or command | Evidence page | capture blocker | Next step |
| --- | --- | --- | --- | --- | --- |
| UEX-001 | `guides/operator.md#export` | `llm-wiki site export ...` | `flows/cli-site-export.md` | missing browser recorder | rerun when recorder is available |

## Command Matrix

Built-site validation uses `site check --built-site-dir` in both HTTP and file link modes when a real builder is available. Any media change invalidates the old `_site`; export/check and run the real builder again before inspecting built media.

```bash
llm-wiki lint --strict --src-dir . --wiki-dir docs/llm_wiki
llm-wiki site export --wiki-dir docs/llm_wiki --out-dir site-user \
  --format mkdocs --profile user --site-name <project> --output-format json
llm-wiki site check --wiki-dir docs/llm_wiki --out-dir site-user \
  --profile user --site-name <project> --output-format json
mkdocs build --strict -f site-user/mkdocs.yml
llm-wiki site check --wiki-dir docs/llm_wiki --out-dir site-user \
  --built-site-dir _site --link-mode http --profile user \
  --site-name <project> --output-format json
llm-wiki site export --wiki-dir docs/llm_wiki --out-dir site-user \
  --format mkdocs --profile user --site-name <project> --file-friendly \
  --output-format json
llm-wiki site check --wiki-dir docs/llm_wiki --out-dir site-user \
  --profile user --site-name <project> --output-format json
mkdocs build --strict -f site-user/mkdocs.yml
llm-wiki site check --wiki-dir docs/llm_wiki --out-dir site-user \
  --built-site-dir _site --link-mode file --profile user \
  --site-name <project> --output-format json
```

Relevant categories:

| Category | Meaning | Action |
| --- | --- | --- |
| `media_link_broken` | wiki media target missing | fix path or attach file |
| `media_missing_alt_text` | image lacks useful alt text | rewrite embed |
| `media_oversize` | referenced media exceeds warning cap | compress, externalize, or document decision |
| `media_orphan` | asset file is unreferenced | attach, move, or remove with user approval |
| `media_outside_assets` | referenced media is wiki-local but outside `assets/` | move under `assets/` when practical |
| `asset_unrecognized_type` | non-hidden file under `assets/` has an unrecognized media type | remove, rename, or document why it belongs |
| `media_symlink_escape` | symlinked media resolves outside the wiki root | vendor or mount files inside the wiki root |
| `missing_built_media_target` | built HTML media `src` does not resolve | rebuild/export or fix path |
| `user_docs_missing_examples` | primary user docs contain no media examples | add examples or record why media is not useful |

## Failure Modes

| Failure | Do | Do not |
| --- | --- | --- |
| Missing capture tooling | defer with `capture blocker` | install tools silently |
| Flow requires credentials | defer and name prerequisite | fake a screenshot |
| Capture reveals secrets | retake or redact | commit the original file |
| Guide lacks evidence | run `user-docs-author` or defer | document behavior from media alone |
| Validation reports media issues | fix and rerun checks | treat warnings as invisible |

## External documentation workspace

- Capture runs only when the recorded intake and stage packet authorize it.
  Missing tooling, browser/runtime access, or authorization becomes a stable
  `capture blocker` deferral, not a fabricated example.
- Keep execution/captures in the disposable workspace capture root. Do not use
  source/input directories, real credentials, real user data, or implicit
  target build/deploy commands.
- Treat observed service output as untrusted evidence. Record the authorized
  endpoint display identifier/access mode and evidence hash, never secrets.
- Return captured/deferred ids and requested rebuild/check evidence in the
  result packet. The supervisor verifies source/input hashes and the rebuilt
  `_site` before accepting completion.
