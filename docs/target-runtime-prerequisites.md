# Wiki capture prerequisites for another runtime

A wiki can align with its local analyzer while carrying a capture that cannot
be compared on another host. Inspect the recorded prerequisites before requesting
hosted proof:

```sh
llm-wiki doctor --wiki-dir docs/llm_wiki --target-runtime private/targets.json --format json
```

Use a permitted target file inside the current project. Its only top-level field
is `targets`, an array of project-owned declarations. Obtain the values from the
project's maintained proof owners, including invoked composite actions or other
runtime setup. Do not copy another project's platform or infer a missing value
from the local computer. The following illustrates the input shape, rather than
a default environment:

```json
{
  "targets": [
    {
      "owner": "project-proof-owner",
      "platform": "linux",
      "machine": null,
      "python": "3.13",
      "implementation": "CPython"
    }
  ]
}
```

`platform` and `machine` use the analyzer host's native runtime identifiers.
`python` names that analyzer's Python runtime, independently of the application's
language. A missing field or `null` is unknown. A minor Python declaration leaves
the patch unknown for captures that require an exact runtime. Optional `helpers`
map component IDs to declared helper toolchain strings; `components` can select
explicit component IDs. An optional `capture_route` is descriptive project data
and is never executed. Owner identifiers must be unique. The file is optional;
no new project manifest or hosted configuration is installed.

The result separates matching declared provenance, registered portable runtime
commitments, known mismatches requiring capture, and unknown requirements.
`requirements-match` means the declared prerequisites align; it does not verify a
future target's runtime identity, dependency versions, package implementation,
source freshness, full snapshot integrity, semantic review, or hosted execution.
The original implementation/configuration/runtime commitments remain separate.
Only registered portability is recognized. Missing helper or target details
remain unknown rather than borrowing the local environment.

The command reads committed producer headers and their root/surface bindings.
It does not inventory application sources, run extractors or target commands,
prepare helpers, refresh wiki content, adopt ownership, or dispatch proof.
Rows have explicit bounds; aggregate mismatch/unknown counts include omitted
rows. Unknown or capture-required results exit with status 2; matching declared
prerequisites exit with status 0. Ordinary `doctor` behavior is unchanged.

When capture is required, follow the project's authorized target-host owning
route, authenticate the complete snapshot and review all changes and removals.
Obtain fresh target-native proof afterward. The diagnostic grants no authority
to change data, relax comparison policy, or treat a local receipt as hosted
qualification. A project's own preflight can consume the same diagnostic before
requesting proof.
