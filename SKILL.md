---
name: ai-capability-pointer-router
description: Use when a user asks which AI capability repository to consult for agent skills, skill infrastructure, evaluation, benchmarking, redteam, or durable GitHub repo pointers for later use.
---

# AI Capability Pointer Router

此 repository root 是 staged Codex skill draft，供審查與改進；它不是 runtime-installed skill。

## 必守路由

1. 先判斷使用者問題屬於哪個 category，只能選 category router。
2. 讀取對應 `references/category-routers/<route_id>.md`，只能選 source card 或 materialization decision。
3. 讀取對應 `references/source-cards/<source_id>.md`，只能選 anchor / manifest / index。
4. 只有最後一步、且問題需要 repo behavior / API / CLI / current facts / cross-file evidence 時，才開 raw repo file。

## 預設讀取量

預設只讀本檔、被選中的 category router、被選中的 source card。不要因為 source card 指到 repo 就直接 materialize 或深讀 worktree。

## Category

`references/route-registry.yaml` 是 category source of truth。下面只列目前已有 route：

- `skill_building`: agent skill spec、Codex skill 寫法、cross-agent skill discovery / install / packaging。
- `eval_benchmark`: LLM eval、benchmark、redteam、provider setup、CI regression。

詳細規則放在 `references/route-registry.yaml`、`references/runtime-protocol.md`、`references/evidence-rules.md`。
