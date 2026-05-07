# Runtime Protocol

這份 staged pack 的核心是三層 tree pointer，而不是大型知識庫。

## 三層規則

1. Root `SKILL.md`: 只能選 category。
2. Category router: 只能選 source card 或 materialization decision。
3. Source card: 只能選 anchor、manifest、route index 或 graph locator。
4. Raw repo file: 只有最後一步才讀，而且必須有明確需求。

## Lazy Loading

預設讀取集合：

- `SKILL.md`
- selected `references/category-routers/<route_id>.md`
- selected `references/source-cards/<source_id>.md`

不得因為 card 裡列了 anchor paths 就自動深讀。以下情境才升級：

- repo behavior / API / CLI / current facts
- cross-file evidence
- 使用者要求 latest/current
- 需要驗證 source card 是否過期

## Current Facts

對 current facts 做聲明前，必須先 refresh live source 或 materialized pinned worktree。若使用 stale cache，必須明說 stale 狀態與 manifest commit/ref。

## No Runtime Install

本資料夾是 `docs/` 下 staged draft，不會自動啟用。除非使用者另行要求，不得 copy/symlink 到 `.agents/skills`、Codex 全域 skill root 或 OMX 設定。
