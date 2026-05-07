# AI Capability Pointer Router

Status: staged Codex skill draft. This repository is published for review and iteration; it is not meant to be copied into a runtime skill root without an explicit install decision.

License: Apache-2.0.

## What It Does

This repo defines a three-layer lazy pointer tree for AI capability sources:

1. `SKILL.md` selects a category.
2. A category router selects a source card or materialization decision.
3. A source card selects anchors, route-index keys, manifests, or graph locators.

Source cards, route indexes, manifests, and graph outputs are locators only. They are not evidence for factual claims. Current behavior claims must be checked against live upstream raw files or a locally refreshed materialized worktree.

## Current Sources

- `agentskills/agentskills`: Agent Skills open format, spec, docs, and reference SDK pointers.
- `openai/skills`: Codex skill catalog, skill authoring, install, and OpenAI skill metadata pointers.
- `vercel-labs/skills`: `npx skills` CLI, source parsing, install/update, lock-file, and cross-agent skill workflow pointers.
- `promptfoo/promptfoo`: LLM eval, provider setup, redteam, and CI regression pointers.

The registry source of truth is `references/route-registry.yaml`.

## Contract Files

- `schemas/route-registry.schema.json`
- `schemas/materialization-plan.schema.json`
- `schemas/anchor-check-report.schema.json`
- `schemas/materialization-manifest.schema.json`
- `schemas/route-index-artifact.schema.json`
- `schemas/locator-graph.schema.json`
- `schemas/graph-report.schema.json`

The Python validator is still the authoritative local check for cross-file closure and safety invariants. It also applies the registry and dry-run plan schemas as a second validation layer. The graph/index schemas describe local-only artifacts under git-ignored `temp_artifact/`; committed repo contents still do not include generated worktrees or graph outputs.

Design boundary references:

- `references/graph-scope-policy.md` explains current graph scope limits and the semantic graphify boundary.
- `references/materialization-writer-design.md` defines the local refresh contract and the boundary around the still-disabled `--write-cache` planner mode.

## Validate

```sh
python -m pip install -r requirements.txt
python validation/validate_router_tree.py .
python -m unittest discover -s tests
```

Optional: run your local Codex or Agent Skills shape validator if it is installed. The portable validator for this repo is `python validation/validate_router_tree.py .`.

## Invocation Local Refresh

When this skill is invoked, the first operational step is to refresh all registered repos locally:

```sh
python scripts/local_refresh_repos.py \
  --registry references/route-registry.yaml \
  --all
```

This command clones missing repos, fetches/prunes `origin main`, resets each local worktree to `origin/main`, writes local-only manifests and route indexes, and rebuilds graphify outputs that can run without semantic subagents. Outputs stay under:

```text
temp_artifact/repo_pointer_router_cache/repos/<source_id>/
  materialization.json
  git_state.json
  route_index.json
  worktree/
    graphify-out/
```

`temp_artifact/` and `graphify-out/` are git-ignored. These local clones and graph outputs must not be committed or pushed.

After refresh, agents should read selected raw files from `temp_artifact/repo_pointer_router_cache/repos/<source_id>/worktree/` before falling back to live upstream raw files. If a refresh fails, answer from live upstream only when explicitly checked, and state the local refresh failure.

Graphify boundary: the local refresh script rebuilds a deterministic graphify locator graph through the installed graphify Python package. Full semantic graphify for docs/papers/images still requires `/graphify` skill execution with subagents or a future non-agent graphify CLI; the script writes `graphify-out/needs_semantic_graphify` when that semantic pass is still needed.

## Dry-Run Materialization Planner

The planner remains read-only. It prints the declared manifest, worktree, route-index, and graph plan, but it does not clone, fetch, install packages, run hooks, run repo scripts, or write cache. Use `scripts/local_refresh_repos.py --all` for the accepted local-only refresh path.

```sh
python scripts/materialize_repo_pointer.py \
  --registry references/route-registry.yaml \
  --source promptfoo-promptfoo \
  --dry-run \
  --offline-ok
```

`--write-cache` is intentionally rejected on the dry-run planner. The combined `--dry-run --write-cache` form is also rejected. Registry sources use `implementation_status: local_refresh_enabled`, meaning local refresh is implemented by `scripts/local_refresh_repos.py`, not by the planner's disabled write-cache mode.

## Optional Upstream Anchor Check

The default validator is offline. To check whether `read_first` and route-index file anchors exist on the upstream GitHub repos:

```sh
python validation/check_upstream_anchors.py references/route-registry.yaml --ref main
```

This command performs network reads against GitHub raw URLs and, in JSON mode, attempts to include resolved commit and blob SHA metadata from the GitHub API. Treat the output as review-time locator metadata, not as a replacement for reading raw source files before making factual claims.

## Add a Category

1. Add a route to `references/route-registry.yaml`.
2. Add `references/category-routers/<route_id>.md`.
3. Add router frontmatter with `route_id` and `sources` matching the registry route exactly.
4. Add at least one source under that route.
5. Update `SKILL.md` category bullets.
6. Run the validator and tests.

## Add a Source

1. Add the source under `sources` in `references/route-registry.yaml`.
2. Add it to exactly one route's `sources` list.
3. Add `references/source-cards/<source_id>.md`.
4. Add source-card frontmatter for identity, freshness, materialization mode, implementation status, graph flag, and `do_not_use_for`; it must mirror the registry.
5. Keep all route-index keys namespaced as `<source_id>/<local_route>`.
6. Use exact raw-file anchors when possible; if a docs route has no single raw file, point to the concrete leaf pages actually needed.
7. Add graph scope for the local refresh path.
8. Run dry-run materialization for the new source, run local refresh for that source, then run the validator and tests.

## Publication Boundaries

This repo is licensed under Apache-2.0 for reuse, review, and iteration. It is still not a runtime-installed skill by default. Local worktrees and graph outputs are intentionally absent from commits; graph semantics are locator-only and do not imply a complete semantic graph release.
