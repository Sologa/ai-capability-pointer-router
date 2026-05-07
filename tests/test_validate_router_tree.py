from __future__ import annotations

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

    def test_materializer_rejects_bad_source_id(self) -> None:
        with copy_repo() as temp:
            root = Path(temp) / "skill"
            proc = self.run_materializer(root, "../promptfoo-promptfoo")
            self.assertNotEqual(proc.returncode, 0)
            self.assertIn("source id must be lowercase kebab-case", proc.stderr)


if __name__ == "__main__":
    unittest.main()
