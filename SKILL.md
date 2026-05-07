---
name: ai-capability-pointer-router
description: Use when a user asks which AI capability repository to consult for agent skills, skill infrastructure, evaluation, benchmarking, redteam, or durable GitHub repo pointers for later use.
---

# AI Capability Pointer Router

此 repository root 是 staged Codex skill draft，供審查與改進；它不是 runtime-installed skill。

## 必守路由

0. 每次本 skill 被 invoke，先在本 repository root 執行 `python scripts/local_refresh_repos.py --registry references/route-registry.yaml --all`。這會把 registry 內所有 source clone/refresh 到 git-ignored `temp_artifact/repo_pointer_router_cache/repos/<source_id>/worktree/`，並重建可自動化的 `graphify-out/` locator artifacts。
1. 判斷使用者問題屬於哪個 category，只能選 category router。
2. 讀取對應 `references/category-routers/<route_id>.md`，只能選 source card 或 materialization decision。
3. 讀取對應 `references/source-cards/<source_id>.md`，只能選 anchor / manifest / index / local worktree / graph locator。
4. 只有最後一步、且問題需要 repo behavior / API / CLI / current facts / cross-file evidence 時，才開 raw repo file；優先讀 local refreshed worktree，必要時再讀 live upstream raw file。

## 預設讀取量

預設只讀本檔、被選中的 category router、被選中的 source card，以及 refresh 後的 manifest / git_state / route_index / graphify status。不要因為 source card 指到 repo 就深讀整個 worktree；只讀被選中 anchors 或問題需要的 scoped raw files。

`scripts/local_refresh_repos.py` 是 local-only automation：clone/fetch/reset latest `main`、寫入 local manifest / route index、重建 deterministic graphify locator graph，全部在 `.gitignore` 排除的 `temp_artifact/` 下，不得 commit/push。`scripts/materialize_repo_pointer.py` 仍只是 dry-run planner，`--write-cache` 仍禁用。

目前 graphify 的完整 semantic extraction 仍需要 `/graphify` skill / subagent 或未來 non-agent CLI；local refresh 會為 docs/papers/images 寫 `graphify-out/needs_semantic_graphify`，不能把它說成 complete semantic graph。

## Category

`references/route-registry.yaml` 是 category source of truth。下面只列目前已有 route：

- `skill_building`: agent skill spec、Codex skill 寫法、cross-agent skill discovery / install / packaging。
- `eval_benchmark`: LLM eval、benchmark、redteam、provider setup、CI regression。

詳細規則放在 `references/route-registry.yaml`、`references/runtime-protocol.md`、`references/evidence-rules.md`、`references/graph-scope-policy.md`、`references/materialization-writer-design.md`。
