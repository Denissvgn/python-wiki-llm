# LLM Wiki Engine

`llm-wiki-engine` is the standard-library-only core of LLM Wiki. It has no
third-party dependencies. Processes, environment variables, the working
directory and the clock are reached only through a replaceable host object.

It provides:

- canonical JSON encodings and SHA-256 digests used by every stored format;
- the host boundary: process runner, environment, working directory and clock;
- path, request and redaction rules;
- the knowledge graph, evidence and concept-identity vocabularies;
- wiki surface, media and section-ownership rules;
- lexical search ranking;
- validators for published formats such as extract payloads, documentation
  query and search results, and maintenance status and queue reports.

The import package is `llm_wiki_engine`. It requires Python 3.11 or later.

```bash
pip install llm-wiki-engine
```

The code-documentation CLI, [`agent-wiki-cli`](https://pypi.org/project/agent-wiki-cli/),
depends on an exact version of this package. Its
`llm_wiki_cli.services.<module>` import paths for these modules stay
available as aliases of the same modules.

Source: <https://github.com/Denissvgn/python-wiki-llm>, in the `src/`
directory. Licensed under the MIT License.
