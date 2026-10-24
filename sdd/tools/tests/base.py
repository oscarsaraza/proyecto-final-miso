import shutil
import sys
import tempfile
import unittest
from pathlib import Path

TOOLS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOLS))

from sddlib.config import load  # noqa: E402
from sddlib.spec import Validator  # noqa: E402

FIXTURES = Path(__file__).resolve().parent / "fixtures"
TEMPLATES = TOOLS.parent / "templates" / "spec"

REPO_TESTS = (
    "def test_owner_lists_policies(): pass\n"
    "def test_other_user_gets_404(): pass\n"
    "def test_error_hides_personal_data(): pass\n"
    "def test_expired_token_gets_401(): pass\n"
)

CRITICAL_PATHS = """# Critical paths

## Critical paths

| Pattern | Area | Why | Minimum profile |
|---|---|---|---|
| **/identity/** | Identity | Credentials | HIGH |
| terraform/** | Infrastructure | Network and IAM | HIGH |
"""


def make_repo() -> Path:
    repo = Path(tempfile.mkdtemp(prefix="sdd-"))
    (repo / ".git").mkdir()
    (repo / "tests").mkdir()
    (repo / "tests" / "test_policies.py").write_text(REPO_TESTS, encoding="utf-8")
    (repo / "sdd" / "security").mkdir(parents=True)
    (repo / "sdd" / "security" / "critical-paths.md").write_text(CRITICAL_PATHS, encoding="utf-8")
    return repo


class Scenario(unittest.TestCase):
    fixture = "valid_high"

    def setUp(self):
        self.repo = make_repo()
        self.addCleanup(shutil.rmtree, self.repo, ignore_errors=True)
        self.package = self.repo / "specs" / "HU-FIX"
        shutil.copytree(FIXTURES / self.fixture, self.package)

    def edit(self, file, old, new, count=1):
        path = self.package / file
        text = path.read_text(encoding="utf-8")
        self.assertIn(old, text, f"the scenario did not find the text to replace in {file}")
        path.write_text(text.replace(old, new, count), encoding="utf-8")

    def cut(self, file, start, end):
        path = self.package / file
        text = path.read_text(encoding="utf-8")
        path.write_text(text[:text.index(start)] + text[text.index(end):], encoding="utf-8")

    def declare(self, state):
        self.edit("gate.md", "| Security status | SECURITY_VERIFIED |", f"| Security status | {state} |")

    def validate(self):
        return Validator(self.package, load(self.repo)).validate()

    def codes(self, result):
        return {f.code for f in result.errors}

    def assertError(self, result, code, fragment=None):
        matches = [f for f in result.errors if f.code == code and (fragment is None or fragment in f.message)]
        detail = "\n".join(str(f) for f in result.findings)
        self.assertTrue(matches, f"expected {code} ({fragment}); findings:\n{detail}")

    def assertNoErrors(self, result):
        detail = "\n".join(str(f) for f in result.errors)
        self.assertEqual([], result.errors, f"unexpected errors:\n{detail}")
