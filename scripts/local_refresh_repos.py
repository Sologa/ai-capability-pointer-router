#!/usr/bin/env python3
"""Local-only repo cache refresher for ai-capability-pointer-router.

This script is intentionally local-output only. It clones or refreshes registered
GitHub repos under temp_artifact/repo_pointer_router_cache/, writes locator
manifests, and runs the non-LLM graphify code rebuild when graphify is available.
Generated repos and graph outputs are ignored by git.
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
CACHE_ROOT = "temp_artifact/repo_pointer_router_cache"
CACHE_PREFIX = f"{CACHE_ROOT}/"
ALLOWED_REF_VALUES = {"main", "tags", "commit_sha"}


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


def scope_excludes(rel_path: Path, patterns: list[str]) -> bool:
    path_text = rel_path.as_posix()
    for pattern in patterns:
        if pattern in rel_path.parts:
            return True
        if fnmatch.fnmatch(path_text, pattern) or fnmatch.fnmatch(rel_path.name, pattern):
            return True
    return False


def clone_or_refresh(source_id: str, repo_url: str, worktree: Path, ref: str) -> dict:
    worktree.parent.mkdir(parents=True, exist_ok=True)
    if (worktree / ".git").is_dir():
        action = "refresh"
        run(["git", "-C", str(worktree), "remote", "set-url", "origin", repo_url])
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
    return {"action": action, "resolved_commit": commit}


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


def run_graphify_code(worktree: Path, materialization: dict) -> dict:
    out = worktree / "graphify-out"
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(exist_ok=True)
    try:
        from graphify.detect import classify_file, detect
        from graphify.export import to_json
        import networkx as nx
    except Exception as exc:
        atomic_write_text(
            out / "GRAPH_REPORT.md",
            f"# Graphify Status\n\nGraphify is not importable in this Python environment: {exc}\n",
        )
        return {"status": "graphify_unavailable", "error": str(exc), "graph_json": None}

    graph = materialization.get("graph") if isinstance(materialization.get("graph"), dict) else {}
    scope = graph.get("scope") if isinstance(graph.get("scope"), dict) else {}
    includes = scope.get("include") or ["."]
    excludes = scope.get("exclude") or []
    code_files: list[Path] = []
    doc_files: list[Path] = []
    seen: set[Path] = set()

    for include in includes:
        scan_root = worktree / include
        if not scan_root.exists():
            continue
        if scan_root.is_file():
            detected_files = {"code": [], "document": [], "paper": [], "image": []}
            file_type = classify_file(scan_root)
            if file_type is not None:
                detected_files[file_type.value if hasattr(file_type, "value") else str(file_type)].append(str(scan_root))
        else:
            detected_files = detect(scan_root, follow_symlinks=False).get("files", {})
        for file_type, target in (
            ("code", code_files),
            ("document", doc_files),
            ("paper", doc_files),
            ("image", doc_files),
        ):
            for item in detected_files.get(file_type, []):
                path = Path(item).resolve()
                try:
                    rel = path.relative_to(worktree.resolve())
                except ValueError:
                    continue
                if scope_excludes(rel, excludes):
                    continue
                if path in seen:
                    continue
                seen.add(path)
                target.append(path)

    scanned_files = list(code_files) + list(doc_files)
    total_bytes = 0
    for item in scanned_files:
        try:
            total_bytes += Path(item).stat().st_size
        except OSError:
            continue
    max_files = materialization.get("max_files")
    max_bytes = materialization.get("max_bytes")
    if isinstance(max_files, int) and len(scanned_files) > max_files:
        atomic_write_text(
            out / "GRAPH_REPORT.md",
            f"# Graphify Status\n\nGraphify rebuild skipped: {len(scanned_files)} supported files exceed max_files={max_files}.\n",
        )
        return {
            "status": "budget_exceeded",
            "reason": "max_files",
            "supported_files": len(scanned_files),
            "max_files": max_files,
            "graph_json": None,
            "graph_report": str(out / "GRAPH_REPORT.md"),
        }
    if isinstance(max_bytes, int) and total_bytes > max_bytes:
        atomic_write_text(
            out / "GRAPH_REPORT.md",
            f"# Graphify Status\n\nGraphify rebuild skipped: {total_bytes} bytes exceed max_bytes={max_bytes}.\n",
        )
        return {
            "status": "budget_exceeded",
            "reason": "max_bytes",
            "supported_bytes": total_bytes,
            "max_bytes": max_bytes,
            "graph_json": None,
            "graph_report": str(out / "GRAPH_REPORT.md"),
        }
    graph_obj = nx.Graph()
    root_id = f"source:{worktree.parent.name}"
    graph_obj.add_node(
        root_id,
        label=worktree.parent.name,
        file_type="source",
        source_file="",
        locator_only=True,
    )
    for path in scanned_files:
        rel = path.relative_to(worktree)
        rel_text = rel.as_posix()
        node_id = f"file:{rel_text}"
        file_type = "code" if path in code_files else "document"
        graph_obj.add_node(
            node_id,
            label=rel_text,
            file_type=file_type,
            source_file=rel_text,
            locator_only=True,
        )
        graph_obj.add_edge(
            root_id,
            node_id,
            relation="contains",
            confidence="EXTRACTED",
            confidence_score=1.0,
            source_file=rel_text,
            weight=1.0,
        )
    communities = {0: list(graph_obj.nodes)}
    to_json(graph_obj, communities, str(out / "graph.json"))
    status = "locator_graph_updated"
    atomic_write_text(
        out / "GRAPH_REPORT.md",
        "\n".join(
            [
                "# Graphify Status",
                "",
                "Deterministic local locator graph rebuilt for the refreshed worktree.",
                "",
                f"- Files indexed: {len(scanned_files)}",
                f"- Code files: {len(code_files)}",
                f"- Docs/papers/images needing semantic graphify: {len(doc_files)}",
                "- Semantics: locator_only",
                "",
                "This graph locates files only. It is not behavioral evidence.",
                "Full semantic graphify still requires /graphify or a future non-agent graphify CLI.",
                "",
            ]
        ),
    )

    if doc_files:
        atomic_write_text(
            out / "needs_semantic_graphify",
            "This repo has docs/papers/images. Full semantic graphify still requires /graphify or a future non-agent graphify CLI.\n",
        )

    return {
        "status": status,
        "code_files": len(code_files),
        "non_code_files_needing_semantic_graphify": len(doc_files),
        "graph_json": str(out / "graph.json") if (out / "graph.json").is_file() else None,
        "graph_report": str(out / "GRAPH_REPORT.md") if (out / "GRAPH_REPORT.md").is_file() else None,
        "needs_semantic_graphify": bool(doc_files),
    }


def refresh_source(skill_root: Path, registry: dict, source_id: str) -> dict:
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

    git_state = clone_or_refresh(source_id, repo_url, worktree, ref)
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
        "worktree_path": str(worktree.relative_to(skill_root)),
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
        "worktree_path": str(worktree.relative_to(skill_root)),
        "safety": safety,
    }

    manifest_path = source.get("materialization", {}).get("manifest", {}).get("path")
    if not isinstance(manifest_path, str):
        manifest_path = str((repo_dir / "materialization.json").relative_to(skill_root))
    atomic_write_json(safe_cache_path(skill_root, manifest_path), manifest)
    atomic_write_json(repo_dir / "git_state.json", git_state_doc)
    atomic_write_json(repo_dir / "route_index.json", build_route_index_artifact(source_id, source, resolved_commit))
    graph_status = run_graphify_code(worktree, materialization)

    return {
        "source_id": source_id,
        "action": git_state["action"],
        "repo_url": repo_url,
        "resolved_commit": resolved_commit,
        "worktree": str(worktree.relative_to(skill_root)),
        "manifest": manifest_path,
        "git_state": str((repo_dir / "git_state.json").relative_to(skill_root)),
        "route_index": str((repo_dir / "route_index.json").relative_to(skill_root)),
        "graphify": graph_status,
    }


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Refresh local repo cache and graphify outputs.")
    parser.add_argument("--registry", default="references/route-registry.yaml")
    parser.add_argument("--source", action="append", help="Source ID to refresh. May be repeated.")
    parser.add_argument("--all", action="store_true", help="Refresh all registry sources.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    try:
        args = parse_args(argv or sys.argv[1:])
        registry_path = Path(args.registry)
        registry = load_registry(registry_path)
        skill_root = infer_skill_root(registry_path)
        sources = registry.get("sources")
        if not isinstance(sources, dict):
            raise RefreshError("registry.sources must be a mapping")
        selected = sorted(sources) if args.all else args.source
        if not selected:
            raise RefreshError("choose --all or at least one --source")
        results = [refresh_source(skill_root, registry, source_id) for source_id in selected]
        index_path = safe_cache_path(
            skill_root,
            registry.get("materialization_defaults", {}).get(
                "manifest_index",
                f"{CACHE_ROOT}/indexes/repo-materialization-index.jsonl",
            ),
        )
        index_path.parent.mkdir(parents=True, exist_ok=True)
        atomic_write_text(
            index_path,
            "".join(json.dumps(result, ensure_ascii=False, sort_keys=True) + "\n" for result in results),
        )
        print(json.dumps({"status": "local_refresh_complete", "results": results}, indent=2, ensure_ascii=False))
        return 0
    except (OSError, RefreshError, yaml.YAMLError, subprocess.SubprocessError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
