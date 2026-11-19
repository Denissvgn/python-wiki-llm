# LLM Wiki Engine

`llm-wiki-engine` is the standard-library-only core of LLM Wiki. It has no
third-party dependencies. Processes, environment variables, the working
directory and the clock are reached only through a replaceable host object.

It provides:

- canonical JSON encodings and SHA-256 digests used by every stored format;
- the host boundary: process runner, environment, working directory and clock;
- path, request and redaction rules;
- guarded filesystem writes, which keep the destination's directories from
  being swapped for links or junctions mid-write, and wiki file I/O;
- ignore-file matching, source-selection profiles and protected-artifact
  checks;
- the knowledge graph, evidence and concept-identity vocabularies;
- the knowledge store: the knowledge model and index, governance, packed
  storage, the sync manifest, maintenance state and recovery, and the
  freshness, consumption and verification formats;
- analysis-compatibility records;
- wiki surface, media, surface-index and section-ownership rules;
- lexical search ranking;
- validators for published formats such as extract payloads, documentation
  query and search results, and maintenance status and queue reports.

The knowledge store does not analyze sources itself. Concept implementation
evidence, source snapshots, the active domain pack and a few issued state
types come from the application through `llm_wiki_engine.integrations`, which
names a provider module for each capability. `agent-wiki-cli` provides all of
them as soon as `llm_wiki_cli` is imported, so a program that uses the engine
next to the CLI imports `llm_wiki_cli` first. An operation that needs a
capability nobody provided fails with `IntegrationUnavailable`.

The import package is `llm_wiki_engine`. It requires Python 3.11 or later.

```bash
pip install llm-wiki-engine
```

The code-documentation CLI, [`agent-wiki-cli`](https://pypi.org/project/agent-wiki-cli/),
depends on an exact version of this package. Both are released together and
share one version number. Its older
`llm_wiki_cli.services.<module>` import paths for these modules still work as
aliases of the same modules, but they are deprecated: importing one raises a
`DeprecationWarning` that names the `llm_wiki_engine.<module>` path to use.

Source: <https://github.com/Denissvgn/python-wiki-llm>, in the `src/`
directory. Licensed under the MIT License.
