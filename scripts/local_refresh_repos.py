#!/usr/bin/env python3
"""Local-only repo cache refresher for ai-capability-pointer-router.

This script is intentionally local-output only. It clones or refreshes selected
GitHub repos under temp_artifact/repo_pointer_router_cache/, writes locator
manifests, and rebuilds deterministic locator graph artifacts only when the
repo commit or graph contract changed. Generated repos and graph outputs are
ignored by git.
"""

from __future__ import annotations

import argparse
import fnmatch
import json
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from pathlib import PurePosixPath
from urllib.parse import urlparse

import yaml


SOURCE_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
ROUTE_RE = re.compile(r"^[a-z][a-z0-9_]*$")
CACHE_ROOT = "temp_artifact/repo_pointer_router_cache"
CACHE_PREFIX = f"{CACHE_ROOT}/"
ALLOWED_REF_VALUES = {"main", "tags", "commit_sha"}
GRAPH_WRITER_VERSION = "locator_graph_v1"
SEMANTIC_EXTENSIONS = {
    ".csv",
    ".doc",
    ".docx",
    ".gif",
    ".jpeg",
    ".jpg",
    ".jsonl",
    ".md",
    ".mdx",
    ".pdf",
    ".png",
    ".rst",
    ".svg",
    ".txt",
    ".yaml",
    ".yml",
}


class RefreshError(Exception):
    pass


def run(cmd: list[str], *, cwd: Path | None = None) -> str:
    proc = subprocess.run(cmd, cwd=cwd, text=True, capture_output=True, check=False)
    if proc.returncode != 0:
        detail = proc.stderr.strip() or proc.stdout.strip()
        raise RefreshError(f"{' '.join(cmd)} failed: {detail}")
    return proc.stdout.strip()


def clean_worktree(worktree: Path) -> None:
    shutil.rmtree(worktree / "graphify-out", ignore_errors=True)
    proc = subprocess.run(
        ["git", "-C", str(worktree), "clean", "-fdx"],
        text=True,
        capture_output=True,
        check=False,
    )
    if proc.returncode != 0:
        detail = proc.stderr.strip() or proc.stdout.strip()
        if "could not lstat" not in detail:
            raise RefreshError(f"git clean failed: {detail}")


