# Graph Scope Policy

Graph artifacts are future locator artifacts. They are not present in this staged draft, and they must not be treated as evidence for upstream behavior.

## Current Status

- No graph builder is implemented.
- No graphify command is run by this repository.
- No generated graph JSON, graph report, scope expansion, or coverage report is published.
- `schemas/locator-graph.schema.json` and `schemas/graph-report.schema.json` are contract-only documents for future reviewed tooling.

## Promptfoo Scope

`promptfoo-promptfoo` is the only current source with `graph.enabled: true`.

Its declared future graph scope is limited to:

- `site/docs`
- `examples`
- `plugins/promptfoo/skills`

This scope is suitable only for locating documentation, examples, and Promptfoo-bundled skill files. It is not sufficient for current CLI implementation behavior, provider internals, parser behavior, command behavior, or runtime execution claims. For those questions, read live upstream raw files or a pinned materialized worktree.

## Future Graph Requirements

A future graph builder must:

- operate only on a pinned materialized worktree;
- record the resolved commit used for graph construction;
- expand include/exclude scope deterministically;
- write a scope file list and exclusion report;
- enforce `max_files` and `max_bytes`;
- reject symlink escapes and unsafe paths;
- keep graph nodes locator-only;
- avoid storing behavioral summaries as factual evidence;
- validate graph output against `schemas/locator-graph.schema.json`;
- validate the graph report against `schemas/graph-report.schema.json`;
- rebuild when commit, scope, or graph schema version changes.

If graphify is enabled for additional registered repos, each source must have explicit include/exclude scope, file/byte limits, graph artifact path, refresh policy, and validation coverage before any graph-complete claim.
