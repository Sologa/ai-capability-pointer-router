# ChatGPT Deep Review Prompt

Use this prompt to ask ChatGPT or another reviewer to review the published repository:

`https://github.com/Sologa/ai-capability-pointer-router`

## Role

You are a strict repository reviewer. Review this repo as a staged Codex skill draft, not as a fully installed runtime skill. Be concrete, source-grounded, and skeptical.

## Repository Intent

The repo implements a three-layer lazy pointer tree for AI capability repositories:

1. Root `SKILL.md` selects a category only.
2. Category routers under `references/category-routers/` select source cards or materialization decisions only.
3. Source cards under `references/source-cards/` select anchors, manifests, route indexes, or graph locators only.

Source cards, route indexes, manifests, and graph outputs are locators, not evidence. Current repo behavior claims must be verified against live or pinned raw source files.

## Review Questions

### 1. Publication Readiness

Assess how far the repo is from being publishable as a reusable public skill.

Check:

- Is `SKILL.md` concise, triggerable, and aligned with Codex skill conventions?
- Are required files present and named predictably?
- Are optional files justified rather than clutter?
- Are dependency, validation, and safety expectations discoverable?
- Are there missing publication basics such as license, README, examples, CI, versioning, release notes, or install instructions?
- Are there any user-facing claims that overstate the repo's maturity?

Return:

- readiness score from 0 to 10;
- blocking fixes before public release;
- important non-blocking fixes;
- optional polish.

### 2. Extensibility

Assess second-layer and third-layer extensibility.

Check:

- Can a new category router be added without editing unrelated files?
- Can a new source card be added without breaking existing routes?
- Does `references/route-registry.yaml` fully drive route/source/card closure?
- Does `validation/validate_router_tree.py` catch orphan routers, orphan cards, bad category IDs, missing source cards, missing anchors, bad materialization fields, and route-index namespace errors?
- Could category/source additions be semi-automated or fully automated from a source manifest?
- What schema changes would make automation easier?

Return:

- extensibility score from 0 to 10;
- concrete workflow for adding a new category;
- concrete workflow for adding a new source;
- what can be automated now;
- what still requires human review.

### 3. Content Alignment

Check whether each source card aligns with its repo identity and role.

Review:

- `agentskills/agentskills`
- `openai/skills`
- `vercel-labs/skills`
- `promptfoo/promptfoo`

For each source:

- Does the summary match the repo's real purpose?
- Do `use_for` and `do_not_use_for` boundaries match the repo?
- Do anchors correspond to plausible files or docs?
- Are authority-level and freshness labels appropriate?
- Are there stale, unsupported, or overconfident claims?
- Are route-index keys and anchors consistent with the card and registry?

Return mismatches as a table with source, file/path, issue, severity, and suggested correction.

### 4. Graph Completeness

Assess graph/index readiness, even though the repo currently has no built graph output.

Check:

- Is graph semantics clearly locator-only?
- Is `promptfoo-promptfoo` graph scope sufficient and not too broad?
- Are deterministic indexes distinguished from semantic graphify output?
- Are graph max file/byte limits reasonable?
- Are graph outputs excluded from publication when rebuildable?
- What would be needed to claim the graph is complete?

Return:

- current graph completeness score from 0 to 10;
- whether graph is intentionally absent or missing;
- minimum graph/index artifacts needed for a stronger version;
- validation checks needed for graph refresh.

### 5. Automation Correctness And Completeness

Review all automation:

- `scripts/materialize_repo_pointer.py`
- `validation/validate_router_tree.py`
- `validation/qa_prompts.md`

Check:

- Does the materialization script correctly refuse unsafe writes in this staged draft?
- Does dry-run expose enough plan fields?
- Are host allowlist and cache path checks sufficient?
- Does validator cover the tree invariant and route/card closure?
- Does validator detect sidecar files, symlinks, unsafe cache paths, bad graph scope, un-namespaced route-index keys, and write-cache drift?
- Are there test cases for extension and adversarial lazy loading?
- What functionality is missing before real clone/fetch/index/materialization can be trusted?

Return:

- automation score from 0 to 10;
- correctness findings;
- missing tests;
- recommended next implementation steps.

### 6. Clone-Backed And Graph-Backed Target Gap

The current repository is intentionally staged and read-only: `--write-cache` is rejected, dry-run plans require `safety.clone=false` and `safety.fetch=false`, and graph/index schemas are contracts only. However, the intended next-stage design may be a clone-backed local cache where all registered repos can be pulled, pinned, indexed, and optionally graphified on explicit use.

Assess this gap directly.

Check:

- Does any wording such as `materialize_on_first_use`, `git_clone_fetch_checkout`, `materialization decision`, `manifest`, or `graph locator` make readers think clone/fetch/cache or graph output already exists?
- Should the registry rename fields like `strategy` to `planned_strategy`, or add `implementation_status: dry_run_only`, to reduce ambiguity?
- If the target is clone-backed local materialization, what exact threat model and controls are required before enabling `--write-cache`?
- What minimum writer behavior is needed: `--source` / `--all`, HTTPS GitHub allowlist, safe refs, resolved commit recording, no hooks, no submodules, no package installs, no repo script execution, symlink rejection, scoped file limits, atomic writes, rollback/cleanup, and cache provenance?
- Should future write-cache artifacts use separate schema versions rather than weakening the current dry-run schema where clone/fetch must be false?
- If graphify is part of the target for every registered repo, should all four sources have explicit graph scope, graph artifact paths, graph refresh policy, and graph validation rules instead of only `promptfoo-promptfoo` having `graph.enabled: true`?
- What tests and validators are required before trusting local cache or graph artifacts: fixture git repos, malicious URLs, unsafe refs, path traversal, symlink escapes, oversized repos, graph scope escape, stale manifest refresh, interrupted writes, and `--require-local-cache` checks?

Return:

- whether the current staged behavior is accurately described;
- whether the clone-backed / graph-backed target is sufficiently specified;
- blocking design changes before implementing `--write-cache`;
- recommended implementation sequence for clone, manifest, route index, and graph support.

## Output Format

Use this structure:

1. Executive verdict
2. Scores table
3. Blocking issues
4. Important non-blocking issues
5. Aspect-by-aspect review
6. File/path-specific findings
7. Recommended next PRs
8. Residual risks

Be direct. Do not assume repository claims are true unless the repo files support them.
