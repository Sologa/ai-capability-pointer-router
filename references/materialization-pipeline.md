# Materialization Pipeline

materialization 有兩條路徑：category/source-scoped local refresh，以及只讀 dry-run planner。local refresh 不再 refresh 全 registry；root 選定 category 後才 refresh 該 category 的 sources，深讀 worktree 仍然是 lazy 的，只在 source card/anchor 選定後進行。

**Current local status:** `scripts/local_refresh_repos.py --category <route_id>` 會處理該 category 的 sources；`--source <source_id>` 會處理單一 source。missing repo 會 clone；existing worktree 會先做 remote HEAD freshness check。若 local commit 已是最新，腳本不 fetch/reset，也不重建 graph。若 remote commit、graph scope、route index 或 graph writer version 改變，才更新 local-only manifest / git_state / route_index / graph artifacts。所有產物都在 git-ignored `temp_artifact/repo_pointer_router_cache/`，不得 push。

**Current planner status:** `scripts/materialize_repo_pointer.py --dry-run` 只輸出計劃；non-dry-run / `--write-cache` 仍明確拒絕執行。`implementation_status: local_refresh_enabled` 指 local refresh script 已啟用，不代表 dry-run planner 可以 write cache。

## Mode

- `pointer_only`: 只保存 source card，不下載 repo。
- `materialize_on_first_use`: category/source 選定後 local refresh；深讀時使用 selected local worktree anchors。
- `materialize_and_graph_on_first_use`: category/source 選定後 local refresh，且在 commit/scope/route index/graph writer version 改變時重建 locator graph output；深讀時使用 selected local worktree anchors / graph locators。
- `manual_only`: 不自動 clone，不自動 graph。

## Required Registry Fields

每個 source 的 `materialization` 必須有：

- `mode`
- `repo_url`
- `implementation_status`
- `default_ref`
- `allowed_refs`
- `pin_policy`
- `update_policy`
- `manifest.path`
- `graph.enabled`
- `graph.scope.include`
- `graph.scope.exclude`
- `max_files`
- `max_bytes`

## Safety

script 不得自動執行 package install、repo scripts、hooks、submodules 或任意 build。graph/index 都是 locator only，不是 evidence。cache 位置維持在 `temp_artifact/repo_pointer_router_cache/`，且必須保持 git-ignored。

local refresh 使用 `git fetch --prune origin main` 加 `checkout -B main origin/main`，功能上等同把 cache 更新到 upstream `main`；文檔中若說 pull/latest，指的是這個 reset-to-origin-main 行為。

## Dry Run

`scripts/materialize_repo_pointer.py --dry-run` 只印出將使用的 manifest / worktree / graph / route index plan，不 clone、不 fetch、不寫 cache。

`--write-cache` 是 planner 的未來寫入模式旗標；目前即使傳入也會拒絕。需要本地 cache 時使用 `scripts/local_refresh_repos.py`。

## Graphify Boundary

`scripts/local_refresh_repos.py` 會重建 deterministic locator graph，並寫入 worktree-local `graphify-out/graph.json`、`graph_report.json` 和人類可讀 `GRAPH_REPORT.md`。docs/papers/images 的 semantic graphify 目前需要 `/graphify` skill / subagents 或未來 non-agent CLI；local refresh 會寫 `graphify-out/needs_semantic_graphify` 標記這個缺口。
