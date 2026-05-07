---
route_id: eval_benchmark
sources:
  - promptfoo-promptfoo
---

# Category Router: `eval_benchmark`

本 router 只處理 evaluation、benchmark、redteam、provider setup、CI regression 的 source 選路。現階段只有一個 primary source：`promptfoo-promptfoo`。

## Source 選擇

- `promptfoo-promptfoo`: 問 prompt/model/provider eval、redteam workflow、Promptfoo skills、CI regression、eval artifact triage。

## Materialization Decision

Promptfoo 是大型且活躍的 monorepo。skill invoke 時 root 已先執行 local refresh。只要問題涉及 current CLI behavior、provider options、redteam command、CI integration、config schema 或跨 docs/code 證據，本 router 只回傳 materialization decision。第三層 `promptfoo-promptfoo` source card 才能選 route index / anchor / local worktree；raw repo file 仍只能在最後 evidence 步驟打開。

## Evidence Boundary

不要從 route index 或 graph 直接推論 Promptfoo 行為。它們只能幫你找到應該開哪個 raw file。
