from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator, FormatChecker


REPO_ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = REPO_ROOT / "validation" / "validate_router_tree.py"
MATERIALIZER = REPO_ROOT / "scripts" / "materialize_repo_pointer.py"
LOCAL_REFRESH = REPO_ROOT / "scripts" / "local_refresh_repos.py"
UPSTREAM_CHECKER = REPO_ROOT / "validation" / "check_upstream_anchors.py"


def copy_repo() -> tempfile.TemporaryDirectory[str]:
    temp = tempfile.TemporaryDirectory()
    dst = Path(temp.name) / "skill"
    shutil.copytree(
        REPO_ROOT,
        dst,
        ignore=shutil.ignore_patterns(
            ".git",
            "._*",
            ".DS_Store",
            "__pycache__",
            ".pytest_cache",
            ".mypy_cache",
            ".ruff_cache",
            ".omx",
            ".codex",
            "cache",
            "temp_artifact",
            "graphify-out",
        ),
    )
    return temp


def load_registry(root: Path) -> dict:
    with (root / "references/route-registry.yaml").open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    assert isinstance(data, dict)
    return data


def write_registry(root: Path, data: dict) -> None:
    with (root / "references/route-registry.yaml").open("w", encoding="utf-8") as handle:
        yaml.safe_dump(data, handle, allow_unicode=True, sort_keys=False)


