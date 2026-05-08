---
source_id: vercel-labs-skills
category: skill_building
repo: https://github.com/vercel-labs/skills
repo_url: https://github.com/vercel-labs/skills.git
authority_level: cross_agent_skill_cli
refresh_sensitivity: high
stale_after_hours: 48
materialization_mode: materialize_on_first_use
implementation_status: local_refresh_enabled
graph_enabled: true
do_not_use_for:
  - skill_spec_authority
  - benchmark_framework
---

# Source Card: `vercel-labs/skills`

本 card 是 locator，不是 evidence。

## Identity

- `source_id`: `vercel-labs-skills`
- `repo`: <https://github.com/vercel-labs/skills>
- `repo_url`: <https://github.com/vercel-labs/skills.git>
- `authority_level`: `cross_agent_skill_cli`
- `refresh_sensitivity`: `high`

## Use For

- cross-agent skill discovery。
- install / update / remove workflow。
- source parsing、lock file、skill recommendation policy。
- local / GitHub / GitLab source handling。

## Do Not Use For

- canonical skill spec。
- benchmark framework。
- proof that an installed third-party skill is safe。

## Read First

- `README.md`
- `AGENTS.md`
- `skills/find-skills/SKILL.md`
- `src/cli.ts`
- `src/add.ts`
- `src/installer.ts`
- `src/source-parser.ts`
- `src/skill-lock.ts`
- `src/skills.ts`

## Route Index / Anchors

這些 anchors 只定位檔案，不直接支撐 factual claim。

- `vercel-labs-skills/discovery_installation`
  - `README.md`
  - `skills/find-skills/SKILL.md`
  - `src/cli.ts`
  - `src/add.ts`
  - `src/installer.ts`
- `vercel-labs-skills/source_parsing`
  - `src/source-parser.ts`
- `vercel-labs-skills/lock_update`
  - `src/cli.ts`
  - `src/skill-lock.ts`
  - `src/skills.ts`

## Materialization

使用 `materialize_on_first_use`。選定 `skill_building` category 或本 source 後，用 `scripts/local_refresh_repos.py --category skill_building` 或 `--source vercel-labs-skills` 將本 repo clone/refresh 到本地 git-ignored cache。clean up-to-date 時不 fetch/reset，也不重建 locator graph；dirty cache 會不 fetch 但 reset/clean 並重建 locator artifacts；commit、scope、route index、graph writer version 或 graph/report content hash 改變時才重建 graphify-out locator artifacts / semantic-needed marker。需要 CLI/source parsing/lock/update 行為時，優先讀本地 worktree 的 raw files 和 `graphify-out/` locators。

Manifest locator: `temp_artifact/repo_pointer_router_cache/repos/vercel-labs-skills/materialization.json`
Local worktree: `temp_artifact/repo_pointer_router_cache/repos/vercel-labs-skills/worktree`
Local graphify output: `temp_artifact/repo_pointer_router_cache/repos/vercel-labs-skills/worktree/graphify-out/`
