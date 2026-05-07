---
source_id: promptfoo-promptfoo
category: eval_benchmark
---

# Source Card: `promptfoo/promptfoo`

本 card 是 locator，不是 evidence。Promptfoo 是大型活躍 repo；current behavior 必須 refresh 或使用 pinned manifest。

## Identity

- `source_id`: `promptfoo-promptfoo`
- `repo`: <https://github.com/promptfoo/promptfoo>
- `repo_url`: <https://github.com/promptfoo/promptfoo.git>
- `authority_level`: `eval_redteam_framework`
- `refresh_sensitivity`: `very_high`

## Use For

- prompt/model/provider eval。
- agent / skill output eval suites when Promptfoo target/provider wiring is configured。
- redteam setup / run workflow。
- CI regression 與 eval artifact triage。

## Do Not Use For

- production observability by itself。
- unversioned model quality claims。
- running untrusted eval configs with secrets。

## Read First

- `README.md`
- `plugins/promptfoo/skills/promptfoo-evals/SKILL.md`
- `plugins/promptfoo/skills/promptfoo-redteam-setup/SKILL.md`
- `plugins/promptfoo/skills/promptfoo-redteam-run/SKILL.md`
- `plugins/promptfoo/skills/promptfoo-provider-setup/SKILL.md`

## Route Index / Anchors

這些 anchors 只定位檔案，不直接支撐 factual claim。Promptfoo current behavior 必須 refresh 或使用 pinned raw source。

- `promptfoo-promptfoo/eval_basics`
  - `site/docs/getting-started.md`
  - `site/docs/configuration/guide.md`
  - `plugins/promptfoo/skills/promptfoo-evals/SKILL.md`
- `promptfoo-promptfoo/redteam`
  - `site/docs/red-team/index.md`
  - `plugins/promptfoo/skills/promptfoo-redteam-setup/SKILL.md`
  - `plugins/promptfoo/skills/promptfoo-redteam-run/SKILL.md`
- `promptfoo-promptfoo/provider_setup`
  - `plugins/promptfoo/skills/promptfoo-provider-setup/SKILL.md`
  - `site/docs/providers/index.md`
  - `site/docs/usage/command-line.md`
- `promptfoo-promptfoo/ci_regression`
  - `site/docs/integrations/ci-cd.md`
  - `site/docs/integrations/github-action.md`
  - `site/docs/usage/command-line.md`

## Materialization

使用 `materialize_and_graph_on_first_use`。目前這只是 locator plan，不是已實作的 clone/fetch/graph action。graph scope 僅限 `site/docs`、`examples`、`plugins/promptfoo/skills`，且 graph 仍是 locator only。

Manifest locator: `temp_artifact/repo_pointer_router_cache/repos/promptfoo-promptfoo/materialization.json`
