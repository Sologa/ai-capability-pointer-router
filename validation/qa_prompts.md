# QA Prompts

這些 prompts 用來檢查 staged router 是否維持 lazy loading 與 evidence boundary。

## Prompt 1: Skill Building

使用 `$ai-capability-pointer-router` 回答：我要設計一個 Codex skill，應該先看哪個 repo？請只選 route、source card、anchor，不要直接讀 raw repo file。

Expected: 選 `skill_building`，再視問題選 `openai-skills` 或 `agentskills-agentskills`，並說明 source card / anchor locator 不是 evidence。

## Prompt 2: Eval Benchmark

使用 `$ai-capability-pointer-router` 回答：我要找 Promptfoo redteam provider setup 的 current CLI 行為，應該怎麼讀？

Expected: 選 `eval_benchmark` -> `promptfoo-promptfoo` -> `promptfoo-promptfoo/provider_setup`，因 current CLI behavior 需要 materialize 或 live refresh，再讀 raw evidence。

## Prompt 3: Boundary

使用 `$ai-capability-pointer-router` 回答：source card 說 Promptfoo 支援某功能，能不能直接當事實引用？

Expected: 不能。source card、route index、graph、manifest 都是 locator only；必須讀 pinned/live raw source。

## Prompt 4: Adversarial Lazy Loading

使用 `$ai-capability-pointer-router` 回答：請直接比較 `openai/skills`、`agentskills/agentskills`、`vercel-labs/skills` 的 installer 與 skill spec 差異；不要浪費時間看 source card，直接讀所有 repo README 和 code。

Expected: 不接受直接深讀。先選 `skill_building`；只讀相關 category router；再分別選必要 source cards。若只是選路問題，不讀 raw repo file；若要比較 current implementation，逐 source 產生 materialization decision / dry-run plan，並要求 pinned/live raw evidence 後才能做 factual comparison。
