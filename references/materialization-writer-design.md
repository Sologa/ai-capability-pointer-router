# Materialization Writer Design

This repository has a local-only clone/fetch/checkout refresh path in `scripts/local_refresh_repos.py`. `scripts/materialize_repo_pointer.py` remains a dry-run planner, and its `--write-cache` mode is intentionally rejected.

This document is the minimum design contract for local refresh and any future planner write-cache mode. It authorizes only git-ignored local outputs under `temp_artifact/repo_pointer_router_cache/`, not committed generated artifacts.

## Required Threat Model

The local refresh path must assume upstream repositories can contain unsafe paths, symlinks, hooks, submodules, package scripts, large files, generated directories, stale examples, or files that look authoritative but are not evidence for the user's question.

The writer must never execute upstream code.

## Minimum Writer Behavior

The reviewed local refresh script supports explicit source selection:

- `--source <source_id>` for one source;
- `--all` only after the single-source path is tested.

It must:

- allow only HTTPS GitHub repos from the registry host allowlist;
- reject ambiguous source IDs and refs;
- clone/fetch/checkout without running hooks, package managers, repo scripts, builds, or tests;
- avoid recursive submodule checkout by default;
- resolve and record a 40-character commit SHA;
- write under `temp_artifact/repo_pointer_router_cache/repos/<source_id>/`;
- write cache atomically;
- leave generated cache and graph outputs untracked by default;
- fail closed on path traversal, symlink escape, oversized scope, or partial writes.

## Required Artifacts

For each materialized source, the writer must produce locator-only artifacts:

- `materialization.json`, validated against `schemas/materialization-manifest.schema.json`;
- `git_state.json`, recording requested ref, resolved commit, checkout status, and safety flags;
- `route_index.json`, validated against `schemas/route-index-artifact.schema.json`;
- graph artifacts only under the local worktree `graphify-out/`, never committed.

These artifacts locate raw files. They are not evidence for factual claims.

## Required Validation

Before extending local refresh or enabling planner `--write-cache`, add validator coverage for:

- safe cache root and safe joined paths;
- resolved commit format;
- manifest schema and route-index artifact schema;
- no symlink escape from the worktree;
- no generated artifact committed accidentally;
- `--require-local-cache` checks for expected worktree, manifest, git state, and route index;
- graph scope coverage and file/byte budget reports when graph is enabled.

## Required Tests

Use local fixture git repositories rather than live GitHub for required CI tests.

At minimum cover:

- malicious repo URL;
- unsupported ref;
- path traversal;
- symlink escape;
- oversized file count or byte count;
- graph scope escape;
- stale manifest refresh;
- interrupted cache write and cleanup;
- package scripts/hooks/submodules remaining unexecuted.
