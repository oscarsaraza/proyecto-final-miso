import argparse
import contextlib
import io
import os
import unittest

from gitrepo import GitRepo

import sdd
from sddlib import secrets

PYPROJECT = '[tool.poetry.dependencies]\npython = ">=3.12"\nfastapi = ">=0.115.0"\n'

SPEC_WITH_PATHS = """# HU-X · Change

## 1. Requirements

### Affected paths

| Path | Change |
|---|---|
| backend/app/modules/identity/** | Adjust |
"""

DEPENDENCY_TABLE = """# Security · HU-X

## 15. Dependencies

| ID | Dependency | Version | Component | Use | Criticality | Evaluation | Result | Status |
|---|---|---|---|---|---|---|---|---|
| DEP-01 | argon2-cffi | 23.1.0 | backend | Passwords | CRITICAL | OSV.dev 2026-10-21 | No known vulnerabilities | {status} |
"""


class Cli(GitRepo):
    branch = "main"

    def setUp(self):
        super().setUp()
        self.branch = "feature/PROJ-1-sample"
        self.write("backend/app/modules/identity/service.py", "def login():\n    pass\n")
        self.write("backend/pyproject.toml", PYPROJECT)
        self.write("backend/app/config.py", 'API_TOKEN = "' + "v13j0" * 3 + '"\n')
        self.git("add", ".")
        self.git("commit", "-q", "-m", "chore: base")
        self.git("checkout", "-q", "-b", self.branch)
        self.previous = os.getcwd()
        os.chdir(self.repo)
        sdd.CONFIG = None
        self.addCleanup(self._restore)

    def _restore(self):
        os.chdir(self.previous)
        sdd.CONFIG = None

    def run_cli(self, function, **kwargs):
        with contextlib.redirect_stdout(io.StringIO()) as out, contextlib.redirect_stderr(io.StringIO()):
            code = function(argparse.Namespace(**kwargs))
        return code, out.getvalue()

    def test_critical_path_without_package_fails(self):
        self.write("backend/app/modules/identity/service.py", "def login():\n    return 1\n")
        code, out = self.run_cli(sdd.scan_paths, base="main")
        self.assertEqual(1, code)
        self.assertIn("MISSING  backend/app/modules/identity/service.py", out)

    def test_critical_path_with_new_package_passes(self):
        self.write("backend/app/modules/identity/service.py", "def login():\n    return 1\n")
        self.write("specs/HU-X-change/spec.md", SPEC_WITH_PATHS)
        code, out = self.run_cli(sdd.scan_paths, base="main")
        self.assertEqual(0, code, out)
        self.assertIn("HU-X-change", out)

    def test_spec_exempt_commit_covers_critical_paths(self):
        self.write("backend/app/modules/identity/service.py", "def login():\n    return 2\n")
        self.git("add", ".")
        self.git("commit", "-q", "-m", "chore(sdd): bootstrap\n\nSPEC-EXEMPT: framework bootstrap reviewed by the team")
        code, out = self.run_cli(sdd.scan_paths, base="main")
        self.assertEqual(0, code, out)
        self.assertIn("EXEMPT", out)

    def test_changes_outside_critical_paths_need_no_package(self):
        self.write("docs/guide.md", "text\n")
        self.assertEqual(0, self.run_cli(sdd.scan_paths, base="main")[0])

    def test_new_dependency_requires_evaluation(self):
        self.write("backend/pyproject.toml", PYPROJECT + 'argon2-cffi = ">=23.1.0"\n')
        code, out = self.run_cli(sdd.scan_deps, base="main", require_evaluation=True)
        self.assertEqual(1, code)
        self.assertIn("argon2-cffi", out)
        self.write("specs/HU-X-change/spec.md", "# HU-X\n")
        self.write("specs/HU-X-change/security.md", DEPENDENCY_TABLE.format(status="PENDING"))
        self.assertEqual(1, self.run_cli(sdd.scan_deps, base="main", require_evaluation=True)[0])
        self.write("specs/HU-X-change/security.md", DEPENDENCY_TABLE.format(status="EVALUATED"))
        code, out = self.run_cli(sdd.scan_deps, base="main", require_evaluation=True)
        self.assertEqual(0, code, out)

    def test_secrets_only_in_new_lines(self):
        self.write("backend/app/other.py", 'PASSWORD = "' + "Nu3v4" * 3 + '"\n')
        self.git("add", "backend/app/other.py")
        self.write("backend/app/untracked.py", "key = " + "AKIA" + "M3N4" * 4 + "\n")
        findings = secrets.scan_diff("main", self.repo)
        self.assertEqual({"backend/app/other.py", "backend/app/untracked.py"}, {f.path for f in findings})

    def test_story_branch_activates_its_package(self):
        self.write("sdd/templates/spec/spec.md", "# {{ID}} · {{TITLE}}\n\n| Field | Value |\n|---|---|\n| ID | {{ID}} |\n")
        self.assertIn("No active spec", self.run_cli(sdd.spec_status)[1])
        code, out = self.run_cli(sdd.spec_new, id="PROJ-1", title="Sample")
        self.assertEqual(0, code, out)
        self.assertIn("feature/PROJ-1-sample", out)
        self.assertIn('"id": "PROJ-1"', self.run_cli(sdd.spec_status)[1])

    def test_marker_on_a_hotfix_branch(self):
        self.git("checkout", "-q", "-b", "hotfix/reset-password")
        self.write("sdd/templates/spec/spec.md", "# {{ID}} · {{TITLE}}\n\n| Field | Value |\n|---|---|\n| ID | {{ID}} |\n")
        code, out = self.run_cli(sdd.spec_new, id="PROJ-7", title="Reset password")
        self.assertEqual(0, code, out)
        self.assertTrue((self.repo / "specs" / "PROJ-7-reset-password" / "spec.md").exists())
        self.assertEqual(0, self.run_cli(sdd.spec_start, reference="PROJ-7", branch="")[0])
        self.assertTrue((self.repo / ".sdd" / "active-spec.json").exists())
        self.assertIn("PROJ-7", self.run_cli(sdd.spec_status)[1])
        self.run_cli(sdd.spec_stop)
        self.assertFalse((self.repo / ".sdd" / "active-spec.json").exists())


if __name__ == "__main__":
    unittest.main()
