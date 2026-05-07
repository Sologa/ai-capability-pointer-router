#!/usr/bin/env python3
"""Read-only validator for the staged ai-capability-pointer-router tree."""

from __future__ import annotations

import re
import json
import subprocess
import sys
from pathlib import Path
from pathlib import PurePosixPath
from urllib.parse import urlparse

import yaml


ROUTE_RE = re.compile(r"^[a-z][a-z0-9_]*$")
SOURCE_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
LOCAL_ROUTE_RE = re.compile(r"^[a-z][a-z0-9_]*$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

ALLOWED_MODES = {
    "pointer_only",
    "materialize_on_first_use",
    "materialize_and_graph_on_first_use",
    "manual_only",
}
ALLOWED_PIN_POLICIES = {"record_resolved_commit", "exact_ref_only"}
ALLOWED_UPDATE_POLICIES = {"fetch_latest_on_explicit_use", "no_auto_update", "manual_refresh_only"}
ALLOWED_GRAPH_MODES = {"locator_only"}
ALLOWED_REF_VALUES = {"main", "tags", "commit_sha"}
CACHE_ROOT = "temp_artifact/repo_pointer_router_cache"
CACHE_PREFIX = f"{CACHE_ROOT}/"
REQUIRED_GITIGNORE_PATTERNS = {
    "._*",
    "__pycache__/",
    ".codex/",
    ".omx/",
    ".pytest_cache/",
    ".mypy_cache/",
    ".ruff_cache/",
    "cache/",
    "temp_artifact/",
    "graphify-out/",
}
SKIP_WALK_DIRS = {
    ".git",
    ".codex",
    ".omx",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "__pycache__",
    "cache",
    "temp_artifact",
    "graphify-out",
}
REQUIRED_SOURCE_FIELDS = {
    "source_id",
    "repo",
    "repo_url",
    "category",
    "source_card_path",
    "authority_level",
    "refresh_sensitivity",
    "stale_after_hours",
    "last_verified",
    "representation",
    "materialization",
    "read_first",
    "do_not_use_for",
}
REQUIRED_SCHEMA_FILES = [
    "schemas/route-registry.schema.json",
    "schemas/materialization-plan.schema.json",
    "schemas/anchor-check-report.schema.json",
]
REQUIRED_PUBLIC_HEALTH_FILES = [
    "README.md",
    "CONTRIBUTING.md",
    "SECURITY.md",
    "CHANGELOG.md",
    "CODE_OF_CONDUCT.md",
    ".github/pull_request_template.md",
    ".github/ISSUE_TEMPLATE/bug_report.md",
    ".github/ISSUE_TEMPLATE/source_update.md",
]
REQUIRED_MATERIALIZATION_FIELDS = {
    "mode",
    "strategy",
    "repo_url",
    "default_ref",
    "allowed_refs",
    "pin_policy",
    "update_policy",
    "manifest",
    "graph",
    "max_files",
    "max_bytes",
}


class ValidationError(Exception):
    pass


def load_yaml(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    if not isinstance(data, dict):
        raise ValidationError(f"{path}: YAML root must be a mapping")
    return data


def read_frontmatter(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return {}
    end = text.find("\n---\n", 4)
    if end == -1:
        return {}
    data = yaml.safe_load(text[4:end])
    return data if isinstance(data, dict) else {}


def load_json(path: Path) -> object:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def rel_exists(root: Path, rel_path: str) -> bool:
    return (root / rel_path).is_file()


def require(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def validate_routes(root: Path, registry: dict, errors: list[str]) -> None:
    routes = registry.get("routes")
    sources = registry.get("sources")
    require(isinstance(routes, dict) and bool(routes), "routes must be a non-empty mapping", errors)
    require(isinstance(sources, dict) and bool(sources), "sources must be a non-empty mapping", errors)
    if not isinstance(routes, dict) or not isinstance(sources, dict):
        return

    for route_id, route in routes.items():
        require(bool(ROUTE_RE.match(route_id)), f"route id must be snake_case: {route_id}", errors)
        require(route.get("route_id") == route_id, f"{route_id}: route_id must match mapping key", errors)
        router_doc = route.get("router_doc")
        require(isinstance(router_doc, str) and rel_exists(root, router_doc), f"{route_id}: router_doc missing: {router_doc}", errors)
        if isinstance(router_doc, str) and rel_exists(root, router_doc):
            validate_category_router_boundary(root, route_id, router_doc, registry, errors)
        route_sources = route.get("sources")
        require(isinstance(route_sources, list) and route_sources, f"{route_id}: sources must be a non-empty list", errors)
        if isinstance(route_sources, list):
            for source_id in route_sources:
                require(source_id in sources, f"{route_id}: unknown source {source_id}", errors)
                source = sources.get(source_id, {})
                require(source.get("category") == route_id, f"{source_id}: category must be {route_id}", errors)

    router_dir = root / "references/category-routers"
    expected_docs = {
        Path(route.get("router_doc", "")).name
        for route in routes.values()
        if isinstance(route, dict) and isinstance(route.get("router_doc"), str)
    }
    actual_docs = {path.name for path in router_dir.glob("*.md") if not path.name.startswith("._")}
    require(
        actual_docs == expected_docs,
        f"category router files must match registry routes exactly: expected {sorted(expected_docs)}, got {sorted(actual_docs)}",
        errors,
    )


def validate_category_router_boundary(root: Path, route_id: str, router_doc: str, registry: dict, errors: list[str]) -> None:
    text = (root / router_doc).read_text(encoding="utf-8")
    sources = registry.get("sources") if isinstance(registry.get("sources"), dict) else {}
    route_index_keys: list[str] = []
    for source in sources.values():
        if isinstance(source, dict) and isinstance(source.get("route_index"), dict):
            route_index_keys.extend(source["route_index"].keys())

    for key in route_index_keys:
        require(key not in text, f"{route_id}: category router must not list third-layer route index key {key}", errors)
    require("## Route Index" not in text, f"{route_id}: category router must not contain a Route Index section", errors)
    require("scoped files" not in text, f"{route_id}: category router must not instruct direct scoped file reads", errors)


def validate_repo_url(source_id: str, repo_url: object, registry: dict, field: str, errors: list[str]) -> None:
    require(isinstance(repo_url, str) and bool(repo_url), f"{source_id}: {field} must be a non-empty string", errors)
    if not isinstance(repo_url, str) or not repo_url:
        return
    parsed = urlparse(repo_url)
    require(parsed.scheme == "https", f"{source_id}: {field} scheme must be https: {repo_url}", errors)
    allowlist = registry.get("materialization_defaults", {}).get("host_allowlist", [])
    require(isinstance(allowlist, list), "materialization_defaults.host_allowlist must be a list", errors)
    if isinstance(allowlist, list):
        require(parsed.hostname in set(allowlist), f"{source_id}: {field} host is not allowlisted: {repo_url}", errors)


def github_repo_slug(repo_url: str) -> tuple[str, str] | None:
    parsed = urlparse(repo_url)
    path = parsed.path.strip("/")
    if path.endswith(".git"):
        path = path[:-4]
    parts = path.split("/")
    if len(parts) != 2 or not all(parts):
        return None
    return parts[0], parts[1]


def validate_display_repo_url(source_id: str, source: dict, registry: dict, errors: list[str]) -> None:
    repo = source.get("repo")
    repo_url = source.get("repo_url")
    materialization = source.get("materialization") if isinstance(source.get("materialization"), dict) else {}
    materialization_repo_url = materialization.get("repo_url") if isinstance(materialization, dict) else None

    validate_repo_url(source_id, repo, registry, "source.repo", errors)
    if isinstance(repo, str):
        require(not repo.endswith(".git"), f"{source_id}: source.repo must be a display URL without .git suffix", errors)

    if isinstance(repo, str) and isinstance(repo_url, str):
        require(
            github_repo_slug(repo) == github_repo_slug(repo_url),
            f"{source_id}: source.repo and source.repo_url must point to the same GitHub repo",
            errors,
        )
    if isinstance(repo, str) and isinstance(materialization_repo_url, str):
        require(
            github_repo_slug(repo) == github_repo_slug(materialization_repo_url),
            f"{source_id}: source.repo and materialization.repo_url must point to the same GitHub repo",
            errors,
        )


def validate_locator_path(source_id: str, field: str, value: object, errors: list[str]) -> None:
    require(isinstance(value, str) and bool(value), f"{source_id}: {field} must be a non-empty string", errors)
    if not isinstance(value, str) or not value:
        return
    path = PurePosixPath(value)
    require(not path.is_absolute(), f"{source_id}: {field} must be relative: {value}", errors)
    require(".." not in path.parts, f"{source_id}: {field} must not contain '..': {value}", errors)
    require("\\" not in value, f"{source_id}: {field} must use POSIX path separators: {value}", errors)


def validate_cache_path(source_id: str, field: str, value: str, errors: list[str], *, allow_root: bool = False) -> None:
    validate_locator_path(source_id, field, value, errors)
    if not isinstance(value, str):
        return
    if allow_root and value == CACHE_ROOT:
        return
    require(
        value.startswith(CACHE_PREFIX),
        f"{source_id}: {field} must stay under {CACHE_PREFIX}: {value}",
        errors,
    )


def validate_materialization_defaults(registry: dict, errors: list[str]) -> None:
    defaults = registry.get("materialization_defaults")
    require(isinstance(defaults, dict), "materialization_defaults must be a mapping", errors)
    if not isinstance(defaults, dict):
        return
    validate_cache_path("defaults", "cache_root", defaults.get("cache_root"), errors, allow_root=True)
    validate_cache_path("defaults", "manifest_index", defaults.get("manifest_index"), errors)
    allowed_modes = defaults.get("allowed_modes")
    require(isinstance(allowed_modes, list), "materialization_defaults.allowed_modes must be a list", errors)
    if isinstance(allowed_modes, list):
        require(set(allowed_modes) == ALLOWED_MODES, "materialization_defaults.allowed_modes must match validator modes", errors)
    allowed_refs = defaults.get("allowed_refs")
    require(isinstance(allowed_refs, list), "materialization_defaults.allowed_refs must be a list", errors)
    if isinstance(allowed_refs, list):
        require(set(allowed_refs) <= ALLOWED_REF_VALUES, "materialization_defaults.allowed_refs has unsupported values", errors)


def validate_graph_scope(source_id: str, graph: dict, errors: list[str]) -> None:
    scope = graph.get("scope")
    require(isinstance(scope, dict), f"{source_id}: graph.scope must be a mapping", errors)
    if not isinstance(scope, dict):
        return
    include = scope.get("include")
    exclude = scope.get("exclude")
    require(isinstance(include, list), f"{source_id}: graph.scope.include must be a list", errors)
    require(isinstance(exclude, list), f"{source_id}: graph.scope.exclude must be a list", errors)
    if isinstance(include, list):
        for idx, item in enumerate(include):
            validate_locator_path(source_id, f"graph.scope.include[{idx}]", item, errors)
    if isinstance(exclude, list):
        for idx, item in enumerate(exclude):
            validate_locator_path(source_id, f"graph.scope.exclude[{idx}]", item, errors)
    if graph.get("enabled"):
        require(bool(include), f"{source_id}: enabled graph requires non-empty scope.include", errors)


def validate_materialization(source_id: str, source: dict, registry: dict, materialization: dict, errors: list[str]) -> None:
    missing = sorted(REQUIRED_MATERIALIZATION_FIELDS - set(materialization))
    require(not missing, f"{source_id}: materialization missing fields: {', '.join(missing)}", errors)

    mode = materialization.get("mode")
    require(mode in ALLOWED_MODES, f"{source_id}: invalid materialization.mode {mode}", errors)
    require(materialization.get("pin_policy") in ALLOWED_PIN_POLICIES, f"{source_id}: invalid pin_policy", errors)
    require(materialization.get("update_policy") in ALLOWED_UPDATE_POLICIES, f"{source_id}: invalid update_policy", errors)
    require(materialization.get("default_ref") == "main", f"{source_id}: default_ref must be main in staged draft", errors)
    allowed_refs = materialization.get("allowed_refs")
    require(isinstance(allowed_refs, list) and set(allowed_refs) <= ALLOWED_REF_VALUES, f"{source_id}: invalid allowed_refs", errors)

    validate_repo_url(source_id, source.get("repo_url"), registry, "source.repo_url", errors)
    validate_repo_url(source_id, materialization.get("repo_url"), registry, "materialization.repo_url", errors)
    validate_display_repo_url(source_id, source, registry, errors)
    if isinstance(source.get("repo_url"), str) and isinstance(materialization.get("repo_url"), str):
        require(source.get("repo_url") == materialization.get("repo_url"), f"{source_id}: source.repo_url and materialization.repo_url must match", errors)

    manifest = materialization.get("manifest")
    require(isinstance(manifest, dict) and isinstance(manifest.get("path"), str) and bool(manifest.get("path")), f"{source_id}: materialization.manifest.path required", errors)
    if isinstance(manifest, dict) and isinstance(manifest.get("path"), str):
        validate_cache_path(source_id, "manifest.path", manifest["path"], errors)

    graph = materialization.get("graph")
    require(isinstance(graph, dict), f"{source_id}: materialization.graph must be a mapping", errors)
    if isinstance(graph, dict):
        require(graph.get("mode") in ALLOWED_GRAPH_MODES, f"{source_id}: graph.mode must be locator_only", errors)
        validate_graph_scope(source_id, graph, errors)

    for key in ("max_files", "max_bytes"):
        value = materialization.get(key)
        require(isinstance(value, int) and value > 0, f"{source_id}: {key} must be positive integer", errors)


def source_anchor_paths(source: dict) -> list[str]:
    paths: list[str] = []
    for anchor in source.get("read_first") or []:
        if isinstance(anchor, str):
            paths.append(anchor)
    route_index = source.get("route_index") or {}
    if isinstance(route_index, dict):
        for anchors in route_index.values():
            if isinstance(anchors, list):
                for anchor in anchors:
                    if isinstance(anchor, str):
                        paths.append(anchor)
    seen: set[str] = set()
    unique: list[str] = []
    for path in paths:
        if path in seen:
            continue
        seen.add(path)
        unique.append(path)
    return unique


def validate_last_verified(source_id: str, source: dict, errors: list[str]) -> None:
    last_verified = source.get("last_verified")
    require(isinstance(last_verified, dict), f"{source_id}: last_verified must be a mapping", errors)
    if not isinstance(last_verified, dict):
        return
    require(bool(DATE_RE.match(str(last_verified.get("date", "")))), f"{source_id}: last_verified.date must be YYYY-MM-DD", errors)
    require(last_verified.get("method") == "github_raw_head", f"{source_id}: last_verified.method must be github_raw_head", errors)
    require(isinstance(last_verified.get("checked_ref"), str) and bool(last_verified.get("checked_ref")), f"{source_id}: last_verified.checked_ref must be non-empty string", errors)
    checked_paths = last_verified.get("checked_paths")
    require(isinstance(checked_paths, list) and all(isinstance(item, str) for item in checked_paths), f"{source_id}: last_verified.checked_paths must be a string list", errors)
    if isinstance(checked_paths, list):
        expected = set(source_anchor_paths(source))
        actual = set(checked_paths)
        require(
            actual == expected,
            f"{source_id}: last_verified.checked_paths must match read_first and route_index anchors exactly",
            errors,
        )


def validate_route_index(source_id: str, source: dict, errors: list[str]) -> None:
    route_index = source.get("route_index")
    if route_index is None:
        return
    require(isinstance(route_index, dict), f"{source_id}: route_index must be a mapping", errors)
    if not isinstance(route_index, dict):
        return
    for key, paths in route_index.items():
        prefix = f"{source_id}/"
        require(key.startswith(prefix), f"{source_id}: route_index key must start with {prefix}: {key}", errors)
        local_route = key[len(prefix) :] if key.startswith(prefix) else key
        require(bool(LOCAL_ROUTE_RE.match(local_route)), f"{source_id}: local route must be snake_case: {key}", errors)
        require(isinstance(paths, list) and all(isinstance(item, str) and item for item in paths), f"{source_id}: route_index[{key}] must be a non-empty string list", errors)
        if isinstance(paths, list):
            for idx, item in enumerate(paths):
                validate_locator_path(source_id, f"route_index[{key}][{idx}]", item, errors)


def validate_sources(root: Path, registry: dict, errors: list[str]) -> None:
    routes = registry.get("routes")
    sources = registry.get("sources")
    if not isinstance(routes, dict) or not isinstance(sources, dict):
        return

    listed_sources = {source_id for route in routes.values() for source_id in (route.get("sources") or [])}
    source_card_paths: set[str] = set()
    expected_card_basenames: set[str] = set()

    for source_id, source in sources.items():
        require(bool(SOURCE_RE.match(source_id)), f"source id must be lowercase kebab-case: {source_id}", errors)
        missing = sorted(REQUIRED_SOURCE_FIELDS - set(source))
        require(not missing, f"{source_id}: missing source fields: {', '.join(missing)}", errors)
        require(source.get("source_id") == source_id, f"{source_id}: source_id must match mapping key", errors)
        require(source_id in listed_sources, f"{source_id}: source is not listed by any route", errors)

        category = source.get("category")
        require(category in routes, f"{source_id}: category does not exist: {category}", errors)

        card_path = source.get("source_card_path")
        require(isinstance(card_path, str), f"{source_id}: source_card_path must be a string", errors)
        if isinstance(card_path, str):
            require(card_path not in source_card_paths, f"{source_id}: duplicate source_card_path {card_path}", errors)
            source_card_paths.add(card_path)
            expected_card_basenames.add(f"{source_id}.md")
            full_card_path = root / card_path
            require(full_card_path.is_file(), f"{source_id}: source card missing: {card_path}", errors)
            if full_card_path.is_file():
                frontmatter = read_frontmatter(full_card_path)
                require(frontmatter.get("source_id") == source_id, f"{source_id}: card frontmatter source_id mismatch", errors)
                require(frontmatter.get("category") == category, f"{source_id}: card frontmatter category mismatch", errors)
                validate_source_card_content(source_id, full_card_path, source, errors)

        read_first = source.get("read_first")
        require(isinstance(read_first, list) and read_first, f"{source_id}: read_first must be a non-empty list", errors)
        do_not_use_for = source.get("do_not_use_for")
        require(isinstance(do_not_use_for, list), f"{source_id}: do_not_use_for must be a list", errors)
        validate_last_verified(source_id, source, errors)

        materialization = source.get("materialization")
        require(isinstance(materialization, dict), f"{source_id}: materialization must be a mapping", errors)
        if isinstance(materialization, dict):
            validate_materialization(source_id, source, registry, materialization, errors)
        validate_route_index(source_id, source, errors)

    source_card_dir = root / "references/source-cards"
    actual_cards = {path.name for path in source_card_dir.glob("*.md") if not path.name.startswith("._")}
    require(actual_cards == expected_card_basenames, f"source-cards files must match sources exactly: expected {sorted(expected_card_basenames)}, got {sorted(actual_cards)}", errors)


def validate_root_files(root: Path, errors: list[str]) -> None:
    required_files = [
        "SKILL.md",
        *REQUIRED_PUBLIC_HEALTH_FILES,
        *REQUIRED_SCHEMA_FILES,
        "agents/openai.yaml",
        "references/route-registry.yaml",
        "references/runtime-protocol.md",
        "references/evidence-rules.md",
        "references/materialization-pipeline.md",
        "scripts/materialize_repo_pointer.py",
        "validation/validate_router_tree.py",
        "validation/qa_prompts.md",
    ]
    for rel_path in required_files:
        require((root / rel_path).is_file(), f"required file missing: {rel_path}", errors)

    for rel_path in REQUIRED_SCHEMA_FILES:
        schema_path = root / rel_path
        if schema_path.is_file():
            try:
                data = load_json(schema_path)
                require(isinstance(data, dict), f"{rel_path}: schema root must be a JSON object", errors)
                require(isinstance(data, dict) and data.get("$schema"), f"{rel_path}: schema must declare $schema", errors)
            except (OSError, json.JSONDecodeError) as exc:
                errors.append(f"{rel_path}: invalid JSON schema: {exc}")

    skill_text = (root / "SKILL.md").read_text(encoding="utf-8") if (root / "SKILL.md").is_file() else ""
    require(
        "route-registry.yaml" in skill_text and "category source of truth" in skill_text,
        "SKILL.md must name route-registry.yaml as category source of truth",
        errors,
    )
    require("docs/ 下" not in skill_text, "SKILL.md must not claim the published root lives under docs/", errors)

    gitignore = root / ".gitignore"
    require(gitignore.is_file(), "required file missing: .gitignore", errors)
    if gitignore.is_file():
        patterns = set(gitignore.read_text(encoding="utf-8").splitlines())
        missing_patterns = sorted(REQUIRED_GITIGNORE_PATTERNS - patterns)
        require(not missing_patterns, f".gitignore missing generated-artifact exclusions: {', '.join(missing_patterns)}", errors)

    openai_yaml = root / "agents/openai.yaml"
    if openai_yaml.is_file():
        try:
            data = load_yaml(openai_yaml)
            allow = data.get("policy", {}).get("allow_implicit_invocation")
            require(allow is False, "agents/openai.yaml must set policy.allow_implicit_invocation: false for staged draft", errors)
        except (OSError, yaml.YAMLError, ValidationError) as exc:
            errors.append(f"agents/openai.yaml invalid: {exc}")

    for path in root.rglob("*"):
        rel_parts = path.relative_to(root).parts
        if any(part in SKIP_WALK_DIRS for part in rel_parts):
            continue
        require(not path.is_symlink(), f"draft skill must not contain symlink: {path.relative_to(root)}", errors)
        require(not path.name.startswith("._"), f"draft skill must not contain macOS sidecar file: {path.relative_to(root)}", errors)


def validate_skill_category_sync(root: Path, registry: dict, errors: list[str]) -> None:
    routes = registry.get("routes")
    if not isinstance(routes, dict):
        return
    skill_path = root / "SKILL.md"
    if not skill_path.is_file():
        return
    text = skill_path.read_text(encoding="utf-8")
    match = re.search(r"^## Category\n(?P<body>.*?)(?:^## |\Z)", text, flags=re.MULTILINE | re.DOTALL)
    require(match is not None, "SKILL.md must contain a Category section", errors)
    if match is None:
        return
    listed = set(re.findall(r"^- `([^`]+)`:", match.group("body"), flags=re.MULTILINE))
    expected = set(routes)
    require(
        listed == expected,
        f"SKILL.md category bullets must match registry routes exactly: expected {sorted(expected)}, got {sorted(listed)}",
        errors,
    )


def validate_source_card_content(source_id: str, card_path: Path, source: dict, errors: list[str]) -> None:
    text = card_path.read_text(encoding="utf-8")
    rel = card_path.name
    lowered = text.lower()
    require("locator" in lowered and "evidence" in lowered, f"{source_id}: source card must state locator/evidence boundary", errors)

    for anchor in source.get("read_first") or []:
        require(anchor in text, f"{source_id}: source card missing read_first anchor {anchor}", errors)

    route_index = source.get("route_index") or {}
    if isinstance(route_index, dict):
        expected_keys = set(route_index)
        found_keys = set(re.findall(rf"`({re.escape(source_id)}/[^`\s]+)`", text))
        invalid_keys = sorted(
            key for key in found_keys
            if "/" in key and not LOCAL_ROUTE_RE.match(key.split("/", 1)[1])
        )
        extra_keys = sorted(key for key in found_keys - expected_keys if key not in invalid_keys)
        require(not invalid_keys, f"{source_id}: source card contains invalid route_index key syntax: {', '.join(invalid_keys)}", errors)
        require(not extra_keys, f"{source_id}: source card contains route_index keys not in registry: {', '.join(extra_keys)}", errors)
        for key, anchors in route_index.items():
            require(key in text, f"{source_id}: source card missing route_index key {key}", errors)
            if isinstance(anchors, list):
                for anchor in anchors:
                    require(anchor in text, f"{source_id}: source card missing route_index anchor {key} -> {anchor}", errors)


def validate_dry_run(root: Path, registry_path: Path, registry: dict, errors: list[str]) -> None:
    script = root / "scripts/materialize_repo_pointer.py"
    sources = registry.get("sources")
    if not script.is_file() or not isinstance(sources, dict):
        return

    for source_id in sorted(sources):
        proc = subprocess.run(
            [
                sys.executable,
                str(script),
                "--registry",
                str(registry_path),
                "--source",
                source_id,
                "--dry-run",
                "--offline-ok",
            ],
            cwd=root.resolve(),
            text=True,
            capture_output=True,
            check=False,
        )
        if proc.returncode != 0:
            errors.append(f"{source_id}: dry-run failed: {proc.stderr.strip() or proc.stdout.strip()}")
            continue
        try:
            plan = json.loads(proc.stdout)
        except json.JSONDecodeError as exc:
            errors.append(f"{source_id}: dry-run did not emit JSON: {exc}")
            continue
        require(plan.get("status") == "dry_run_plan", f"{source_id}: dry-run status must be dry_run_plan", errors)
        for key in ("clone", "fetch", "run_package_install", "run_repo_scripts", "run_hooks"):
            require(plan.get("safety", {}).get(key) is False, f"{source_id}: dry-run safety.{key} must be false", errors)
        require("stale_after_hours" in plan, f"{source_id}: dry-run plan missing stale_after_hours", errors)
        require("allowed_refs" in plan, f"{source_id}: dry-run plan missing allowed_refs", errors)
        require("manifest_exists" in plan.get("paths", {}), f"{source_id}: dry-run plan missing paths.manifest_exists", errors)

    first_source = sorted(sources)[0] if sources else None
    if first_source:
        proc = subprocess.run(
            [
                sys.executable,
                str(script),
                "--registry",
                str(registry_path),
                "--source",
                first_source,
                "--write-cache",
                "--offline-ok",
            ],
            cwd=root.resolve(),
            text=True,
            capture_output=True,
            check=False,
        )
        require(proc.returncode == 2, "write-cache mode must be rejected in staged draft", errors)
        require("not implemented" in proc.stderr, "write-cache rejection must explain that it is not implemented", errors)


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    if len(args) != 1:
        print("usage: validate_router_tree.py <skill-root>", file=sys.stderr)
        return 2

    root = Path(args[0])
    errors: list[str] = []
    validate_root_files(root, errors)

    registry_path = root / "references/route-registry.yaml"
    if registry_path.is_file():
        try:
            registry = load_yaml(registry_path)
            validate_materialization_defaults(registry, errors)
            validate_skill_category_sync(root, registry, errors)
            validate_routes(root, registry, errors)
            validate_sources(root, registry, errors)
            validate_dry_run(root, registry_path, registry, errors)
        except (OSError, yaml.YAMLError, ValidationError) as exc:
            errors.append(str(exc))

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    print(f"OK: router tree valid: {root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
