#!/usr/bin/env python3
"""Optional network checker for upstream raw-file anchors.

This script verifies that registry read_first and route_index anchors resolve
on GitHub raw URLs for a chosen ref. It is intentionally separate from the
offline validator so CI and local review can stay deterministic.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import PurePosixPath
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlparse
from urllib.request import Request, urlopen

import yaml


def load_registry(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    if not isinstance(data, dict):
        raise ValueError("registry must be a YAML mapping")
    return data


def github_slug(repo_url: str) -> tuple[str, str]:
    parsed = urlparse(repo_url)
    if parsed.scheme != "https" or parsed.hostname != "github.com":
        raise ValueError(f"only https://github.com repos are supported: {repo_url}")
    path = parsed.path.strip("/")
    if path.endswith(".git"):
        path = path[:-4]
    parts = path.split("/")
    if len(parts) != 2 or not all(parts):
        raise ValueError(f"repo URL must identify owner/repo: {repo_url}")
    return parts[0], parts[1]


def validate_anchor_path(source_id: str, path: str) -> None:
    posix = PurePosixPath(path)
    if posix.is_absolute() or ".." in posix.parts or "\\" in path:
        raise ValueError(f"{source_id}: unsafe anchor path: {path}")


def raw_url(owner: str, repo: str, ref: str, path: str) -> str:
    return f"https://raw.githubusercontent.com/{owner}/{repo}/{quote(ref, safe='')}/{quote(path, safe='/')}"


def commit_api_url(owner: str, repo: str, ref: str) -> str:
    return f"https://api.github.com/repos/{owner}/{repo}/commits/{quote(ref, safe='')}"


def contents_api_url(owner: str, repo: str, ref: str, path: str) -> str:
    return f"https://api.github.com/repos/{owner}/{repo}/contents/{quote(path, safe='/')}?ref={quote(ref, safe='')}"


def anchor_exists(url: str, timeout: float) -> tuple[bool, str | None]:
    request = Request(url, method="HEAD")
    try:
        with urlopen(request, timeout=timeout) as response:
            return 200 <= response.status < 400, None
    except HTTPError as exc:
        if exc.code == 405:
            try:
                with urlopen(url, timeout=timeout) as response:
                    return 200 <= response.status < 400, None
            except (HTTPError, URLError, TimeoutError) as fallback_exc:
                return False, str(fallback_exc)
        return False, str(exc)
    except (URLError, TimeoutError) as exc:
        return False, str(exc)


def fetch_json(url: str, timeout: float) -> tuple[dict | None, str | None]:
    request = Request(url, headers={"Accept": "application/vnd.github+json"})
    try:
        with urlopen(request, timeout=timeout) as response:
            data = json.load(response)
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as exc:
        return None, str(exc)
    if not isinstance(data, dict):
        return None, "GitHub API response was not a JSON object"
    return data, None


def resolve_commit(owner: str, repo: str, ref: str, timeout: float) -> tuple[str | None, str | None]:
    data, error = fetch_json(commit_api_url(owner, repo, ref), timeout)
    if error:
        return None, error
    sha = data.get("sha") if isinstance(data, dict) else None
    if isinstance(sha, str) and len(sha) == 40:
        return sha, None
    return None, "GitHub commit response did not include a 40-character sha"


def resolve_blob_sha(owner: str, repo: str, ref: str, path: str, timeout: float) -> tuple[str | None, str | None]:
    data, error = fetch_json(contents_api_url(owner, repo, ref, path), timeout)
    if error:
        return None, error
    sha = data.get("sha") if isinstance(data, dict) else None
    content_type = data.get("type") if isinstance(data, dict) else None
    if content_type != "file":
        return None, f"GitHub contents response type is not file: {content_type}"
    if isinstance(sha, str) and len(sha) == 40:
        return sha, None
    return None, "GitHub contents response did not include a 40-character sha"


def iter_source_anchors(source_id: str, source: dict) -> list[tuple[str, str]]:
    anchors: list[tuple[str, str]] = []
    for path in source.get("read_first") or []:
        if isinstance(path, str):
            anchors.append(("read_first", path))
    route_index = source.get("route_index") or {}
    if isinstance(route_index, dict):
        for key, paths in route_index.items():
            for path in paths or []:
                if isinstance(path, str):
                    anchors.append((key, path))

    seen: set[str] = set()
    unique: list[tuple[str, str]] = []
    for locator, path in anchors:
        if path in seen:
            continue
        validate_anchor_path(source_id, path)
        seen.add(path)
        unique.append((locator, path))
    return unique


def check_registry(registry: dict, ref: str, timeout: float) -> tuple[list[dict], int]:
    sources = registry.get("sources")
    if not isinstance(sources, dict):
        raise ValueError("registry.sources must be a mapping")

    checked_at = datetime.now(timezone.utc).isoformat()
    results: list[dict] = []
    missing = 0
    for source_id, source in sorted(sources.items()):
        if not isinstance(source, dict):
            continue
        owner, repo = github_slug(source.get("repo_url") or source.get("repo") or "")
        anchors = iter_source_anchors(source_id, source)
        resolved_commit, commit_error = resolve_commit(owner, repo, ref, timeout)
        for locator, path in anchors:
            url = raw_url(owner, repo, ref, path)
            exists, error = anchor_exists(url, timeout)
            if not exists:
                missing += 1
            blob_sha = None
            metadata_error = commit_error
            if exists:
                blob_sha, blob_error = resolve_blob_sha(owner, repo, ref, path, timeout)
                metadata_error = commit_error or blob_error
            results.append(
                {
                    "source_id": source_id,
                    "locator": locator,
                    "path": path,
                    "exists": exists,
                    "checked_ref": ref,
                    "checked_at": checked_at,
                    "resolved_commit": resolved_commit,
                    "blob_sha": blob_sha,
                    "url": url,
                    "error": error,
                    "metadata_error": metadata_error,
                }
            )
    return results, missing


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check upstream GitHub raw-file anchors.")
    parser.add_argument("registry", help="Path to references/route-registry.yaml")
    parser.add_argument("--ref", default="main", help="Git ref to check; default: main")
    parser.add_argument("--timeout", type=float, default=15.0, help="Network timeout in seconds")
    parser.add_argument("--json", action="store_true", help="Emit JSON results")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    try:
        args = parse_args(argv or sys.argv[1:])
        registry = load_registry(args.registry)
        results, missing = check_registry(registry, args.ref, args.timeout)
    except (OSError, ValueError, yaml.YAMLError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(results, indent=2, ensure_ascii=False, sort_keys=True))
    else:
        for result in results:
            status = "OK" if result["exists"] else "MISSING"
            print(f"{status}\t{result['source_id']}\t{result['path']}")
            if result["error"]:
                print(f"ERROR\t{result['source_id']}\t{result['error']}", file=sys.stderr)

    return 1 if missing else 0


if __name__ == "__main__":
    raise SystemExit(main())
