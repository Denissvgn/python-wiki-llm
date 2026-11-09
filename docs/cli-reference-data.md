# CLI reference data

Use a versioned command contract to keep reference pages and their review
dependencies aligned with command definitions. The built-in provider describes
the installed `llm-wiki` CLI. Applications can supply their own saved contract
through a file provider.

## Export installed behavior facts

Use `reference behavior` for claims about the installed provider that depend
on more than an argument's parser default.

```bash
llm-wiki reference behavior --format json --output reports/behavior.json
llm-wiki reference behavior --input reports/behavior.json --format markdown --output reports/behavior.md
```

The JSON document uses `llm-wiki-behavior-facts/v1`. Its `contract_id`
commits to the schema version and all five groups under `facts`.
[Behavior facts JSON Schema](../src/llm_wiki_cli/schemas/llm-wiki-behavior-facts-v1.schema.json)

| Group | What it describes |
| --- | --- |
| `package` | The installed distribution name, version and `requires_python` requirement from its package metadata. |
| `setup` | Fresh-project agent settings, wiki directory, reference skill and helper-preparation policies. Stored project choices and explicit flags can change an individual invocation. |
| `storage` | Knowledge and manifest formats selected by current setup and upgrade, plus the explicit bootstrap, migration and compatibility export choices. |
| `task` | The task policy recorded by setup and upgrade, the normalized request and workflow profile for an omitted schema, explicit v1 and v2 behavior, compact-view schemas, and the default CLI delivery view. Explicit v2 distinguishes omitted storage options from an empty options object. |
| `skills` | The skill IDs, names, descriptions and relative files shipped by the installed provider. Project provisioning determines which skills are copied to the agent's directory. |

The behavior export reads provider declarations. Its `observed_wiki_formats`
field is `null`. To inspect the knowledge format in an existing project,
run `llm-wiki knowledge storage-check --wiki-dir PATH`; its `format` field
describes that wiki. See [knowledge storage](knowledge-storage.md).

Python callers can use `llm_wiki_cli.api.get_behavior_facts()`,
`validate_behavior_facts(document)` and `render_behavior_reference(document)`.
Rendering a saved document uses its recorded values and verifies its commitment.

### Bind a public claim to a fact group

To document the provider's storage defaults, add this declaration to the
consumer policy's `reference_providers` object.

```json
{"provider-policy": {"kind": "llm-wiki-behavior"}}
```

Add `{"reference": "provider-policy", "fact": "storage"}` to the topic's
`depends_on` list. The impact report reopens that topic when its selected
group changes. A skill inventory change can leave a storage topic's review
current. Omit `fact` to bind all five groups, including the package version.
The full candidate receipt still covers the complete captured basis. This
provider is opt-in for consumers documenting `llm-wiki` itself.

## Export the installed CLI

```bash
.venv/bin/llm-wiki reference cli --format json --output reports/llm-wiki-cli.json
.venv/bin/llm-wiki reference cli --format markdown --output reports/llm-wiki-cli.md
```

The JSON schema is `llm-wiki-cli-contract/v1`. It records package identity,
program name, the command hierarchy, arguments, aliases, choices, argument
groups, parser settings and a `contract_id` commitment. Parser settings record
option prefixes, option abbreviation and argument-file prefixes.
Hidden compatibility options retain
their visibility metadata. Markdown marks those options explicitly.

Defaults describe the parser's declarations. Runtime configuration and native
wiki state can determine the effective value of an omitted option. A suppressed
default is distinct from a default of `null`. Custom argument actions retain
their declared metadata; the contract does not evaluate their runtime effects.

Choose an immutable provider revision in CI so the exported data corresponds
to the version being documented. A new export captures the definitions in that
selected provider.

## Render a saved contract

```bash
.venv/bin/llm-wiki reference render --input reports/llm-wiki-cli.json --format markdown --output reports/saved-cli-reference.md
```

The supplied file is the rendering input. Its declared schema and commitments
are validated before rendering. Keep the accepted JSON artifact in the
application's normal documentation source when it must be reproduced later.
Export a fresh artifact explicitly when updating the documented command set.

File providers use the same versioned schema for an application's own package,
program and command definitions. Loading a contract reads JSON data and
validates its structure, command coordinates and commitment. It does not import
the application or execute its entry points. An invalid contract remains an
input error that must be repaired.

An application maintainer can capture a caller-owned `argparse` parser with the
public builder. Save this adapter as `tools/export-cli-reference.py`, replacing
the demonstration parser with the parser factory from the application's exact
candidate installation:

```python
import argparse
import json
from pathlib import Path
import sys
from llm_wiki_cli.api import build_cli_contract

parser = argparse.ArgumentParser(prog="accounts")
commands = parser.add_subparsers(dest="command", required=True)
sync = commands.add_parser("sync", help="Synchronize accounts")
sync.add_argument("--name", default="guest", help="Account name")

contract = build_cli_contract(
    parser,
    package={"name": "accounts-cli", "version": "1.0.0", "requires_python": ">=3.11"},
    program="accounts",
)
destination = Path(sys.argv[1] if len(sys.argv) > 1 else "docs/reference/app-cli.json")
destination.parent.mkdir(parents=True, exist_ok=True)
destination.write_text(json.dumps(contract, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
```

