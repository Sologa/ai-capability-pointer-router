---
source_id: promptfoo-promptfoo
category: eval_benchmark
repo: https://github.com/promptfoo/promptfoo
repo_url: https://github.com/promptfoo/promptfoo.git
authority_level: eval_redteam_framework
refresh_sensitivity: very_high
stale_after_hours: 24
materialization_mode: materialize_and_graph_on_first_use
implementation_status: local_refresh_enabled
graph_enabled: true
do_not_use_for:
  - production_observability_without_trace_system
  - unversioned_model_comparison_claims
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

使用 `materialize_and_graph_on_first_use`。選定 `eval_benchmark` category 或本 source 後，用 `scripts/local_refresh_repos.py --category eval_benchmark` 或 `--source promptfoo-promptfoo` 將本 repo clone/refresh 到本地 git-ignored cache。up-to-date 時不 fetch/reset，也不重建 locator graph；commit、scope、route index 或 graph writer version 改變時才重建 graphify-out locator artifacts / semantic-needed marker。graph scope 僅限 `site/docs`、`examples`、`plugins/promptfoo/skills`，且 graph 仍是 locator only。需要 eval/redteam/provider/CI current behavior 時，優先讀本地 worktree 的 raw files 和 `graphify-out/` locators。

Manifest locator: `temp_artifact/repo_pointer_router_cache/repos/promptfoo-promptfoo/materialization.json`
Local worktree: `temp_artifact/repo_pointer_router_cache/repos/promptfoo-promptfoo/worktree`
Local graphify output: `temp_artifact/repo_pointer_router_cache/repos/promptfoo-promptfoo/worktree/graphify-out/`
