# AI Capability Pointer Router / Repo Taxonomy Template

Status: staged Codex skill draft. This repository is published for review and iteration; it is not meant to be copied into a runtime skill root without an explicit install decision.

License: Apache-2.0.

## What It Does

This repo defines a three-layer lazy pointer tree for a repository taxonomy profile. The committed profile routes AI capability sources, and the same contract can be copied into a different Codex skill for paper + repo taxonomies.

1. `SKILL.md` selects a category.
2. A category router selects a source card or materialization decision.
3. A source card selects anchors, route-index keys, manifests, or graph locators.

Source cards, route indexes, manifests, and graph outputs are locators only. They are not evidence for factual claims. Current behavior claims must be checked against live upstream raw files or a locally refreshed materialized worktree.

## Seed AI Capability Profile

- `agentskills/agentskills`: Agent Skills open format, spec, docs, and reference SDK pointers.
- `openai/skills`: Codex skill catalog, skill authoring, install, and OpenAI skill metadata pointers.
- `vercel-labs/skills`: `npx skills` CLI, source parsing, install/update, lock-file, and cross-agent skill workflow pointers.
- `promptfoo/promptfoo`: LLM eval, provider setup, redteam, and CI regression pointers.

The registry source of truth is `references/route-registry.yaml`.

The registry now declares an explicit `profile` block. Treat the current `ai_capability` profile as a working seed, not as the only valid taxonomy. A paper + repo router should replace the profile, routes, source cards, and `SKILL.md` category list while keeping the router invariants and validation contract.

Current first-class materialization support is GitHub-repo-first: HTTPS GitHub repos, `main` default refs, safe relative file anchors, and local-only cache outputs. Paper PDFs, arXiv pages, Zenodo records, Hugging Face repos, GitLab repos, or local corpora can still be described in prose, but they are not first-class materialized sources until the schemas and scripts are extended deliberately.

## Template Library

Use `templates/paper-repo-taxonomy/` to create a Codex version of this router for a new paper + repo taxonomy. The templates use placeholder markers like `<route_id>`, `<source_id>`, `<repo_url>`, and `<checked_paths>`. Replace every placeholder before review.

Recommended use:

1. Copy this repo or create a new repo from it.
2. Rename the skill identity in `SKILL.md` and `agents/openai.yaml`.
3. Replace `references/route-registry.yaml` profile/routes/sources with the template blocks.
4. Create `references/category-routers/<route_id>.md` from the category router template.
5. Create `references/source-cards/<source_id>.md` from the source card template.
6. Run the validator and tests before treating the taxonomy as ready.

For paper + repo work, common route units are paper family, method family, benchmark family, implementation role, or evaluation role. Common source units are public GitHub repos tied to a paper, benchmark, data release, or reference implementation. Do not force non-GitHub paper artifacts into the repo materializer without extending the contract first.

The registry schema allows optional paper-facing metadata on each source: `paper`, `artifact_role`, `topic_tags`, `question_types`, `claim_scope`, `preferred_evidence_order`, and `paired_assets`. These fields make a paper/repo pairing explicit while keeping the current materializer scoped to GitHub repo anchors.

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

- `references/template-authoring.md` explains how to instantiate a new taxonomy profile from the templates.
- `references/graph-scope-policy.md` explains current graph scope limits and the semantic graphify boundary.
- `references/materialization-writer-design.md` defines the local refresh contract and the boundary around the still-disabled `--write-cache` planner mode.

## How It Is Wired

```text
repo-root/
|- SKILL.md
|- agents/openai.yaml
|- references/
|  |- route-registry.yaml
|  |- category-routers/<route_id>.md
|  |- source-cards/<source_id>.md
|  |- template-authoring.md
|- schemas/
|- scripts/
|  |- local_refresh_repos.py
|  |- materialize_repo_pointer.py
|- validation/
|- tests/
|- templates/paper-repo-taxonomy/
|- temp_artifact/repo_pointer_router_cache/   # git-ignored local outputs
```

## Validate

```sh
python3 -m pip install -r requirements.txt
python3 validation/validate_router_tree.py .
python3 -m unittest discover -s tests
```

Optional: run your local Codex or Agent Skills shape validator if it is installed. The portable validator for this repo is `python3 validation/validate_router_tree.py .`.

## Scoped Local Refresh

The runtime path is category-scoped, not all-source. After the root selects a category, refresh only that category's sources:

```sh
python3 scripts/local_refresh_repos.py \
  --registry references/route-registry.yaml \
  --category skill_building
```

For one repo, use the narrower source-scoped path:

```sh
python3 scripts/local_refresh_repos.py \
  --registry references/route-registry.yaml \
  --source agentskills-agentskills
```

