---
source_id: vercel-labs-skills
category: skill_building
repo: https://github.com/vercel-labs/skills
repo_url: https://github.com/vercel-labs/skills.git
authority_level: cross_agent_skill_cli
refresh_sensitivity: high
stale_after_hours: 48
materialization_mode: materialize_on_first_use
implementation_status: dry_run_only
graph_enabled: false
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

使用 `materialize_on_first_use`。這是 declarative only；current implementation 只做 dry-run planning，不 clone、fetch、checkout 或 write cache。graph 關閉。需要 CLI/source parsing/lock/update 行為時才 materialize。

Manifest locator: `temp_artifact/repo_pointer_router_cache/repos/vercel-labs-skills/materialization.json`
