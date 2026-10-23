import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from base import CRITICAL_PATHS

FRAMEWORK = Path(__file__).resolve().parents[2]


@unittest.skipUnless(shutil.which("git"), "requires git")
class GitRepo(unittest.TestCase):
    branch = "feature/PROJ-1-sample"

    def setUp(self):
        self.repo = Path(tempfile.mkdtemp(prefix="sdd-git-"))
        self.addCleanup(shutil.rmtree, self.repo, ignore_errors=True)
        self.git("init", "-q", "-b", "main")
        self.write("sdd/security/critical-paths.md", CRITICAL_PATHS)
        self.write("src/app.py", "def run():\n    pass\n")
        self.write("README.md", "# Sample\n")
        self.git("add", ".")
        self.git("commit", "-q", "-m", "chore: initial commit")
        if self.branch != "main":
            self.git("checkout", "-q", "-b", self.branch)

    def git(self, *args):
        return subprocess.run(["git", "-c", "user.name=Tester", "-c", "user.email=tester@example.com", *args],
                              cwd=self.repo, check=True, capture_output=True, text=True).stdout

    def package(self, name="PROJ-1-sample"):
        return self.write(f"specs/{name}/spec.md", f"# {name}\n").parent

    def write(self, path, text):
        file = self.repo / path
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_text(text, encoding="utf-8")
        return file
