# Template Authoring Guide

This repo is a staged Codex skill draft with one committed seed profile: `ai_capability`. The reusable part is the router contract, not the specific four sources.

Use this guide when turning the repo into another paper + repo taxonomy router.

## Keep These Invariants

- Root `SKILL.md` selects only a taxonomy route.
- A category router selects only a source card or materialization decision.
- A source card selects only anchors, route-index keys, manifests, local worktree paths, or graph locators.
- Raw upstream files are opened only at the final evidence step.
- Registry entries, source cards, route indexes, manifests, and graph outputs are locators only.
- Local refresh outputs stay under git-ignored `temp_artifact/repo_pointer_router_cache/`.
- The dry-run planner stays read-only; `--write-cache` is intentionally disabled there.

## What To Replace For A New Profile

1. `SKILL.md` frontmatter, title, trigger wording, and `## Category` bullets.
2. `agents/openai.yaml` display text and default prompt.
3. The `profile` block in `references/route-registry.yaml`.
4. Every route under `routes`.
5. Every source under `sources`.
6. Files under `references/category-routers/`.
7. Files under `references/source-cards/`.

Do not leave seed AI-capability routes or source cards in a paper + repo profile unless they are intentionally part of that new taxonomy.

## Paper + Repo Taxonomy Shape

A paper + repo taxonomy should usually route by the user's intent rather than by a flat paper list. Useful route units include:

- method family, such as `taxonomy_generation`
- paper family, such as `survey_generation`
- benchmark or dataset family, such as `taxonomy_benchmarks`
- implementation role, such as `reference_implementations`
- evaluation role, such as `metrics_and_judges`

Each source is currently a GitHub repository. Put paper identity in source prose and source-card wording, then use raw repo files as anchors. Examples:

- paper repository README, docs, scripts, prompt files, or evaluation code
- benchmark release files committed to the repo
- paper-specific reproduction notebooks or configs
- source code paths that implement an algorithm described in the paper

The registry schema also allows optional paper-facing source metadata. If these fields are present, they are validated more strictly than free prose:

- `paper`: paper id, title, citation, and URI.
- `artifact_role`: one of `paper_code_repo`, `benchmark_release`, `reference_implementation`, or `secondary_tooling`.
- `topic_tags`: routing hints for the source.
- `question_types`: one or more supported question types such as `implementation_detail`, `benchmark_setup`, or `method_mapping`.
- `claim_scope`: what claims the source can support after raw-file verification.
- `preferred_evidence_order`: validated evidence steps such as `local_refreshed_worktree` and `live_upstream_raw_file`.
- `paired_assets`: non-materialized paper pointers and materialized GitHub repo pointers that belong together.

These fields describe the taxonomy. They do not change the current materializer, which still refreshes only GitHub repositories.

## Current Materialization Limits

The scripts currently validate and refresh only HTTPS GitHub repositories with `main` as the default branch. This is deliberate. Do not represent a PDF-only paper, arXiv landing page, Zenodo record, Hugging Face repo, GitLab repo, or local folder as a first-class materialized source until the schemas, validator, materializer, local refresh script, and tests are extended together.

If a taxonomy needs those artifacts before the implementation exists, mention them only as non-materialized context in source-card prose and keep factual claims tied to raw files that were actually read.

## Expansion Workflow

1. Copy template blocks from `templates/paper-repo-taxonomy/`.
2. Replace every `<placeholder>`.
3. Add the route to `references/route-registry.yaml`.
4. Add the category router file and make its frontmatter match the route exactly.
5. Add each source block under `sources` and list the source under exactly one route.
6. Add the source card and make its frontmatter mirror the registry exactly.
7. Keep all route-index keys namespaced as `<source_id>/<local_route>`.
8. Keep `last_verified.checked_paths` exactly equal to the union of `read_first` and route-index anchors.
9. Run:

```sh
python3 validation/validate_router_tree.py .
python3 -m unittest discover -s tests
```

When anchors change, also run:

```sh
python3 validation/check_upstream_anchors.py references/route-registry.yaml --ref main
```

## Review Checklist

- No placeholder remains.
- `SKILL.md` category bullets match registry routes exactly.
- Category router files match registry routes exactly.
- Source-card filenames match source ids exactly.
- Category routers do not contain raw upstream anchor paths.
- Source cards explicitly state locator/evidence boundaries.
- `do_not_use_for` says what the source should not answer.
- Graph scope is bounded and excludes generated outputs, secrets, package directories, and broad repo roots unless justified.
- No `temp_artifact/`, local worktree, manifest, graph output, or reference clone artifact is committed.
