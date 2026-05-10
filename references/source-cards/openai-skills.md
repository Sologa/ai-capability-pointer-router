---
source_id: openai-skills
category: skill_building
repo: https://github.com/openai/skills
repo_url: https://github.com/openai/skills.git
authority_level: official_codex_skill_catalog
refresh_sensitivity: high
stale_after_hours: 48
materialization_mode: materialize_on_first_use
implementation_status: local_refresh_enabled
graph_enabled: true
do_not_use_for:
  - sole_current_openai_product_authority
  - general_cross_agent_installer
---

# Source Card: `openai/skills`

本 card 是 locator，不是 evidence。OpenAI 產品 current behavior 必須以 official docs 或 live source 更新確認。

## Identity

- `source_id`: `openai-skills`
- `repo`: `https://github.com/openai/skills`
- `repo_url`: `https://github.com/openai/skills.git`
- `authority_level`: `official_codex_skill_catalog`
- `refresh_sensitivity`: `high`

## Use For

- Codex skill anatomy。
- `SKILL.md` concise body、`references/`、`scripts/`、`assets/`。
- `agents/openai.yaml` metadata pattern。
- system skill examples such as `skill-creator` / `skill-installer`。

## Do Not Use For

- sole current OpenAI product/API authority。
- cross-agent installer design。
- eval / benchmarking framework。

## Read First

- `README.md`
- `skills/.system/skill-creator/SKILL.md`
- `skills/.system/skill-installer/SKILL.md`
- `skills/.system/skill-creator/references/openai_yaml.md`
- `skills/.curated/openai-docs/SKILL.md`

## Route Index / Anchors

這些 anchors 只定位檔案，不直接支撐 factual claim。OpenAI product current behavior 仍需 official docs 或 live source。

- `openai-skills/skill_creation`
  - `README.md`
  - `skills/.system/skill-creator/SKILL.md`
- `openai-skills/installation`
  - `skills/.system/skill-installer/SKILL.md`
- `openai-skills/openai_yaml`
  - `skills/.system/skill-creator/references/openai_yaml.md`
- `openai-skills/openai_docs_skill`
  - `skills/.curated/openai-docs/SKILL.md`

## Materialization

使用 `materialize_on_first_use`。選定 `skill_building` category 或本 source 後，用 `scripts/local_refresh_repos.py --category skill_building` 或 `--source openai-skills` 將本 repo clone/refresh 到本地 git-ignored cache。clean up-to-date 時不 fetch/reset，也不重建 locator graph；dirty cache 會不 fetch 但 reset/clean 並重建 locator artifacts；commit、scope、route index、graph writer version 或 graph/report content hash 改變時才重建 graphify-out locator artifacts / semantic-needed marker。需要 current example path、官方 skill pattern 或多檔比較時，優先讀本地 worktree 對應 raw files；OpenAI 產品 current behavior 仍需搭配 official docs。

Manifest locator: `temp_artifact/repo_pointer_router_cache/repos/openai-skills/materialization.json`
Local worktree: `temp_artifact/repo_pointer_router_cache/repos/openai-skills/worktree`
Local graphify output: `temp_artifact/repo_pointer_router_cache/repos/openai-skills/worktree/graphify-out/`
