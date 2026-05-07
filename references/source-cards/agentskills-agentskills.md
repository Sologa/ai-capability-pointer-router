---
source_id: agentskills-agentskills
category: skill_building
---

# Source Card: `agentskills/agentskills`

本 card 是 locator，不是 evidence。

## Identity

- `source_id`: `agentskills-agentskills`
- `repo`: <https://github.com/agentskills/agentskills>
- `repo_url`: <https://github.com/agentskills/agentskills.git>
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

使用 `materialize_on_first_use`。graph 關閉。只有需要 current spec wording、client behavior 或跨文件比較時才 materialize。

Manifest locator: `temp_artifact/repo_pointer_router_cache/repos/agentskills-agentskills/materialization.json`
