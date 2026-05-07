# AI Capability Pointer Router

Status: staged Codex skill draft. This repository is published for review and iteration; it is not meant to be copied into a runtime skill root without an explicit install decision.

## What It Does

This repo defines a three-layer lazy pointer tree for AI capability sources:

1. `SKILL.md` selects a category.
2. A category router selects a source card or materialization decision.
3. A source card selects anchors, route-index keys, manifests, or graph locators.

Source cards, route indexes, manifests, and graph outputs are locators only. They are not evidence for factual claims. Current behavior claims must be checked against live upstream raw files or a pinned materialized worktree.

## Current Sources

- `agentskills/agentskills`: Agent Skills open format, spec, docs, and reference SDK pointers.
- `openai/skills`: Codex skill catalog, skill authoring, install, and OpenAI skill metadata pointers.
- `vercel-labs/skills`: `npx skills` CLI, source parsing, install/update, lock-file, and cross-agent skill workflow pointers.
- `promptfoo/promptfoo`: LLM eval, provider setup, redteam, and CI regression pointers.

The registry source of truth is `references/route-registry.yaml`.

## Validate

```sh
python -m pip install -r requirements.txt
python validation/validate_router_tree.py .
python -m unittest discover -s tests
```

For Codex skill-shape validation:

```sh
python /Users/xjp/.codex/skills/.system/skill-creator/scripts/quick_validate.py .
```

## Dry-Run Materialization Planner

The current planner is read-only. It prints the declared manifest, worktree, route-index, and graph plan, but it does not clone, fetch, install packages, run hooks, run repo scripts, or write cache.

```sh
python scripts/materialize_repo_pointer.py \
  --registry references/route-registry.yaml \
  --source promptfoo-promptfoo \
  --dry-run \
  --offline-ok
```

`--write-cache` is intentionally rejected until clone/fetch/index/write-cache behavior has a separate reviewed implementation.

## Add a Category

1. Add a route to `references/route-registry.yaml`.
2. Add `references/category-routers/<route_id>.md`.
3. Add at least one source under that route.
4. Update `SKILL.md` category bullets.
5. Run the validator and tests.

## Add a Source

1. Add the source under `sources` in `references/route-registry.yaml`.
2. Add it to exactly one route's `sources` list.
3. Add `references/source-cards/<source_id>.md`.
4. Keep all route-index keys namespaced as `<source_id>/<local_route>`.
5. Use exact raw-file anchors when possible; if a docs route has no single raw file, point to the concrete leaf pages actually needed.
6. Run dry-run materialization for the new source and then run the validator and tests.

## Publication Gaps

This draft still needs an owner-selected `LICENSE` before it should be treated as publicly reusable. Graph artifacts are intentionally absent; graph semantics are currently locator-only contracts, not a built graph release.
