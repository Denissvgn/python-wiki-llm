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

## Runtime capture result contract

In an `external_agent_docs` result, `runtime_captures` is an optional array of
strict `llm-wiki-documentation-runtime-capture/v1` records. Each record carries:

- a stable `capture_id`, `command_or_flow_id`, and `result` (`captured`,
  `failed`, or `deferred`; completed attempts require an integer exit code and
  deferrals require null);
- exact `concept_uid` or `concept_locator` and an optional `section_locator`;
- a wiki-relative `capture_path` under the approved `assets/` surface and the
  SHA-256 `capture_digest` of the persisted, redacted bytes;
- `native_observation` with availability, reason, structural-evidence state,
  and the freshness state/reason only when freshness was evaluated;
- `redaction`, `environment`, and explicit `limitations`.

A deferred capture uses a null path and digest and names its blocker. A rejected
redaction or unavailable environment must be deferred. The supervisor verifies
the file digest and recomputes current concept/section reconciliation. Captures
remain out-of-band runtime evidence; neither a successful run nor an exact
binding changes native structural authority, freshness, lifecycle, human
review, machine verification, or permission to execute anything.
For PNG/JPEG/GIF/video/WebP evidence, record `redaction.outcome=redacted` and
retain both `binary-media-content-not-machine-inspected` and
`canonical-body-media-review-required` limitations. Digest validation cannot
inspect pixels; publication still requires the separate canonical body/media
review. Text, JSON, log, Markdown, and SVG captures are additionally scanned
for credential-like values, URI user information, and machine-specific
absolute paths.

## Command Matrix

Built-site validation uses `site check --built-site-dir` in both HTTP and file
link modes when a real builder is available. Hosted and direct-file selections
use distinct mirror/build directories. Any media change invalidates the old
build; export/check and run the real builder again before inspecting built
media. Mirror checks require the complete publication receipt; built checks
also require the matching marker at the built root.
When a managed capture pass changes canonical Markdown or media references,
run `llm-wiki sync --jobs 1 ...` before the strict lint shown below. Repeat
that owning sync after any later Markdown adjustment. In
`external_agent_docs`, the supervisor performs the assigned refresh; the
capture worker only returns authorized changes and requested checks.

```bash
llm-wiki sync --jobs 1 --src-dir . --wiki-dir docs/llm_wiki
llm-wiki lint --strict --src-dir . --wiki-dir docs/llm_wiki
llm-wiki ci-check --src-dir . --wiki-dir docs/llm_wiki --format json
llm-wiki site export --wiki-dir docs/llm_wiki --out-dir site-user-http \
  --format mkdocs --profile user --site-name <project> --output-format json
llm-wiki site check --wiki-dir docs/llm_wiki --out-dir site-user-http \
  --format mkdocs --link-mode http --profile user --site-name <project> \
  --output-format json
mkdocs build --strict -f site-user-http/mkdocs.yml --site-dir _site-user-http
llm-wiki site check --wiki-dir docs/llm_wiki --out-dir site-user-http \
  --format mkdocs --built-site-dir _site-user-http --link-mode http \
  --profile user \
  --site-name <project> --output-format json
llm-wiki site export --wiki-dir docs/llm_wiki --out-dir site-user-file \
  --format mkdocs --profile user --site-name <project> --file-friendly \
  --output-format json
llm-wiki site check --wiki-dir docs/llm_wiki --out-dir site-user-file \
  --format mkdocs --link-mode file --profile user --site-name <project> \
  --output-format json
mkdocs build --strict -f site-user-file/mkdocs.yml --site-dir _site-user-file
llm-wiki site check --wiki-dir docs/llm_wiki --out-dir site-user-file \
  --format mkdocs --built-site-dir _site-user-file --link-mode file \
  --profile user \
  --site-name <project> --output-format json
```

The command block shows publication policy `off`. Freeze one of these policies
before the first export and preserve it across every mirror and built check:

| Policy | Required behavior |
| --- | --- |
| `off` | Omit all Site knowledge options. After an enriched failure, this fallback must be an explicit new decision. |
| `public-portable` | Repeat `--knowledge-metadata summary --knowledge-profile public-portable`; repeat an exact corroborated public identity when supplied. |
| `internal` | Repeat `--knowledge-metadata summary --knowledge-profile internal` only for an explicitly authorized internal target. |

For a standalone run, make the same choice with `docs prepare
--knowledge-mode off|public-portable|internal` and optionally assert it on
`docs export`. Its export/check pair uses one snapshot-only policy and must
record matching source-knowledge hashes. Metadata redaction never sanitizes the
canonical page or captured media, which still need their own public-content
review.

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
- Return `runtime_captures` with digests and exact native bindings when the
  result schema supports them. Legacy result fields remain valid; do not
  fabricate capture records merely to fill the optional array.
