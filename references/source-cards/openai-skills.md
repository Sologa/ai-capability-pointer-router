---
source_id: openai-skills
category: skill_building
repo: https://github.com/openai/skills
repo_url: https://github.com/openai/skills.git
authority_level: official_codex_skill_catalog
refresh_sensitivity: high
stale_after_hours: 48
materialization_mode: materialize_on_first_use
implementation_status: dry_run_only
graph_enabled: false
do_not_use_for:
  - sole_current_openai_product_authority
  - general_cross_agent_installer
---

# Source Card: `openai/skills`

本 card 是 locator，不是 evidence。OpenAI 產品 current behavior 必須以 official docs 或 live source 更新確認。

## Identity

- `source_id`: `openai-skills`
- `repo`: <https://github.com/openai/skills>
- `repo_url`: <https://github.com/openai/skills.git>
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

使用 `materialize_on_first_use`。這是 declarative only；current implementation 只做 dry-run planning，不 clone、fetch、checkout 或 write cache。graph 關閉。需要 current example path、官方 skill pattern 或多檔比較時才 materialize。

Manifest locator: `temp_artifact/repo_pointer_router_cache/repos/openai-skills/materialization.json`