class RouterTreeValidationTests(unittest.TestCase):
    def run_validator(self, root: Path) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(VALIDATOR), str(root)],
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
            check=False,
        )

    def run_materializer(self, root: Path, source: str) -> subprocess.CompletedProcess[str]:
        return self.run_materializer_args(
            root,
            "--source",
            source,
            "--dry-run",
            "--offline-ok",
        )

    def run_materializer_args(self, root: Path, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [
                sys.executable,
                str(MATERIALIZER),
                "--registry",
                str(root / "references/route-registry.yaml"),
                *args,
            ],
            cwd=root,
            text=True,
            capture_output=True,
            check=False,
        )

    def run_materializer_from_cwd(self, root: Path, source: str, cwd: Path) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [
                sys.executable,
                str(MATERIALIZER),
                "--registry",
                str(root / "references/route-registry.yaml"),
                "--source",
                source,
                "--dry-run",
                "--offline-ok",
            ],
            cwd=cwd,
            text=True,
            capture_output=True,
            check=False,
        )

    def import_local_refresh(self):
        import importlib.util

        spec = importlib.util.spec_from_file_location("local_refresh_repos", LOCAL_REFRESH)
        self.assertIsNotNone(spec)
        module = importlib.util.module_from_spec(spec)
        assert spec and spec.loader
        spec.loader.exec_module(module)
        return module

    def test_current_tree_is_valid(self) -> None:
        with copy_repo() as temp:
            root = Path(temp) / "skill"
            proc = self.run_validator(root)
            self.assertEqual(proc.returncode, 0, proc.stderr)

    def test_router_frontmatter_source_drift_fails(self) -> None:
        with copy_repo() as temp:
            root = Path(temp) / "skill"
            router = root / "references/category-routers/skill_building.md"
            router.write_text(
                router.read_text(encoding="utf-8").replace("  - openai-skills\n", ""),
                encoding="utf-8",
            )
            proc = self.run_validator(root)
            self.assertNotEqual(proc.returncode, 0)
            self.assertIn("router frontmatter sources must match registry", proc.stderr)

    def test_category_router_raw_anchor_leakage_fails(self) -> None:
        with copy_repo() as temp:
            root = Path(temp) / "skill"
            router = root / "references/category-routers/skill_building.md"
            router.write_text(
                router.read_text(encoding="utf-8") + "\nDirect raw path leak: `docs/specification.mdx`.\n",
                encoding="utf-8",
            )
            proc = self.run_validator(root)
            self.assertNotEqual(proc.returncode, 0)
            self.assertIn("category router must not contain raw source anchor path", proc.stderr)

    def test_source_card_frontmatter_identity_drift_fails(self) -> None:
        with copy_repo() as temp:
            root = Path(temp) / "skill"
            card = root / "references/source-cards/promptfoo-promptfoo.md"
            card.write_text(
                card.read_text(encoding="utf-8").replace(
                    "authority_level: eval_redteam_framework",
                    "authority_level: generic_eval_tool",
                ),
                encoding="utf-8",
            )
            proc = self.run_validator(root)
            self.assertNotEqual(proc.returncode, 0)
            self.assertIn("source card frontmatter authority_level must match registry", proc.stderr)

    def test_source_card_frontmatter_source_id_mismatch_fails(self) -> None:
        with copy_repo() as temp:
            root = Path(temp) / "skill"
            card = root / "references/source-cards/promptfoo-promptfoo.md"
            card.write_text(
                card.read_text(encoding="utf-8").replace(
                    "source_id: promptfoo-promptfoo",
                    "source_id: promptfoo-other",
                    1,
                ),
                encoding="utf-8",
            )
            proc = self.run_validator(root)
            self.assertNotEqual(proc.returncode, 0)
            self.assertIn("card frontmatter source_id mismatch", proc.stderr)

    def test_extra_source_card_route_key_fails(self) -> None:
        with copy_repo() as temp:
            root = Path(temp) / "skill"
            card = root / "references/source-cards/promptfoo-promptfoo.md"
            card.write_text(
                card.read_text(encoding="utf-8")
                + "\n- `promptfoo-promptfoo/unregistered`\n  - `README.md`\n",
                encoding="utf-8",
            )
            proc = self.run_validator(root)
            self.assertNotEqual(proc.returncode, 0)
            self.assertIn("route_index keys not in registry", proc.stderr)

    def test_invalid_source_card_route_key_syntax_fails(self) -> None:
        with copy_repo() as temp:
            root = Path(temp) / "skill"
            card = root / "references/source-cards/promptfoo-promptfoo.md"
            card.write_text(
                card.read_text(encoding="utf-8")
                + "\n- `promptfoo-promptfoo/bad-route`\n  - `README.md`\n",
                encoding="utf-8",
            )
            proc = self.run_validator(root)
            self.assertNotEqual(proc.returncode, 0)
            self.assertIn("invalid route_index key syntax", proc.stderr)

    def test_unbackticked_route_like_text_is_not_treated_as_declared_route_key(self) -> None:
        with copy_repo() as temp:
            root = Path(temp) / "skill"
            card = root / "references/source-cards/promptfoo-promptfoo.md"
            card.write_text(
                card.read_text(encoding="utf-8")
                + "\nPlain prose mention: promptfoo-promptfoo/not_a_declared_key.\n",
                encoding="utf-8",
            )
            proc = self.run_validator(root)
            self.assertEqual(proc.returncode, 0, proc.stderr)

    def test_unsafe_default_cache_root_fails(self) -> None:
        with copy_repo() as temp:
            root = Path(temp) / "skill"
            registry = load_registry(root)
            registry["materialization_defaults"]["cache_root"] = "../router-cache"
            write_registry(root, registry)
            proc = self.run_validator(root)
            self.assertNotEqual(proc.returncode, 0)
            self.assertIn("cache_root must not contain '..'", proc.stderr)

    def test_unsafe_graph_scope_fails(self) -> None:
        with copy_repo() as temp:
            root = Path(temp) / "skill"
            registry = load_registry(root)
            registry["sources"]["promptfoo-promptfoo"]["materialization"]["graph"]["scope"]["include"] = [
                "../site/docs"
            ]
            write_registry(root, registry)
            proc = self.run_validator(root)
            self.assertNotEqual(proc.returncode, 0)
            self.assertIn("graph.scope.include[0] must not contain '..'", proc.stderr)

    def test_unsafe_graph_scope_exclude_fails(self) -> None:
        with copy_repo() as temp:
            root = Path(temp) / "skill"
            registry = load_registry(root)
            registry["sources"]["promptfoo-promptfoo"]["materialization"]["graph"]["scope"]["exclude"].append(
                "../secrets"
            )
            write_registry(root, registry)
            proc = self.run_validator(root)
            self.assertNotEqual(proc.returncode, 0)
            self.assertIn("graph.scope.exclude", proc.stderr)

    def test_generated_dirs_are_skipped_by_validator(self) -> None:
        with copy_repo() as temp:
            root = Path(temp) / "skill"
            for rel in ("temp_artifact", "graphify-out", "cache", ".codex", ".omx"):
                generated_dir = root / rel
                generated_dir.mkdir(parents=True)
                (generated_dir / "._generated").write_text("sidecar", encoding="utf-8")
                (root / f"._{Path(rel).name}").write_text("directory sidecar", encoding="utf-8")
            proc = self.run_validator(root)
            self.assertEqual(proc.returncode, 0, proc.stderr)

    def test_sidecar_outside_generated_dirs_fails(self) -> None:
        with copy_repo() as temp:
            root = Path(temp) / "skill"
            (root / "._bad").write_text("sidecar", encoding="utf-8")
            proc = self.run_validator(root)
            self.assertNotEqual(proc.returncode, 0)
            self.assertIn("macOS sidecar", proc.stderr)

    def test_skill_category_drift_fails(self) -> None:
        with copy_repo() as temp:
            root = Path(temp) / "skill"
            skill = root / "SKILL.md"
            skill.write_text(
                skill.read_text(encoding="utf-8").replace("`eval_benchmark`", "`evalbench`"),
                encoding="utf-8",
            )
            proc = self.run_validator(root)
            self.assertNotEqual(proc.returncode, 0)
            self.assertIn("category bullets must match registry routes", proc.stderr)

    def test_materializer_rejects_non_https_repo_url(self) -> None:
        with copy_repo() as temp:
            root = Path(temp) / "skill"
            registry = load_registry(root)
            registry["sources"]["promptfoo-promptfoo"]["repo_url"] = "ssh://github.com/promptfoo/promptfoo.git"
            registry["sources"]["promptfoo-promptfoo"]["materialization"][
                "repo_url"
            ] = "ssh://github.com/promptfoo/promptfoo.git"
            write_registry(root, registry)
            proc = self.run_materializer(root, "promptfoo-promptfoo")
            self.assertNotEqual(proc.returncode, 0)
            self.assertIn("scheme must be https", proc.stderr)
            self.assertNotIn("Traceback", proc.stderr)

    def test_materializer_rejects_bad_source_id(self) -> None:
        with copy_repo() as temp:
            root = Path(temp) / "skill"
            proc = self.run_materializer(root, "../promptfoo-promptfoo")
            self.assertEqual(proc.returncode, 1)
            self.assertTrue(proc.stderr.startswith("ERROR:"), proc.stderr)
            self.assertIn("source id must be lowercase kebab-case", proc.stderr)
            self.assertNotIn("Traceback", proc.stderr)

    def test_materializer_manifest_exists_is_registry_root_relative(self) -> None:
        with copy_repo() as temp:
            root = Path(temp) / "skill"
            manifest = root / "temp_artifact/repo_pointer_router_cache/repos/promptfoo-promptfoo/materialization.json"
            manifest.parent.mkdir(parents=True)
            manifest.write_text("{}", encoding="utf-8")
            proc = self.run_materializer_from_cwd(root, "promptfoo-promptfoo", Path(temp))
            self.assertEqual(proc.returncode, 0, proc.stderr)
            plan = json.loads(proc.stdout)
            self.assertTrue(plan["paths"]["manifest_exists"])

    def test_validator_rejects_display_repo_mismatch(self) -> None:
        with copy_repo() as temp:
            root = Path(temp) / "skill"
            registry = load_registry(root)
            registry["sources"]["promptfoo-promptfoo"]["repo"] = "https://github.com/openai/skills"
            write_registry(root, registry)
            proc = self.run_validator(root)
            self.assertNotEqual(proc.returncode, 0)
            self.assertIn("source.repo and source.repo_url must point to the same GitHub repo", proc.stderr)

    def test_validator_rejects_stale_last_verified_paths(self) -> None:
        with copy_repo() as temp:
            root = Path(temp) / "skill"
            registry = load_registry(root)
            registry["sources"]["promptfoo-promptfoo"]["last_verified"]["checked_paths"] = ["README.md"]
            write_registry(root, registry)
            proc = self.run_validator(root)
            self.assertNotEqual(proc.returncode, 0)
            self.assertIn("last_verified.checked_paths must match", proc.stderr)

    def test_validator_requires_schema_files(self) -> None:
        with copy_repo() as temp:
            root = Path(temp) / "skill"
            (root / "schemas/route-registry.schema.json").unlink()
            proc = self.run_validator(root)
            self.assertNotEqual(proc.returncode, 0)
            self.assertIn("required file missing: schemas/route-registry.schema.json", proc.stderr)

    def test_validator_requires_local_refresh_script(self) -> None:
        with copy_repo() as temp:
            root = Path(temp) / "skill"
            (root / "scripts/local_refresh_repos.py").unlink()
            proc = self.run_validator(root)
            self.assertNotEqual(proc.returncode, 0)
            self.assertIn("required file missing: scripts/local_refresh_repos.py", proc.stderr)

    def test_registry_schema_violation_fails(self) -> None:
        with copy_repo() as temp:
            root = Path(temp) / "skill"
            registry = load_registry(root)
            registry["sources"]["promptfoo-promptfoo"]["unexpected_field"] = True
            write_registry(root, registry)
            proc = self.run_validator(root)
            self.assertNotEqual(proc.returncode, 0)
            self.assertIn("schema violation", proc.stderr)

    def test_route_index_wrong_source_prefix_fails(self) -> None:
        with copy_repo() as temp:
            root = Path(temp) / "skill"
            registry = load_registry(root)
            route_index = registry["sources"]["promptfoo-promptfoo"]["route_index"]
            route_index["openai-skills/eval_basics"] = route_index.pop("promptfoo-promptfoo/eval_basics")
            write_registry(root, registry)
            proc = self.run_validator(root)
            self.assertNotEqual(proc.returncode, 0)
            self.assertIn("route_index key must start", proc.stderr)

    def test_source_listed_by_multiple_routes_fails(self) -> None:
        with copy_repo() as temp:
            root = Path(temp) / "skill"
            registry = load_registry(root)
            registry["routes"]["skill_building"]["sources"].append("promptfoo-promptfoo")
            write_registry(root, registry)
            proc = self.run_validator(root)
            self.assertNotEqual(proc.returncode, 0)
            self.assertIn("source must be listed by exactly one route", proc.stderr)

    def test_materializer_rejects_write_cache_even_with_dry_run(self) -> None:
        with copy_repo() as temp:
            root = Path(temp) / "skill"
            proc = self.run_materializer_args(
                root,
                "--source",
                "promptfoo-promptfoo",
                "--dry-run",
                "--write-cache",
                "--offline-ok",
            )
            self.assertEqual(proc.returncode, 2)
            self.assertEqual(proc.stdout, "")
            self.assertIn("not implemented", proc.stderr)

    def test_materializer_rejects_non_locator_graph_mode(self) -> None:
        with copy_repo() as temp:
            root = Path(temp) / "skill"
            registry = load_registry(root)
            registry["sources"]["promptfoo-promptfoo"]["materialization"]["graph"]["mode"] = "summary_graph"
            write_registry(root, registry)
            proc = self.run_materializer(root, "promptfoo-promptfoo")
            self.assertNotEqual(proc.returncode, 0)
            self.assertIn("graph.mode must be locator_only", proc.stderr)

    def test_materializer_rejects_unsupported_implementation_status(self) -> None:
        with copy_repo() as temp:
            root = Path(temp) / "skill"
            registry = load_registry(root)
            registry["sources"]["promptfoo-promptfoo"]["materialization"][
                "implementation_status"
            ] = "write_cache_enabled"
            write_registry(root, registry)
            proc = self.run_materializer(root, "promptfoo-promptfoo")
            self.assertNotEqual(proc.returncode, 0)
            self.assertIn("implementation_status must be local_refresh_enabled", proc.stderr)

    def test_materializer_rejects_non_positive_materialization_limits(self) -> None:
        with copy_repo() as temp:
            root = Path(temp) / "skill"
            registry = load_registry(root)
            registry["sources"]["promptfoo-promptfoo"]["materialization"]["max_files"] = 0
            write_registry(root, registry)
            proc = self.run_materializer(root, "promptfoo-promptfoo")
            self.assertNotEqual(proc.returncode, 0)
            self.assertIn("max_files must be positive integer", proc.stderr)

    def test_local_refresh_rejects_non_locator_graph_mode_before_network(self) -> None:
        with copy_repo() as temp:
            root = Path(temp) / "skill"
            registry = load_registry(root)
            registry["sources"]["promptfoo-promptfoo"]["materialization"]["graph"]["mode"] = "summary_graph"
            module = self.import_local_refresh()
            with self.assertRaisesRegex(module.RefreshError, "graph.mode must be locator_only"):
                module.refresh_source(root, registry, "promptfoo-promptfoo")

    def test_local_refresh_rejects_non_positive_limits_before_network(self) -> None:
        with copy_repo() as temp:
            root = Path(temp) / "skill"
            registry = load_registry(root)
            registry["sources"]["promptfoo-promptfoo"]["materialization"]["max_bytes"] = 0
            module = self.import_local_refresh()
            with self.assertRaisesRegex(module.RefreshError, "max_bytes must be a positive integer"):
                module.refresh_source(root, registry, "promptfoo-promptfoo")

    def test_dry_run_plans_match_materialization_plan_schema(self) -> None:
        with copy_repo() as temp:
            root = Path(temp) / "skill"
            proc = self.run_materializer(root, "promptfoo-promptfoo")
            self.assertEqual(proc.returncode, 0, proc.stderr)
            plan = json.loads(proc.stdout)
            self.assertEqual(
                plan["paths"]["graph"],
                "temp_artifact/repo_pointer_router_cache/repos/promptfoo-promptfoo/worktree/graphify-out/graph.json",
            )
            schema = json.loads((root / "schemas/materialization-plan.schema.json").read_text(encoding="utf-8"))
            validator = Draft202012Validator(schema, format_checker=FormatChecker())
            self.assertEqual(list(validator.iter_errors(plan)), [])

    def test_materialization_plan_schema_rejects_clone_true(self) -> None:
        with copy_repo() as temp:
            root = Path(temp) / "skill"
            proc = self.run_materializer(root, "promptfoo-promptfoo")
            self.assertEqual(proc.returncode, 0, proc.stderr)
            plan = json.loads(proc.stdout)
            plan["safety"]["clone"] = True
            schema = json.loads((root / "schemas/materialization-plan.schema.json").read_text(encoding="utf-8"))
            validator = Draft202012Validator(schema, format_checker=FormatChecker())
            errors = list(validator.iter_errors(plan))
            self.assertTrue(errors)
            self.assertIn("False was expected", errors[0].message)

    def test_local_manifest_schema_accepts_local_refresh_manifest_shape(self) -> None:
        with copy_repo() as temp:
            root = Path(temp) / "skill"
            manifest = {
                "source_id": "promptfoo-promptfoo",
                "repo_url": "https://github.com/promptfoo/promptfoo.git",
                "requested_ref": "main",
                "resolved_commit": "a" * 40,
                "materialized_at": "2026-05-07T00:00:00+00:00",
                "worktree_path": "temp_artifact/repo_pointer_router_cache/repos/promptfoo-promptfoo/worktree",
                "safety": {
                    "run_package_install": False,
                    "run_repo_scripts": False,
                    "run_hooks": False,
                    "follow_external_symlinks": False,
                    "submodules_recursive": False,
                },
                "locator_only": True,
            }
            schema = json.loads((root / "schemas/materialization-manifest.schema.json").read_text(encoding="utf-8"))
            validator = Draft202012Validator(schema, format_checker=FormatChecker())
            self.assertEqual(list(validator.iter_errors(manifest)), [])

    def test_route_index_artifact_schema_accepts_local_refresh_artifact_shape(self) -> None:
        with copy_repo() as temp:
            root = Path(temp) / "skill"
            registry = load_registry(root)
            source = registry["sources"]["promptfoo-promptfoo"]
            module = self.import_local_refresh()
            artifact = module.build_route_index_artifact("promptfoo-promptfoo", source, "a" * 40)
            schema = json.loads((root / "schemas/route-index-artifact.schema.json").read_text(encoding="utf-8"))
            validator = Draft202012Validator(schema, format_checker=FormatChecker())
            self.assertEqual(list(validator.iter_errors(artifact)), [])

    def test_anchor_report_schema_accepts_mocked_checker_output(self) -> None:
        with copy_repo() as temp:
            root = Path(temp) / "skill"
            report = [
                {
                    "source_id": "promptfoo-promptfoo",
                    "locator": "read_first",
                    "path": "README.md",
                    "exists": True,
                    "checked_ref": "main",
                    "checked_at": "2026-05-07T00:00:00+00:00",
                    "resolved_commit": "a" * 40,
                    "blob_sha": "b" * 40,
                    "url": "https://raw.githubusercontent.com/promptfoo/promptfoo/main/README.md",
                    "error": None,
                    "metadata_error": None,
                }
            ]
            schema = json.loads((root / "schemas/anchor-check-report.schema.json").read_text(encoding="utf-8"))
            validator = Draft202012Validator(schema, format_checker=FormatChecker())
            self.assertEqual(list(validator.iter_errors(report)), [])

    def test_upstream_checker_rejects_unsafe_anchor_without_network(self) -> None:
        import importlib.util

        spec = importlib.util.spec_from_file_location("check_upstream_anchors", UPSTREAM_CHECKER)
        self.assertIsNotNone(spec)
        module = importlib.util.module_from_spec(spec)
        assert spec and spec.loader
        spec.loader.exec_module(module)
        registry = {
            "sources": {
                "bad-source": {
                    "repo_url": "https://github.com/owner/repo.git",
                    "read_first": ["../README.md"],
                }
            }
        }
        with mock.patch.object(module, "resolve_commit", side_effect=AssertionError("network touched")):
            with self.assertRaises(ValueError):
                module.check_registry(registry, "main", 0.01)

    def test_symlink_outside_generated_dirs_fails(self) -> None:
        with copy_repo() as temp:
            root = Path(temp) / "skill"
            target = root / "README.md"
            link = root / "bad-link"
            try:
                link.symlink_to(target)
            except (NotImplementedError, OSError) as exc:
                self.skipTest(f"symlink unavailable: {exc}")
            proc = self.run_validator(root)
            self.assertNotEqual(proc.returncode, 0)
            self.assertIn("draft skill must not contain symlink", proc.stderr)

    def test_orphan_category_router_fails(self) -> None:
        with copy_repo() as temp:
            root = Path(temp) / "skill"
            (root / "references/category-routers/orphan.md").write_text("# Orphan\n", encoding="utf-8")
            proc = self.run_validator(root)
            self.assertNotEqual(proc.returncode, 0)
            self.assertIn("category router files must match registry routes exactly", proc.stderr)

    def test_orphan_source_card_fails(self) -> None:
        with copy_repo() as temp:
            root = Path(temp) / "skill"
            (root / "references/source-cards/orphan-source.md").write_text("# Orphan\n", encoding="utf-8")
            proc = self.run_validator(root)
            self.assertNotEqual(proc.returncode, 0)
            self.assertIn("source-cards files must match sources exactly", proc.stderr)

    def test_missing_source_card_fails(self) -> None:
        with copy_repo() as temp:
            root = Path(temp) / "skill"
            (root / "references/source-cards/promptfoo-promptfoo.md").unlink()
            proc = self.run_validator(root)
            self.assertNotEqual(proc.returncode, 0)
            self.assertIn("source card missing", proc.stderr)

    def test_upstream_checker_url_encoding_helper(self) -> None:
        import importlib.util

        spec = importlib.util.spec_from_file_location("check_upstream_anchors", UPSTREAM_CHECKER)
        self.assertIsNotNone(spec)
        module = importlib.util.module_from_spec(spec)
        assert spec and spec.loader
        spec.loader.exec_module(module)
        self.assertEqual(
            module.raw_url("owner", "repo", "feature/ref", "docs/a file.md"),
            "https://raw.githubusercontent.com/owner/repo/feature%2Fref/docs/a%20file.md",
        )

    def test_upstream_checker_404_reports_missing(self) -> None:
        import importlib.util

        spec = importlib.util.spec_from_file_location("check_upstream_anchors", UPSTREAM_CHECKER)
        self.assertIsNotNone(spec)
        module = importlib.util.module_from_spec(spec)
        assert spec and spec.loader
        spec.loader.exec_module(module)

        def raise_404(*_args, **_kwargs):
            raise module.HTTPError("url", 404, "Not Found", {}, None)

        with mock.patch.object(module, "urlopen", side_effect=raise_404):
            exists, error = module.anchor_exists("https://example.test/missing", 0.01)
        self.assertFalse(exists)
        self.assertIn("404", error or "")

    def test_upstream_checker_405_falls_back_to_get(self) -> None:
        import importlib.util

        spec = importlib.util.spec_from_file_location("check_upstream_anchors", UPSTREAM_CHECKER)
        self.assertIsNotNone(spec)
        module = importlib.util.module_from_spec(spec)
        assert spec and spec.loader
        spec.loader.exec_module(module)

        class Response:
            status = 200

            def __enter__(self):
                return self

            def __exit__(self, *_args):
                return None

        calls = []

        def fake_urlopen(request, timeout=0):
            calls.append(request)
            if len(calls) == 1:
                raise module.HTTPError("url", 405, "Method Not Allowed", {}, None)
            return Response()

        with mock.patch.object(module, "urlopen", side_effect=fake_urlopen):
            exists, error = module.anchor_exists("https://example.test/file", 0.01)
        self.assertTrue(exists)
        self.assertIsNone(error)
        self.assertEqual(len(calls), 2)

    def test_upstream_checker_metadata_error_does_not_fail_existing_anchor(self) -> None:
        import importlib.util

        spec = importlib.util.spec_from_file_location("check_upstream_anchors", UPSTREAM_CHECKER)
        self.assertIsNotNone(spec)
        module = importlib.util.module_from_spec(spec)
        assert spec and spec.loader
        spec.loader.exec_module(module)

        registry = {
            "sources": {
                "promptfoo-promptfoo": {
                    "repo_url": "https://github.com/promptfoo/promptfoo.git",
                    "read_first": ["README.md"],
                }
            }
        }
        with mock.patch.object(module, "resolve_commit", return_value=(None, "rate limited")), mock.patch.object(
            module, "anchor_exists", return_value=(True, None)
        ), mock.patch.object(module, "resolve_blob_sha", return_value=("b" * 40, None)):
            results, missing = module.check_registry(registry, "main", 0.01)
        self.assertEqual(missing, 0)
        self.assertTrue(results[0]["exists"])
        self.assertEqual(results[0]["metadata_error"], "rate limited")


if __name__ == "__main__":
    unittest.main()