The script clones missing repos. For an existing worktree, it first checks remote HEAD. If the recorded local commit is current and the cache is clean, it skips fetch/reset; if the local cache is dirty, it resets/cleans without fetching. Graph artifacts are skipped only when the commit, graph scope, route index, graph writer version, and stored graph/report content hashes are unchanged. Outputs stay under:

```text
temp_artifact/repo_pointer_router_cache/repos/<source_id>/
  materialization.json
  git_state.json
  route_index.json
  worktree/
    graphify-out/
      graph.json
      graph_report.json
      graph_meta.json
```

`temp_artifact/` and `graphify-out/` are git-ignored. These local clones and graph outputs must not be committed or pushed.

After refresh, agents should read selected raw files from `temp_artifact/repo_pointer_router_cache/repos/<source_id>/worktree/` before falling back to live upstream raw files. Local refresh validates `read_first` and route-index anchors as regular in-worktree files before treating them as locators. If a category refresh partially fails, successful source results are still merged into the manifest index, and the command reports structured failures with a non-zero exit code. If a refresh fails, answer from live upstream only when explicitly checked, and state the local refresh failure.

Graphify boundary: the local refresh script writes deterministic locator graph artifacts under `graphify-out/`. These artifacts are schema-compatible locators, not semantic evidence. Full semantic graphify for docs/papers/images still requires `/graphify` skill execution with subagents or a future non-agent graphify CLI; the script writes `graphify-out/needs_semantic_graphify` when that semantic pass is still needed.

## Dry-Run Materialization Planner

The planner remains read-only. It prints the declared manifest, worktree, route-index, and graph plan, but it does not clone, fetch, install packages, run hooks, run repo scripts, or write cache. Use `scripts/local_refresh_repos.py --category <route_id>` or `--source <source_id>` for the accepted local-only refresh path.

```sh
python3 scripts/materialize_repo_pointer.py \
  --registry references/route-registry.yaml \
  --source promptfoo-promptfoo \
  --dry-run \
  --offline-ok
```

`--write-cache` is intentionally rejected on the dry-run planner. The combined `--dry-run --write-cache` form is also rejected. Registry sources use `implementation_status: local_refresh_enabled`, meaning local refresh is implemented by `scripts/local_refresh_repos.py`, not by the planner's disabled write-cache mode.

## Optional Upstream Anchor Check

The default validator is offline. To check whether `read_first` and route-index file anchors exist on the upstream GitHub repos:

```sh
python3 validation/check_upstream_anchors.py references/route-registry.yaml --ref main
```

This command performs network reads against GitHub raw URLs and, in JSON mode, attempts to include resolved commit and blob SHA metadata from the GitHub API. Treat the output as review-time locator metadata, not as a replacement for reading raw source files before making factual claims.

## Add a Category

1. Start from `templates/paper-repo-taxonomy/category-router.md.tmpl` or an existing category router.
2. Add a route to `references/route-registry.yaml`.
3. Add `references/category-routers/<route_id>.md`.
4. Add router frontmatter with `route_id` and `sources` matching the registry route exactly.
5. Add at least one source under that route.
6. Update `SKILL.md` category bullets.
7. Run the validator and tests.

## Add a Source

1. Start from `templates/paper-repo-taxonomy/route-registry-source.yaml.tmpl` and `templates/paper-repo-taxonomy/source-card.md.tmpl`.
2. Add the source under `sources` in `references/route-registry.yaml`.
3. Add it to exactly one route's `sources` list.
4. Add `references/source-cards/<source_id>.md`.
5. Add source-card frontmatter for identity, freshness, materialization mode, implementation status, graph flag, and `do_not_use_for`; it must mirror the registry.
6. Keep all route-index keys namespaced as `<source_id>/<local_route>`.
7. Use exact raw-file anchors when possible; if a docs route has no single raw file, point to the concrete leaf pages actually needed.
8. Add graph scope for the local refresh path.
9. Run dry-run materialization for the new source, run local refresh for that source, then run the validator and tests.

## Expansion Quality Bar

- Category routers choose only source cards or materialization decisions.
- Category routers must not leak raw upstream file paths or route-index keys.
- Source cards and route indexes are locators, not evidence.
- `last_verified.checked_paths` must exactly match `read_first` plus route-index anchors.
- Graph scope must be bounded and must not include secrets, generated outputs, package installs, or broad repo roots without reason.
- `temp_artifact/`, materialized worktrees, manifests, and `graphify-out/` must stay uncommitted.
- Run `python3 validation/validate_router_tree.py .` and `python3 -m unittest discover -s tests` before review.

## Publication Boundaries

This repo is licensed under Apache-2.0 for reuse, review, and iteration. It is still not a runtime-installed skill by default. Local worktrees and graph outputs are intentionally absent from commits; graph semantics are locator-only and do not imply a complete semantic graph release.
