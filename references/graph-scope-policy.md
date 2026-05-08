# Graph Scope Policy

Graph artifacts are local-only locator artifacts. They are generated under git-ignored `temp_artifact/` by the invocation refresh path, are not published in the repository, and must not be treated as evidence for upstream behavior.

## Current Status

- `scripts/local_refresh_repos.py` refreshes selected category/source repos and writes worktree-local `graphify-out/` status/artifacts.
- Deterministic locator graph rebuild is automated within the declared scope and budget, and is skipped when commit, scope, route index, and graph writer version are unchanged.
- Docs/papers/images semantic graphify is not context-free in the currently installed graphify package; those files require `/graphify` skill / subagents or a future non-agent graphify CLI.
- No generated graph JSON, graph report, scope expansion, or coverage report is committed or published.
- `schemas/locator-graph.schema.json` and `schemas/graph-report.schema.json` are local artifact contracts.

## Promptfoo Scope

All current sources have `graph.enabled: true` for local invocation refresh. This does not mean every source has a complete semantic graph.

`promptfoo-promptfoo` has the broadest declared scope:

- `site/docs`
- `examples`
- `plugins/promptfoo/skills`

This scope is suitable only for locating documentation, examples, and Promptfoo-bundled skill files. It is not sufficient for current CLI implementation behavior, provider internals, parser behavior, command behavior, or runtime execution claims. For those questions, read live upstream raw files or a local refreshed worktree raw file.

## Future Graph Requirements

Any graph builder or refresh script must:

- operate only on a pinned materialized worktree;
- record the resolved commit used for graph construction;
- expand include/exclude scope deterministically;
- write a scope file list and exclusion report;
- enforce `max_files` and `max_bytes`;
- reject symlink escapes and unsafe paths;
- keep graph nodes locator-only;
- avoid storing behavioral summaries as factual evidence;
- validate graph output against `schemas/locator-graph.schema.json`;
- validate `graphify-out/graph_report.json` against `schemas/graph-report.schema.json`;
- rebuild when commit, scope, route index, or graph writer version changes.

If graphify is enabled for additional registered repos, each source must have explicit include/exclude scope, file/byte limits, graph artifact path, refresh policy, and validation coverage before any graph-complete claim.
