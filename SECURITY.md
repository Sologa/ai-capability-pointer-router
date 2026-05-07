# Security

This repository is a locator-only staged draft. It should not execute upstream repository code.

## Current Safety Model

- `scripts/materialize_repo_pointer.py` is dry-run only.
- `--write-cache` is intentionally rejected.
- The validator rejects unsafe cache paths, unsafe graph scope paths, symlinks, and macOS sidecar files outside generated directories.
- Optional upstream anchor checks perform GitHub raw-file reads only.

## Reporting

Open a GitHub issue for security concerns that do not expose private credentials or secrets. For sensitive reports, contact the repository owner through their GitHub profile.

## Out of Scope

The following are not implemented and should not be assumed safe:

- clone/fetch/write-cache materialization
- graph build or graph refresh
- executing package managers, hooks, tests, or scripts from upstream repositories
- following external symlinks in materialized worktrees
