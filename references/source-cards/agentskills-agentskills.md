---
source_id: agentskills-agentskills
category: skill_building
repo: https://github.com/agentskills/agentskills
repo_url: https://github.com/agentskills/agentskills.git
authority_level: canonical_spec_anchor
refresh_sensitivity: high
stale_after_hours: 48
materialization_mode: materialize_on_first_use
implementation_status: local_refresh_enabled
graph_enabled: true
do_not_use_for:
  - production_package_manager
  - behavioral_eval_framework
---

# Source Card: `agentskills/agentskills`

本 card 是 locator，不是 evidence。

## Identity

- `source_id`: `agentskills-agentskills`
- `repo`: `https://github.com/agentskills/agentskills`
- `repo_url`: `https://github.com/agentskills/agentskills.git`
- `authority_level`: `canonical_spec_anchor`
- `refresh_sensitivity`: `high`

## Use For

- Agent Skills directory / `SKILL.md` contract。
- progressive disclosure 與 referenced files。
- client-side skill support。
- spec-vs-implementation boundary。

## Do Not Use For

- production package manager。
- behavior benchmark framework。
- proof that third-party skills are safe。

## Read First

- `README.md`
- `docs/specification.mdx`
- `docs/client-implementation/adding-skills-support.mdx`
- `docs/skill-creation/best-practices.mdx`
- `skills-ref/README.md`

## Route Index / Anchors

這些 anchors 只定位檔案，不直接支撐 factual claim。

- `agentskills-agentskills/spec_contract`
  - `README.md`
  - `docs/specification.mdx`
- `agentskills-agentskills/client_support`
  - `docs/client-implementation/adding-skills-support.mdx`
- `agentskills-agentskills/skill_authoring`
  - `docs/skill-creation/best-practices.mdx`
  - `skills-ref/README.md`

## Materialization

使用 `materialize_on_first_use`。選定 `skill_building` category 或本 source 後，用 `scripts/local_refresh_repos.py --category skill_building` 或 `--source agentskills-agentskills` 將本 repo clone/refresh 到本地 git-ignored cache。clean up-to-date 時不 fetch/reset，也不重建 locator graph；dirty cache 會不 fetch 但 reset/clean 並重建 locator artifacts；commit、scope、route index、graph writer version 或 graph/report content hash 改變時才重建 graphify-out locator artifacts / semantic-needed marker。需要 current spec wording、client behavior 或跨文件比較時，優先讀本地 worktree 對應 raw files；若 cache refresh 失敗，再讀 live upstream raw files 並標明狀態。

Manifest locator: `temp_artifact/repo_pointer_router_cache/repos/agentskills-agentskills/materialization.json`
Local worktree: `temp_artifact/repo_pointer_router_cache/repos/agentskills-agentskills/worktree`
Local graphify output: `temp_artifact/repo_pointer_router_cache/repos/agentskills-agentskills/worktree/graphify-out/`
