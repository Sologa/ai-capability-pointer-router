# Evidence Rules

## Locator 不是 Evidence

以下都只能當 locator：

- `references/route-registry.yaml`
- category router
- source card
- route index
- graph / graph report
- materialization manifest

它們可以告訴 agent 去哪裡看，但不能單獨支撐 repo behavior、API、CLI、current facts 或 benchmark 結論。

## 可接受 Evidence

可接受 evidence 必須來自實際 source：

- pinned worktree raw file
- live GitHub raw/blob source
- official product documentation
- released package documentation
- 使用者提供的檔案內容

## 回答時要標記

當回答依賴 repo 內容時，至少標記：

- `source_id`
- raw path 或 URL
- ref / commit / 查詢日期
- claim 是 current、pinned snapshot、還是 stale cache

建議 evidence packet 欄位：

```yaml
source_id: promptfoo-promptfoo
raw_path_or_url: plugins/promptfoo/skills/promptfoo-provider-setup/SKILL.md
ref_or_commit: "<commit-or-live-date>"
span_or_section: "<heading-or-line-range-if-known>"
quote_or_summary: "<short supporting excerpt or summary>"
support_type: direct|indirect|locator_only|unsupported
freshness: current|pinned_snapshot|stale_cache
```

## 禁止推論

不要把某 repo 的 installer / skill / eval pattern 推廣成所有 agent runtime 的事實。跨 repo 比較必須讀各 repo 的 raw evidence。
