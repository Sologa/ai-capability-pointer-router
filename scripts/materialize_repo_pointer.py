#!/usr/bin/env python3
"""Draft materialization planner for ai-capability-pointer-router.

This staged implementation is intentionally conservative: dry-run prints the
declared plan and never clones, fetches, installs, runs hooks, or executes repo
code. Non-dry-run exits with a clear message until the clone/index writer is
implemented and reviewed.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from pathlib import PurePosixPath
from urllib.parse import urlparse

import yaml


ALLOWED_MODES = {
    "pointer_only",
    "materialize_on_first_use",
    "materialize_and_graph_on_first_use",
    "manual_only",
}
SOURCE_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
CACHE_ROOT = "temp_artifact/repo_pointer_router_cache"
CACHE_PREFIX = f"{CACHE_ROOT}/"
ALLOWED_REF_VALUES = {"main", "tags", "commit_sha"}


def load_registry(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    if not isinstance(data, dict):
        raise ValueError("registry must be a YAML mapping")
    return data


def validate_source_id(source_id: str) -> None:
    if not SOURCE_RE.match(source_id):
        raise ValueError(f"source id must be lowercase kebab-case: {source_id}")


def validate_cache_path(field: str, value: str, *, allow_root: bool = False) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{field} must be a non-empty string")
    path = PurePosixPath(value)
    if path.is_absolute():
        raise ValueError(f"{field} must be relative: {value}")
    if ".." in path.parts:
        raise ValueError(f"{field} must not contain '..': {value}")
    if "\\" in value:
        raise ValueError(f"{field} must use POSIX path separators: {value}")
    if allow_root and value == CACHE_ROOT:
        return value
    if not value.startswith(CACHE_PREFIX):
        raise ValueError(f"{field} must stay under {CACHE_PREFIX}: {value}")
    return value


def validate_locator_path(field: str, value: object) -> None:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{field} must be a non-empty string")
    path = PurePosixPath(value)
    if path.is_absolute():
        raise ValueError(f"{field} must be relative: {value}")
    if ".." in path.parts:
        raise ValueError(f"{field} must not contain '..': {value}")
    if "\\" in value:
        raise ValueError(f"{field} must use POSIX path separators: {value}")


def validate_graph_scope(source_id: str, materialization: dict) -> None:
    graph = materialization.get("graph")
    if not isinstance(graph, dict):
        raise ValueError(f"{source_id}: materialization.graph must be a mapping")
    scope = graph.get("scope")
    if not isinstance(scope, dict):
        raise ValueError(f"{source_id}: graph.scope must be a mapping")
    include = scope.get("include")
    exclude = scope.get("exclude")
    if not isinstance(include, list) or not isinstance(exclude, list):
        raise ValueError(f"{source_id}: graph scope include/exclude must be lists")
    if graph.get("enabled") and not include:
        raise ValueError(f"{source_id}: enabled graph requires non-empty scope.include")
    for idx, item in enumerate(include):
        validate_locator_path(f"{source_id}: graph.scope.include[{idx}]", item)
    for idx, item in enumerate(exclude):
        validate_locator_path(f"{source_id}: graph.scope.exclude[{idx}]", item)


def validate_repo_url(source_id: str, repo_url: str, registry: dict) -> None:
    parsed = urlparse(repo_url)
    if parsed.scheme != "https":
        raise ValueError(f"{source_id}: repo_url scheme must be https: {repo_url}")

    allowlist = set(registry.get("materialization_defaults", {}).get("host_allowlist", []))
    if parsed.hostname not in allowlist:
        raise ValueError(f"{source_id}: repo host '{parsed.hostname}' is not allowlisted")


def validate_source(registry: dict, source_id: str) -> dict:
    validate_source_id(source_id)
    sources = registry.get("sources")
    if not isinstance(sources, dict):
        raise ValueError("registry.sources must be a mapping")
    source = sources.get(source_id)
    if not isinstance(source, dict):
        available = ", ".join(sorted(sources))
        raise ValueError(f"unknown source '{source_id}'. Available: {available}")

    materialization = source.get("materialization")
    if not isinstance(materialization, dict):
        raise ValueError(f"{source_id}: missing materialization mapping")
    mode = materialization.get("mode")
    if mode not in ALLOWED_MODES:
        raise ValueError(f"{source_id}: invalid materialization.mode '{mode}'")

    repo_url = materialization.get("repo_url") or source.get("repo_url")
    if not isinstance(repo_url, str) or not repo_url:
        raise ValueError(f"{source_id}: missing repo_url")
    source_repo_url = source.get("repo_url")
    if isinstance(source_repo_url, str) and source_repo_url and source_repo_url != repo_url:
        raise ValueError(f"{source_id}: source.repo_url and materialization.repo_url must match")
    validate_repo_url(source_id, repo_url, registry)

    allowed_refs = materialization.get("allowed_refs")
    if not isinstance(allowed_refs, list) or not all(item in ALLOWED_REF_VALUES for item in allowed_refs):
        raise ValueError(f"{source_id}: allowed_refs must be a list drawn from {sorted(ALLOWED_REF_VALUES)}")

    defaults = registry.get("materialization_defaults", {})
    cache_root = defaults.get("cache_root", CACHE_ROOT)
    validate_cache_path("materialization_defaults.cache_root", cache_root, allow_root=True)
    manifest_index = defaults.get("manifest_index")
    if manifest_index is not None:
        validate_cache_path("materialization_defaults.manifest_index", manifest_index)

    manifest = materialization.get("manifest")
    if not isinstance(manifest, dict):
        raise ValueError(f"{source_id}: missing materialization.manifest mapping")
    manifest_path = manifest.get("path")
    validate_cache_path(f"{source_id}: materialization.manifest.path", manifest_path)
    validate_graph_scope(source_id, materialization)

    return source


def build_plan(registry_path: Path, registry: dict, source_id: str) -> dict:
    source = validate_source(registry, source_id)
    materialization = source["materialization"]
    cache_root = registry.get("materialization_defaults", {}).get(
        "cache_root", CACHE_ROOT
    )
    repo_dir = f"{cache_root}/repos/{source_id}"
    graph = materialization.get("graph", {})
    manifest_path = materialization.get("manifest", {}).get("path")

    return {
        "status": "dry_run_plan",
        "registry": str(registry_path),
        "source_id": source_id,
        "category": source.get("category"),
        "repo_url": materialization.get("repo_url") or source.get("repo_url"),
        "mode": materialization.get("mode"),
        "default_ref": materialization.get("default_ref"),
        "allowed_refs": materialization.get("allowed_refs", []),
        "pin_policy": materialization.get("pin_policy"),
        "update_policy": materialization.get("update_policy"),
        "stale_after_hours": source.get("stale_after_hours"),
        "paths": {
            "worktree": f"{repo_dir}/worktree",
            "manifest": manifest_path,
            "manifest_exists": bool(manifest_path and Path(manifest_path).exists()),
            "git_state": f"{repo_dir}/git_state.json",
            "route_index": f"{repo_dir}/route_index.json",
            "graph": f"{repo_dir}/graphify-out/graph.json" if graph.get("enabled") else None,
        },
        "graph": {
            "enabled": bool(graph.get("enabled")),
            "mode": graph.get("mode", "locator_only"),
            "scope": graph.get("scope", {"include": [], "exclude": []}),
            "max_files": materialization.get("max_files"),
            "max_bytes": materialization.get("max_bytes"),
        },
        "read_first": source.get("read_first", []),
        "route_index_keys": sorted((source.get("route_index") or {}).keys()),
        "safety": {
            "clone": False,
            "fetch": False,
            "run_package_install": False,
            "run_repo_scripts": False,
            "run_hooks": False,
        },
    }


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Plan repo pointer materialization.")
    parser.add_argument("--registry", required=True, help="Path to route-registry.yaml")
    parser.add_argument("--source", required=True, help="Source ID from registry.sources")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print manifest/worktree/graph/index plan only; never clone or write cache.",
    )
    parser.add_argument(
        "--offline-ok",
        action="store_true",
        help="Allow offline planning. This draft only plans and never contacts network.",
    )
    parser.add_argument(
        "--write-cache",
        action="store_true",
        help="Future explicit write mode. Currently rejected in this staged draft.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    registry_path = Path(args.registry)
    registry = load_registry(registry_path)
    plan = build_plan(registry_path, registry, args.source)
    plan["offline_ok"] = bool(args.offline_ok)

    if args.dry_run:
        print(json.dumps(plan, indent=2, ensure_ascii=False, sort_keys=True))
        return 0

    print(json.dumps(plan, indent=2, ensure_ascii=False, sort_keys=True))
    if args.write_cache:
        print(
            "--write-cache is intentionally not implemented in this staged draft; "
            "clone/fetch/index/write-cache requires a separate reviewed implementation.",
            file=sys.stderr,
        )
    else:
        print(
            "Write actions require an explicit --write-cache flag, and that mode is "
            "not implemented in this staged draft. Rerun with --dry-run for read-only planning.",
            file=sys.stderr,
        )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
