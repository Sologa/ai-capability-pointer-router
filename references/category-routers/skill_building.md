---
route_id: skill_building
sources:
  - agentskills-agentskills
  - openai-skills
  - vercel-labs-skills
---

# Category Router: `skill_building`

本 router 只做第二層選路，不直接回答 repo 事實。選到 source 後，先讀 source card；只有問題明確需要 repo behavior、API、CLI、current facts 或 cross-file evidence，才 materialize 或開 raw repo file。

## Source 選擇

- `agentskills-agentskills`: 問 Agent Skills 開放格式、`SKILL.md` 契約、client 如何支援 skills、progressive disclosure。
- `openai-skills`: 問 Codex skill 寫法、官方 catalog 範例、`skill-creator` / `skill-installer` pattern、`agents/openai.yaml`。
- `vercel-labs-skills`: 問 cross-agent skill discovery / install / lock / update / source parsing。

## Materialization Decision

skill invoke 時已由 root 執行 `scripts/local_refresh_repos.py --all` 來 clone/fetch 最新 local cache。只有以下情境才回傳 materialization decision 或讀取 local worktree raw files；`scripts/materialize_repo_pointer.py` 仍只做 dry-run planning，不能 `--write-cache`：

- 使用者要求 current/latest repo behavior。
- 需要比較多個 anchor file 的實作細節。
- 需要確認 CLI/API/code path。
- source card 的 locator 不足以回答。

## Evidence Boundary

source card、route index、graph、manifest 都只是 locator。要做事實聲明時，必須讀 pinned worktree 或 live official source 中的實際文件，並回報 commit/ref 或查詢時間。
