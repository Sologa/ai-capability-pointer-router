# Materialization Pipeline

materialization 是明確升級步驟，不是預設行為。長期目標是用 deterministic script 產生 pinned snapshot、manifest、route index 或 scoped graph locator，避免主 agent 手動處理整個 clone/fetch/index 流程。

**Current staged status:** 本 draft 目前只提供 dry-run planner。`scripts/materialize_repo_pointer.py --dry-run` 只輸出計劃；non-dry-run / `--write-cache` 目前明確拒絕執行。真正 clone/fetch/index/write cache 必須另行實作與審查。

Registry 中每個 source 的 `implementation_status` 必須是 `dry_run_only`。只要這個值存在，`materialize_on_first_use` / `materialize_and_graph_on_first_use` 都只能解讀為 declarative future mode，不代表已經能 clone、fetch、checkout、write cache 或 graphify。

## Mode

- `pointer_only`: 只保存 source card，不下載 repo。
- `materialize_on_first_use`: 未來明確需要深讀時 clone/fetch/checkout 並寫 manifest；目前只 dry-run planning。
- `materialize_and_graph_on_first_use`: 未來明確需要深讀時 materialize，並對 declared scope 建 locator index / graph；目前只 dry-run planning。
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

script 不得自動執行 package install、repo scripts、hooks、submodules 或任意 build。graph/index 都是 locator only，不是 evidence。cache 位置維持在 `temp_artifact/repo_pointer_router_cache/`，但本 staged draft 不會主動寫入 cache。

## Dry Run

`scripts/materialize_repo_pointer.py --dry-run` 只印出將使用的 manifest / worktree / graph / route index plan，不 clone、不 fetch、不寫 cache。

`--write-cache` 是未來寫入模式的顯式旗標；目前即使傳入也會拒絕，避免 agent 誤以為 staged draft 已經能建立 pinned snapshot。
