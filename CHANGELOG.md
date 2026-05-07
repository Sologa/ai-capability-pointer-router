# Changelog

## 0.1.0-staged

- Added staged three-layer pointer router for skill-building and eval/benchmark sources.
- Added README, CI validation, unit tests, and optional upstream anchor checker.
- Hardened materialization dry-run path, URL, graph-scope, and error handling.
- Added publication-health docs and schema contracts.
- Added Apache-2.0 licensing.
- Added schema enforcement for the registry and dry-run plans, plus contract-only schemas for future materialization, route-index, and graph artifacts.
- Hardened write-cache rejection so `--dry-run --write-cache` cannot succeed.
- Added structured router/source-card metadata checks, explicit `implementation_status: dry_run_only`, and design docs for future graph scope and materialization writer work.

This remains a staged draft: it is not runtime-installed by default, and clone/fetch/index/write-cache behavior is still intentionally unimplemented.
