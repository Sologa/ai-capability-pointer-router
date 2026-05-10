---
name: ai-capability-pointer-router
description: Use when a user asks which AI capability repository to consult for agent skills, skill infrastructure, evaluation, benchmarking, redteam, durable GitHub repo pointers, or how to adapt this staged Codex router into another paper + repo taxonomy.
---

# AI Capability Pointer Router

此 repository root 是 staged Codex skill draft，供審查與改進；它不是 runtime-installed skill。當前 registry 是 `ai_capability` seed profile，但同一個三層 pointer contract 可以複製成不同 paper + repo taxonomy router。

## 必守路由

0. 判斷使用者問題屬於哪個 category，只能選 category router。
1. 選定 category 後，若問題需要 current repo evidence 或 local cache，執行 `python3 scripts/local_refresh_repos.py --registry references/route-registry.yaml --category {route_id}`。這只 refresh 該 category 的 sources；腳本會先做 remote HEAD freshness check，clean up-to-date 時不 fetch/reset，也不重建 graph；若本地 cache dirty，會不 fetch 但 reset/clean 後重建 locator artifacts。
2. 讀取對應 `references/category-routers/{route_id}.md`，只能選 source card 或 materialization decision。
3. 讀取對應 `references/source-cards/{source_id}.md`，只能選 anchor / manifest / index / local worktree / graph locator。需要單一 repo 時可用 `python3 scripts/local_refresh_repos.py --registry references/route-registry.yaml --source {source_id}`。
4. 只有最後一步、且問題需要 repo behavior / API / CLI / current facts / cross-file evidence 時，才開 raw repo file；優先讀 local refreshed worktree，必要時再讀 live upstream raw file。

## 預設讀取量

預設只讀本檔、被選中的 category router、被選中的 source card，以及被選中 category/source refresh 後的 manifest / git_state / route_index / graphify status。不要因為 source card 指到 repo 就深讀整個 worktree；只讀被選中 anchors 或問題需要的 scoped raw files。

`scripts/local_refresh_repos.py` 是 local-only automation：對選定 category/source clone 或 remote HEAD check；只有 remote commit 改變、cache 缺失或本地 cache dirty 時才 reset/clean latest `main`，且只有 remote commit 改變或 cache 缺失時才 fetch。它會驗證 `read_first` / route-index anchors 是 worktree 內 regular files，寫入 local manifest / route index，並在 commit、scope、route index、graph writer version 或 graph/report content hash 改變時重建 deterministic locator graph。全部產物都在 `.gitignore` 排除的 `temp_artifact/repo_pointer_router_cache/` 下，不得 commit/push。`scripts/materialize_repo_pointer.py` 仍只是 dry-run planner，`--write-cache` 仍禁用。

目前 graphify 的完整 semantic extraction 仍需要 `/graphify` skill / subagent 或未來 non-agent CLI；local refresh 會為 docs/papers/images 寫 `graphify-out/needs_semantic_graphify`，不能把它說成 complete semantic graph。

## Template / Profile 模式

`references/route-registry.yaml` 的 `profile` block 說明目前 profile 的 domain。若使用者要做另一個 paper + repo taxonomy router，先讀 `references/template-authoring.md` 和 `templates/paper-repo-taxonomy/`，再替換 profile/routes/sources/category routers/source cards。模板 placeholder 不能當作事實來源；新 taxonomy 必須用實際 repo anchors、`last_verified.checked_paths`、source cards 和 validator 結果閉合。

目前 materialization 只支援 HTTPS GitHub repos on `main`。若 paper 只存在 PDF/arXiv/Zenodo/local corpus，或 repo 不在 GitHub/main，這些可以先在 taxonomy prose 中描述，但不能假裝已被 local refresh pipeline materialize；需要先擴 schema/scripts。

## Category

`references/route-registry.yaml` 是 category source of truth。下面只列目前 `ai_capability` seed profile 已有 route：

- `skill_building`: agent skill spec、Codex skill 寫法、cross-agent skill discovery / install / packaging。
- `eval_benchmark`: LLM eval、benchmark、redteam、provider setup、CI regression。

詳細規則放在 `references/route-registry.yaml`、`references/runtime-protocol.md`、`references/evidence-rules.md`、`references/graph-scope-policy.md`、`references/materialization-writer-design.md`。
