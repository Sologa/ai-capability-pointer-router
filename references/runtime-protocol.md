# Runtime Protocol

這份 staged pack 的核心是三層 tree pointer，而不是大型知識庫。

## 三層規則

0. Invocation refresh: 每次本 skill 被 invoke，先執行 `python scripts/local_refresh_repos.py --registry references/route-registry.yaml --all`。
1. Root `SKILL.md`: 只能選 category。
2. Category router: 只能選 source card 或 materialization decision。
3. Source card: 只能選 anchor、manifest、route index、local worktree 或 graph locator。
4. Raw repo file: 只有最後一步才讀，而且必須有明確需求；優先讀 local refreshed worktree。

## Lazy Loading

預設讀取集合：

- `SKILL.md`
- selected `references/category-routers/<route_id>.md`
- selected `references/source-cards/<source_id>.md`
- selected local manifest / git state / route index / `graphify-out/` status under `temp_artifact/repo_pointer_router_cache/repos/<source_id>/`

不得因為 card 裡列了 anchor paths 就自動深讀。以下情境才升級：

- repo behavior / API / CLI / current facts
- cross-file evidence
- 使用者要求 latest/current
- 需要驗證 source card 是否過期

## Current Facts

對 current facts 做聲明前，必須先 refresh local source cache 或 live upstream source。若使用 stale cache，必須明說 stale 狀態與 manifest commit/ref。local refresh 產物在 `temp_artifact/` 下，只能留本地，不得 push。

## No Runtime Install

此 repository root 是 staged draft，不會自動啟用。除非使用者另行要求，不得 copy/symlink 到 `.agents/skills`、Codex 全域 skill root 或 OMX 設定。
