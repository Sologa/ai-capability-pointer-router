from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import yaml


REPO_ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = REPO_ROOT / "validation" / "validate_router_tree.py"
MATERIALIZER = REPO_ROOT / "scripts" / "materialize_repo_pointer.py"
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

    def test_current_tree_is_valid(self) -> None:
        with copy_repo() as temp:
            root = Path(temp) / "skill"
            proc = self.run_validator(root)
            self.assertEqual(proc.returncode, 0, proc.stderr)

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

    def test_generated_dirs_are_skipped_by_validator(self) -> None:
        with copy_repo() as temp:
            root = Path(temp) / "skill"
            for rel in ("temp_artifact", "graphify-out", "cache", ".codex", ".omx"):
                generated_dir = root / rel
                generated_dir.mkdir(parents=True)
                (generated_dir / "._generated").write_text("sidecar", encoding="utf-8")
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


if __name__ == "__main__":
    unittest.main()