def load_registry(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    if not isinstance(data, dict):
        raise RefreshError("registry must be a YAML mapping")
    return data


def infer_skill_root(registry_path: Path) -> Path:
    resolved = registry_path.resolve()
    if resolved.name == "route-registry.yaml" and resolved.parent.name == "references":
        return resolved.parent.parent
    return resolved.parent


def validate_source_id(source_id: str) -> None:
    if not SOURCE_RE.match(source_id):
        raise RefreshError(f"source id must be lowercase kebab-case: {source_id}")


def validate_route_id(route_id: str) -> None:
    if not ROUTE_RE.match(route_id):
        raise RefreshError(f"route id must be snake_case: {route_id}")


def validate_repo_url(source_id: str, repo_url: str, allowlist: list[str]) -> None:
    parsed = urlparse(repo_url)
    if parsed.scheme != "https" or parsed.hostname not in set(allowlist):
        raise RefreshError(f"{source_id}: repo_url must be https and host-allowlisted: {repo_url}")
    path = parsed.path.strip("/")
    if path.endswith(".git"):
        path = path[:-4]
    if len(path.split("/")) != 2:
        raise RefreshError(f"{source_id}: repo_url must identify exactly owner/repo: {repo_url}")


def validate_cache_rel(field: str, value: str, *, allow_root: bool = False) -> str:
    path = PurePosixPath(value)
    if path.is_absolute() or ".." in path.parts or "\\" in value:
        raise RefreshError(f"{field} must be a safe relative POSIX path: {value}")
    if allow_root and value == CACHE_ROOT:
        return value
    if not value.startswith(CACHE_PREFIX):
        raise RefreshError(f"{field} must stay under {CACHE_PREFIX}: {value}")
    return value


def safe_cache_path(skill_root: Path, rel_path: str, *, allow_root: bool = False) -> Path:
    validate_cache_rel("cache path", rel_path, allow_root=allow_root)
    root = skill_root.resolve()
    cache_root = (root / CACHE_ROOT).resolve()
    path = (root / rel_path).resolve()
    if path != cache_root and cache_root not in path.parents:
        raise RefreshError(f"resolved cache path escapes cache root: {rel_path}")
    return path


def relative_cache_path(path: Path, skill_root: Path) -> str:
    return str(path.resolve().relative_to(skill_root.resolve()))


def atomic_write_json(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    tmp.replace(path)


def atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(path)


def read_json(path: Path) -> object | None:
    try:
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, json.JSONDecodeError):
        return None


def scope_excludes(rel_path: Path, patterns: list[str]) -> bool:
    path_text = rel_path.as_posix()
    for pattern in patterns:
        if pattern in rel_path.parts:
            return True
        if fnmatch.fnmatch(path_text, pattern) or fnmatch.fnmatch(rel_path.name, pattern):
            return True
    return False


def remote_head(repo_url: str, ref: str) -> str:
    output = run(["git", "ls-remote", repo_url, f"refs/heads/{ref}"])
    parts = output.split()
    if not parts:
        raise RefreshError(f"remote ref not found: {repo_url} {ref}")
    commit = parts[0]
    if not re.fullmatch(r"[0-9a-f]{40}", commit):
        raise RefreshError(f"remote ref did not resolve to a 40-char sha: {commit}")
    return commit


def clone_or_refresh(source_id: str, repo_url: str, worktree: Path, ref: str, *, force: bool = False) -> dict:
    worktree.parent.mkdir(parents=True, exist_ok=True)
    if (worktree / ".git").is_dir():
        run(["git", "-C", str(worktree), "remote", "set-url", "origin", repo_url])
        local_commit = run(["git", "-C", str(worktree), "rev-parse", "HEAD"])
        remote_commit = remote_head(repo_url, ref)
        if not force and local_commit == remote_commit:
            return {
                "action": "up_to_date",
                "resolved_commit": local_commit,
                "remote_commit": remote_commit,
                "fetch_performed": False,
            }
        action = "refresh"
        run(["git", "-C", str(worktree), "reset", "--hard"])
        clean_worktree(worktree)
        run(["git", "-C", str(worktree), "fetch", "--prune", "origin", ref])
    else:
        if worktree.exists():
            shutil.rmtree(worktree)
        action = "clone"
        run(["git", "-c", "core.hooksPath=/dev/null", "clone", "--no-recurse-submodules", repo_url, str(worktree)])
        run(["git", "-C", str(worktree), "fetch", "--prune", "origin", ref])

    run(["git", "-C", str(worktree), "checkout", "--force", "-B", ref, f"origin/{ref}"])
    run(["git", "-C", str(worktree), "reset", "--hard", f"origin/{ref}"])
    clean_worktree(worktree)
    subprocess.run(
        ["git", "-C", str(worktree), "submodule", "deinit", "--all", "--force"],
        text=True,
        capture_output=True,
        check=False,
    )
    commit = run(["git", "-C", str(worktree), "rev-parse", "HEAD"])
    if not re.fullmatch(r"[0-9a-f]{40}", commit):
        raise RefreshError(f"{source_id}: resolved commit is not a 40-char sha: {commit}")
    return {
        "action": action,
        "resolved_commit": commit,
        "remote_commit": commit,
        "fetch_performed": True,
    }


def build_route_index_artifact(source_id: str, source: dict, resolved_commit: str) -> dict:
    entries = []
    for key, anchors in sorted((source.get("route_index") or {}).items()):
        entries.append(
            {
                "key": key,
                "anchors": [
                    {
                        "kind": "raw_file",
                        "path": path,
                        "source_id": source_id,
                        "repo_url": source["repo_url"],
                        "commit": resolved_commit,
                        "locator_only": True,
                    }
                    for path in anchors
                ],
            }
        )
    return {
        "source_id": source_id,
        "repo_url": source["repo_url"],
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "resolved_commit": resolved_commit,
        "locator_only": True,
        "entries": entries,
    }


def graph_meta(source_id: str, source: dict, materialization: dict, resolved_commit: str) -> dict:
    graph = materialization.get("graph") if isinstance(materialization.get("graph"), dict) else {}
    return {
        "writer_version": GRAPH_WRITER_VERSION,
        "source_id": source_id,
        "repo_url": source["repo_url"],
        "resolved_commit": resolved_commit,
        "graph": graph,
        "max_files": materialization.get("max_files"),
        "max_bytes": materialization.get("max_bytes"),
        "route_index": source.get("route_index") or {},
    }


def graph_is_current(out: Path, expected_meta: dict) -> bool:
    return (
        (out / "graph.json").is_file()
        and (out / "graph_report.json").is_file()
        and (out / "graph_meta.json").is_file()
        and read_json(out / "graph_meta.json") == expected_meta
    )


def iter_scoped_files(worktree: Path, includes: list[str], excludes: list[str]) -> list[Path]:
    files: list[Path] = []
    seen: set[Path] = set()
    worktree_resolved = worktree.resolve()
    for include in includes:
        scan_root = worktree / include
        if not scan_root.exists():
            continue
        candidates = [scan_root] if scan_root.is_file() or scan_root.is_symlink() else sorted(scan_root.rglob("*"))
        for path in candidates:
            if not path.is_file() and not path.is_symlink():
                continue
            try:
                rel = path.resolve().relative_to(worktree_resolved)
            except ValueError:
                continue
            if scope_excludes(rel, excludes):
                continue
            resolved = path.resolve()
            if resolved in seen:
                continue
            seen.add(resolved)
            files.append(path)
    return files


def route_index_nodes_and_edges(source: dict, file_node_ids: dict[str, str]) -> tuple[list[dict], list[dict]]:
    nodes: list[dict] = []
    edges: list[dict] = []
    route_index = source.get("route_index") if isinstance(source.get("route_index"), dict) else {}
    for key, anchors in sorted(route_index.items()):
        route_id = f"route:{key}"
        nodes.append({"id": route_id, "path": key, "locator_type": "route_index_entry"})
        if isinstance(anchors, list):
            for anchor in anchors:
                target = file_node_ids.get(anchor)
                if target:
                    edges.append({"from": route_id, "to": target, "relation": "points_to"})
    return nodes, edges


def run_graphify_code(
    source_id: str,
    source: dict,
    worktree: Path,
    materialization: dict,
    resolved_commit: str,
    *,
    force: bool = False,
) -> dict:
    out = worktree / "graphify-out"
    out.mkdir(exist_ok=True)
    graph = materialization.get("graph") if isinstance(materialization.get("graph"), dict) else {}
    if not graph.get("enabled"):
        return {"status": "graph_disabled", "graph_json": None, "graph_report": None}
    expected_meta = graph_meta(source_id, source, materialization, resolved_commit)
    if not force and graph_is_current(out, expected_meta):
        return {
            "status": "graph_up_to_date",
            "graph_json": str(out / "graph.json"),
            "graph_report": str(out / "graph_report.json"),
            "needs_semantic_graphify": (out / "needs_semantic_graphify").is_file(),
        }

    scope = graph.get("scope") if isinstance(graph.get("scope"), dict) else {}
    includes = scope.get("include") or ["."]
    excludes = scope.get("exclude") or []
    candidate_files = iter_scoped_files(worktree, includes, excludes)
    max_files = materialization.get("max_files")
    max_bytes = materialization.get("max_bytes")
    nodes: list[dict] = []
    edges: list[dict] = []
    file_node_ids: dict[str, str] = {}
    indexed_files = 0
    bytes_indexed = 0
    truncated = False
    warnings: list[str] = []
    semantic_needed = False

    for path in candidate_files:
        try:
            rel = path.resolve().relative_to(worktree.resolve())
        except ValueError:
            warnings.append(f"Skipped path escaping worktree: {path}")
            continue
        if path.is_symlink():
            warnings.append(f"Skipped symlink: {rel.as_posix()}")
            continue
        try:
            size = path.stat().st_size
        except OSError as exc:
            warnings.append(f"Skipped unreadable file {rel.as_posix()}: {exc}")
            continue
        if isinstance(max_files, int) and indexed_files >= max_files:
            truncated = True
            continue
        if isinstance(max_bytes, int) and bytes_indexed + size > max_bytes:
            truncated = True
            continue
        rel = path.relative_to(worktree)
        rel_text = rel.as_posix()
        semantic_needed = semantic_needed or path.suffix.lower() in SEMANTIC_EXTENSIONS
        node_id = f"file:{rel_text}"
        nodes.append({"id": node_id, "path": rel_text, "locator_type": "file"})
        file_node_ids[rel_text] = node_id
        indexed_files += 1
        bytes_indexed += size

    route_nodes, route_edges = route_index_nodes_and_edges(source, file_node_ids)
    nodes.extend(route_nodes)
    edges.extend(route_edges)
    now = datetime.now(timezone.utc).isoformat()
    graph_artifact = {
        "source_id": source_id,
        "repo_url": source["repo_url"],
        "resolved_commit": resolved_commit,
        "generated_at": now,
        "semantics": "locator_only",
        "nodes": nodes,
        "edges": edges,
    }
    report_artifact = {
        "source_id": source_id,
        "resolved_commit": resolved_commit,
        "generated_at": now,
        "scope": {"include": includes, "exclude": excludes},
        "counts": {
            "files_seen": len(candidate_files),
            "files_indexed": indexed_files,
            "bytes_indexed": bytes_indexed,
        },
        "truncated": truncated,
        "warnings": warnings,
    }
    atomic_write_json(out / "graph.json", graph_artifact)
    atomic_write_json(out / "graph_report.json", report_artifact)
    atomic_write_json(out / "graph_meta.json", expected_meta)
    status = "locator_graph_updated"
    atomic_write_text(
        out / "GRAPH_REPORT.md",
        "\n".join(
            [
                "# Graphify Status",
                "",
                "Deterministic local locator graph rebuilt for the refreshed worktree.",
                "",
                f"- Files seen: {len(candidate_files)}",
                f"- Files indexed: {indexed_files}",
                f"- Bytes indexed: {bytes_indexed}",
                f"- Truncated: {str(truncated).lower()}",
                "- Semantics: locator_only",
                "",
                "This graph locates files only. It is not behavioral evidence.",
                "Full semantic graphify still requires /graphify or a future non-agent graphify CLI.",
                "",
            ]
        ),
    )

    marker = out / "needs_semantic_graphify"
    if semantic_needed:
        atomic_write_text(
            marker,
            "This repo has docs/papers/images. Full semantic graphify still requires /graphify or a future non-agent graphify CLI.\n",
        )
    elif marker.exists():
        marker.unlink()

    return {
        "status": status,
        "files_seen": len(candidate_files),
        "files_indexed": indexed_files,
        "bytes_indexed": bytes_indexed,
        "truncated": truncated,
        "warnings": warnings,
        "graph_json": str(out / "graph.json"),
        "graph_report": str(out / "graph_report.json"),
        "graph_report_markdown": str(out / "GRAPH_REPORT.md"),
        "needs_semantic_graphify": semantic_needed,
    }


def refresh_source(skill_root: Path, registry: dict, source_id: str, *, force: bool = False, force_graph: bool = False) -> dict:
    validate_source_id(source_id)
    sources = registry.get("sources")
    if not isinstance(sources, dict) or source_id not in sources:
        raise RefreshError(f"unknown source: {source_id}")
    source = sources[source_id]
    materialization = source.get("materialization")
    if not isinstance(source, dict) or not isinstance(materialization, dict):
        raise RefreshError(f"{source_id}: source/materialization must be mappings")
    if materialization.get("implementation_status") != "local_refresh_enabled":
        raise RefreshError(f"{source_id}: expected implementation_status local_refresh_enabled")
    if materialization.get("pin_policy") != "record_resolved_commit":
        raise RefreshError(f"{source_id}: local refresh requires pin_policy record_resolved_commit")
    if materialization.get("update_policy") != "fetch_latest_on_explicit_use":
        raise RefreshError(f"{source_id}: local refresh requires update_policy fetch_latest_on_explicit_use")
    for key in ("max_files", "max_bytes"):
        value = materialization.get(key)
        if not isinstance(value, int) or value <= 0:
            raise RefreshError(f"{source_id}: {key} must be a positive integer")
    graph = materialization.get("graph")
    if not isinstance(graph, dict) or graph.get("mode") != "locator_only":
        raise RefreshError(f"{source_id}: graph.mode must be locator_only")

    defaults = registry.get("materialization_defaults", {})
    allowlist = defaults.get("host_allowlist", ["github.com"])
    repo_url = materialization.get("repo_url") or source.get("repo_url")
    if not isinstance(repo_url, str):
        raise RefreshError(f"{source_id}: repo_url missing")
    validate_repo_url(source_id, repo_url, allowlist)

    cache_root = defaults.get("cache_root", CACHE_ROOT)
    cache_root_path = safe_cache_path(skill_root, cache_root, allow_root=True)
    repo_dir = cache_root_path / "repos" / source_id
    worktree = repo_dir / "worktree"
    ref = materialization.get("default_ref", "main")
    if ref != "main":
        raise RefreshError(f"{source_id}: local refresh currently supports default_ref main only")
    allowed_refs = materialization.get("allowed_refs")
    if not isinstance(allowed_refs, list) or not set(allowed_refs) <= ALLOWED_REF_VALUES:
        raise RefreshError(f"{source_id}: allowed_refs must be drawn from {sorted(ALLOWED_REF_VALUES)}")

    git_state = clone_or_refresh(source_id, repo_url, worktree, ref, force=force)
    resolved_commit = git_state["resolved_commit"]
    now = datetime.now(timezone.utc).isoformat()

    safety = {
        "run_package_install": False,
        "run_repo_scripts": False,
        "run_hooks": False,
        "follow_external_symlinks": False,
        "submodules_recursive": False,
    }
    manifest = {
        "source_id": source_id,
        "repo_url": repo_url,
        "requested_ref": ref,
        "resolved_commit": resolved_commit,
        "materialized_at": now,
        "worktree_path": relative_cache_path(worktree, skill_root),
        "safety": safety,
        "locator_only": True,
    }
    git_state_doc = {
        "source_id": source_id,
        "repo_url": repo_url,
        "default_ref": ref,
        "resolved_commit": resolved_commit,
        "action": git_state["action"],
        "updated_at": now,
        "worktree_path": relative_cache_path(worktree, skill_root),
        "safety": safety,
    }

    manifest_path = source.get("materialization", {}).get("manifest", {}).get("path")
    if not isinstance(manifest_path, str):
        manifest_path = relative_cache_path(repo_dir / "materialization.json", skill_root)
    atomic_write_json(safe_cache_path(skill_root, manifest_path), manifest)
    atomic_write_json(repo_dir / "git_state.json", git_state_doc)
    atomic_write_json(repo_dir / "route_index.json", build_route_index_artifact(source_id, source, resolved_commit))
    graph_status = run_graphify_code(
        source_id,
        source,
        worktree,
        materialization,
        resolved_commit,
        force=force or force_graph,
    )

    return {
        "source_id": source_id,
        "action": git_state["action"],
        "repo_url": repo_url,
        "resolved_commit": resolved_commit,
        "remote_commit": git_state.get("remote_commit"),
        "fetch_performed": git_state.get("fetch_performed"),
        "worktree": relative_cache_path(worktree, skill_root),
        "manifest": manifest_path,
        "git_state": relative_cache_path(repo_dir / "git_state.json", skill_root),
        "route_index": relative_cache_path(repo_dir / "route_index.json", skill_root),
        "graphify": graph_status,
    }


def selected_sources(registry: dict, categories: list[str] | None, sources: list[str] | None) -> list[str]:
    registry_sources = registry.get("sources")
    routes = registry.get("routes")
    if not isinstance(registry_sources, dict) or not isinstance(routes, dict):
        raise RefreshError("registry.sources and registry.routes must be mappings")

    selected: list[str] = []
    for route_id in categories or []:
        validate_route_id(route_id)
        route = routes.get(route_id)
        if not isinstance(route, dict):
            raise RefreshError(f"unknown category: {route_id}")
        route_sources = route.get("sources")
        if not isinstance(route_sources, list):
            raise RefreshError(f"{route_id}: route sources must be a list")
        selected.extend(str(source_id) for source_id in route_sources)
    for source_id in sources or []:
        validate_source_id(source_id)
        selected.append(source_id)

    unique: list[str] = []
    seen: set[str] = set()
    for source_id in selected:
        if source_id in seen:
            continue
        if source_id not in registry_sources:
            raise RefreshError(f"unknown source: {source_id}")
        seen.add(source_id)
        unique.append(source_id)
    return unique


def merge_manifest_index(index_path: Path, results: list[dict]) -> None:
    existing: dict[str, dict] = {}
    if index_path.is_file():
        for line in index_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                item = json.loads(line)
            except json.JSONDecodeError:
                continue
            source_id = item.get("source_id") if isinstance(item, dict) else None
            if isinstance(source_id, str):
                existing[source_id] = item
    for result in results:
        source_id = result.get("source_id")
        if isinstance(source_id, str):
            existing[source_id] = result
    atomic_write_text(
        index_path,
        "".join(json.dumps(existing[source_id], ensure_ascii=False, sort_keys=True) + "\n" for source_id in sorted(existing)),
    )


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Refresh local repo cache and graphify outputs.")
    parser.add_argument("--registry", default="references/route-registry.yaml")
    parser.add_argument("--category", action="append", help="Route/category ID to refresh. May be repeated.")
    parser.add_argument("--source", action="append", help="Source ID to refresh. May be repeated.")
    parser.add_argument("--force", action="store_true", help="Refresh even when remote HEAD matches the local worktree.")
    parser.add_argument("--force-graph", action="store_true", help="Rebuild graph artifacts even when graph metadata is current.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    try:
        args = parse_args(argv or sys.argv[1:])
        registry_path = Path(args.registry)
        registry = load_registry(registry_path)
        skill_root = infer_skill_root(registry_path)
        selected = selected_sources(registry, args.category, args.source)
        if not selected:
            raise RefreshError("choose at least one --category or --source")
        results = [
            refresh_source(skill_root, registry, source_id, force=args.force, force_graph=args.force_graph)
            for source_id in selected
        ]
        index_path = safe_cache_path(
            skill_root,
            registry.get("materialization_defaults", {}).get(
                "manifest_index",
                f"{CACHE_ROOT}/indexes/repo-materialization-index.jsonl",
            ),
        )
        index_path.parent.mkdir(parents=True, exist_ok=True)
        merge_manifest_index(index_path, results)
        print(json.dumps({"status": "local_refresh_complete", "results": results}, indent=2, ensure_ascii=False))
        return 0
    except (OSError, RefreshError, yaml.YAMLError, subprocess.SubprocessError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
