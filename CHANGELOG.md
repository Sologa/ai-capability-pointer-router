# Changelog

## 0.1.0-staged

- Added staged three-layer pointer router for skill-building and eval/benchmark sources.
- Added README, CI validation, unit tests, and optional upstream anchor checker.
- Hardened materialization dry-run path, URL, graph-scope, and error handling.
- Added publication-health docs and schema contracts.
- Added Apache-2.0 licensing.
- Added schema enforcement for the registry and dry-run plans, plus schemas for local-only materialization, route-index, and graph artifacts.
- Hardened write-cache rejection so `--dry-run --write-cache` cannot succeed.
- Added local-only `scripts/local_refresh_repos.py` to clone/fetch all registered repos into git-ignored `temp_artifact/`, write manifests/route indexes, and rebuild deterministic graphify locator outputs.
- Added structured router/source-card metadata checks, explicit `implementation_status: local_refresh_enabled`, and design docs for local refresh plus graph scope boundaries.

This remains a staged draft: it is not runtime-installed by default, generated cache/graph artifacts are not committed, and planner `--write-cache` remains intentionally unimplemented.