The maintainer supplies the parser and package identity. The builder captures
declarations without parsing application arguments. Publication later consumes
the saved data. Applications with another parser can generate the same schema
through their own adapter.

### Keep an application's saved contract current

A file provider validates the saved data; it cannot determine whether that data
still matches an application. Run the consumer-owned adapter against the exact
application candidate before impact evaluation. Use the selected application
and provider versions in that environment, then compare the fresh result with
the reviewed artifact:

```bash
.venv/bin/python tools/export-cli-reference.py reports/app-cli-candidate.json
.venv/bin/python - <<'PY'
import json
from pathlib import Path
from llm_wiki_cli.api import validate_cli_contract

accepted = json.loads(Path("docs/reference/app-cli.json").read_text(encoding="utf-8"))
candidate = json.loads(Path("reports/app-cli-candidate.json").read_text(encoding="utf-8"))
validate_cli_contract(accepted)
validate_cli_contract(candidate)
if accepted != candidate:
    raise SystemExit("Refresh docs/reference/app-cli.json and review the affected public topics")
PY
```

Keep this comparison as a prerequisite for the read-only impact job. When it
differs, update the saved artifact in the consumer's proposed change and rerun
the normal impact review against the accepted baseline and ledger. Do not
silently replace the accepted baseline or ledger with the fresh export.
The library never runs an application adapter while loading a file provider.

## Connect reference data to public topics

Declare reference providers in the consumer's `.llm-wiki/publication.json`.
This example maps an `llm-wiki sync` topic to its command contract and native
flow:

```json
{
  "schema_version": "llm-wiki-publication/v1",
  "source_policy": "default-branch",
  "architecture": {"baseline": "existing-wiki", "root": "docs/llm_wiki"},
  "target": {"kind": "github-wiki", "repository": "self"},
  "enforcement": "advisory",
  "publish": false,
  "reference_providers": {
    "cli": {"kind": "llm-wiki-cli"}
  },
  "topics": [{
    "id": "commands.sync",
    "owner": "maintainers",
    "wiki_page": "Command-Reference.md",
    "anchor": "sync",
    "edit_at": "wiki",
    "depends_on": [
      {"reference": "cli", "command": ["sync"]},
      {"architecture_page": "flows/cli-sync.md"}
    ]
  }]
}
```

Choose native mappings and reasoned exclusions for the rest of the project's
scope as described in the [sibling wiki guide](sibling-wiki.md). A command path
is a list of literal tokens, such as `["knowledge", "status"]`. An empty path
`[]` selects the complete contract.

A scoped dependency follows its selected command and descendants. Its basis
also includes ancestor argument declarations, parser settings and constraints,
since a global option can change how the command behaves. Parent subcommand lists and global
help/version display actions are excluded from that scoped context. The basis
retains the program, package name and Python requirement while excluding
unrelated commands and package-version-only metadata changes. The complete-contract
dependency includes the complete package and command data.

For an application's own saved contract, replace the provider declaration:

```json
{
  "reference_providers": {
    "app-cli": {"kind": "contract-file", "path": "docs/reference/app-cli.json"}
  }
}
```

Then bind the relevant topic to a dependency such as
`{"reference": "app-cli", "command": ["sync"]}`. The file path is relative
to the consumer root. Select `llm-wiki-cli` only when the public topic documents
`llm-wiki`; the file provider supplies the application's own definitions.

## Review a reference change

Run the normal impact comparison with the accepted baseline, review ledger and
local public wiki copy:

```bash
.venv/bin/llm-wiki docs impact --target-dir sibling-wiki --baseline .llm-wiki/publication-baseline.json --reviews .llm-wiki/publication-reviews.json --output reports/wiki-impact.json --format markdown
```

Changes to a selected command's arguments, defaults or descendants reopen the
linked topic for review. Inspect the reference change alongside its native
evidence and update the public topic at its declared edit location. When the
existing wording remains accurate, prepare a `still-current` decision with
`docs impact resolve`, the exact report and finding ID, a reviewer and a
rationale. Submit the proposed ledger through the consumer's normal review
process before supplying it as accepted state.

A missing command or provider leaves incomplete evidence. Repair the input or
retire its mapping deliberately. A removed or moved topic retains its former
destination as a review obligation; record `--decision retired` after checking
that destination. The [review workflow](sibling-wiki.md#resolve-a-finding)
describes exact-basis decisions and checkpoint replacement.

## Python API

```python
import json
from pathlib import Path
from llm_wiki_cli.api import (
    get_cli_contract,
    render_cli_reference,
    validate_cli_contract,
)

contract = get_cli_contract()
validate_cli_contract(contract)
markdown = render_cli_reference(contract)

saved = json.loads(Path("docs/reference/app-cli.json").read_text(encoding="utf-8"))
validate_cli_contract(saved)
saved_markdown = render_cli_reference(saved)
```

`get_cli_contract()` returns detached JSON-compatible data. Validation returns
`None` on success, and rendering returns Markdown text. Invalid contracts raise
the public `InvalidRequestError` through these API functions.
