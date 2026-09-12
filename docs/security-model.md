# Security model

[Back to README](../README.md) · [Report a vulnerability](../SECURITY.md)

LLM Wiki is a local automation tool. It can generate prompt files containing
diffs, source structure, and architectural context. Prompt files are written
inside `.git/` by default and use owner-only permissions where the platform
supports that mode.

Manual CLI triggers can edit files and run commands according to the selected
agent's own permission model. Review generated prompt files and wiki diffs
before trusting agent-produced changes in a shared repository.

Native knowledge data is inert: loaders, status, freshness comparison, and
query methods never execute commands, hooks, plugins, URLs, or extension values
obtained from `.llm-wiki-knowledge.json`. Live service construction performs
static analysis through application configuration. Built-in extractors and
prepared helpers do not import or execute the target application. Installed
extractor plugins remain trusted, unsandboxed project-local Python and can have
effects outside the core read contract; artifact metadata never selects them.
The explicit `knowledge verify` command can run only fixed application-owned
pure checker IDs. Loading or linting its receipt never reruns a checker, and
document content cannot supply checker commands, arguments, helpers, network
targets, containers, or code.
See [Read-only and no-execution rules][native-knowledge-no-exec].

Standalone `docs` runs use a stricter external-workspace boundary. Source trees
and adopted wikis are read-only evidence; target agent-policy files, prompts,
plugin manifests, README instructions, and prior LLM prose cannot change the
run policy. The importer rejects symlinks, non-regular/non-portable paths,
agent-policy files, and cache content. Native inputs are validated from guarded,
descriptor-pinned bytes; complete v5 projections must match their exact marker
hashes and canonical Markdown snapshot. Source plugins are disabled unless the
caller explicitly passes `--trust-source-plugins`; artifact metadata cannot
enable them, and missing helpers and builders are never installed implicitly.
Live-service observation permission is opt-in, requires an explicit disposable
capture root, and rejects URL credentials/query/fragment data. The core records
that permission but makes no request and captures nothing; later host execution
needs separate authorization and must follow the packet's path contract.
Callers must still keep secrets and real user data out of paths, captures, and
documentation.

The `docs` core emits provider-neutral packets and never imports a provider SDK,
calls a model, stores provider credentials, deploys output, or installs target
instructions. Credential-free model-routing metadata is selected separately by
the host. Both generic-agent and handoff defaults must be low-cost; more
capable/costly routes require configured escalation evidence or a user
override. These tiers are host-declared labels, and the core provides no native
provider adapter, price verification, or proof of the model actually invoked.
See the [standalone documentation security and routing
guide](standalone-documentation.md#provider-neutral-low-cost-host-routing).

[native-knowledge-no-exec]: native-knowledge.md#read-only-and-no-execution-rules
