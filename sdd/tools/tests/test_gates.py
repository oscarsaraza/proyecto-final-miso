import json
import subprocess
import sys
import unittest

from base import FIXTURES  # noqa: F401  (adds the tools folder to sys.path)
from gitrepo import FRAMEWORK, GitRepo

from sddlib import gates, state
from sddlib.config import load

PATCH = "*** Begin Patch\n*** Update File: src/app.py\n@@\n-pass\n+return 1\n*** End Patch\n"


class EventNormalization(unittest.TestCase):
    def event(self, raw, name="pre-tool"):
        return gates.normalize_event(raw, name)

    def test_edit_shell_and_read_calls(self):
        self.assertEqual("edit", self.event({"tool_name": "Edit", "tool_input": {"file_path": "/r/src/a.py"}}).kind)
        self.assertEqual("shell", self.event({"tool_name": "Bash", "tool_input": {"command": "ls"}}).kind)
        self.assertEqual("read", self.event({"tool_name": "Read", "tool_input": {"file_path": ".env"}}).kind)

    def test_flat_payloads(self):
        self.assertEqual("shell", self.event({"command": "git status", "cwd": "/r"}).kind)
        event = self.event({"file_path": ".env"}, "read")
        self.assertEqual(("read", [".env"]), (event.kind, event.paths))

    def test_patch_payload_is_an_edit_of_its_files(self):
        event = self.event({"tool_name": "apply_patch", "tool_input": {"command": PATCH}})
        self.assertEqual(("edit", ["src/app.py"]), (event.kind, event.paths))

    def test_alternative_field_names(self):
        self.assertEqual("edit", self.event({"tool_name": "write_file", "tool_input": {"file_path": "src/a.py"}}).kind)
        self.assertEqual(["src/a.py"], self.event({"tool_name": "edit", "tool_input": {"filePath": "src/a.py"}}).paths)

    def test_repeated_stop_is_detected(self):
        self.assertTrue(self.event({"stop_hook_active": True}, "stop").stop_active)
        self.assertTrue(self.event({"loop_count": 1}, "stop").stop_active)


class SecretsGate(GitRepo):
    def decide(self, raw, name="pre-tool"):
        return gates.evaluate(gates.normalize_event({**raw, "cwd": str(self.repo)}, name), load(self.repo))

    def test_reading_secret_files_is_denied(self):
        for path in (".env", "config/.env.production", "deploy/id_rsa", "infra/prod.tfvars", "certs/server.pem"):
            with self.subTest(path=path):
                self.assertFalse(self.decide({"tool_name": "Read", "tool_input": {"file_path": path}}).allow)

    def test_examples_are_allowed(self):
        self.assertTrue(self.decide({"tool_name": "Read", "tool_input": {"file_path": ".env.example"}}).allow)
        self.assertTrue(self.decide({"tool_name": "Read", "tool_input": {"file_path": "README.md"}}).allow)

    def test_writing_secret_files_is_denied(self):
        self.assertFalse(self.decide({"tool_name": "Write", "tool_input": {"file_path": ".env"}}).allow)

    def test_commands_that_print_secrets_are_denied(self):
        for command in ("cat .env", "printenv", "env", "echo $AWS_SECRET_ACCESS_KEY", "gh auth token",
                        "head -n 5 config/.env.local", "Get-Content .env"):
            with self.subTest(command=command):
                self.assertFalse(self.decide({"tool_name": "Bash", "tool_input": {"command": command}}).allow)

    def test_ordinary_commands_are_allowed(self):
        for command in ("cat README.md", "env FOO=1 python -V", "echo $HOME", "ls -la"):
            with self.subTest(command=command):
                self.assertTrue(self.decide({"tool_name": "Bash", "tool_input": {"command": command}}).allow)


class SpecGate(GitRepo):
    def edit(self, path):
        raw = {"tool_name": "Edit", "tool_input": {"file_path": path}, "cwd": str(self.repo)}
        return gates.evaluate(gates.normalize_event(raw, "pre-tool"), load(self.repo))

    def test_product_edit_without_spec_is_denied(self):
        decision = self.edit("src/app.py")
        self.assertFalse(decision.allow)
        self.assertIn("SPEC-FIRST", decision.reason)
        self.assertFalse(self.edit(str(self.repo / "src" / "app.py")).allow)

    def test_docs_and_framework_are_exempt(self):
        for path in ("README.md", "docs/guide.md", "sdd/skills/x/SKILL.md", "specs/P-1-x/spec.md"):
            with self.subTest(path=path):
                self.assertTrue(self.edit(path).allow)

    def test_the_story_package_unlocks_product_edits(self):
        self.assertIn("PROJ-1", self.edit("src/app.py").reason)
        self.package()
        self.assertTrue(self.edit("src/app.py").allow)
        self.assertEqual("PROJ-1", state.active_spec(load(self.repo), self.branch)["id"])

    def test_another_story_package_does_not_count(self):
        self.package("PROJ-10-other")
        self.package("PROJ-1.1-subtask")
        self.assertFalse(self.edit("src/app.py").allow)

    def test_branches_without_story_need_no_package(self):
        for branch in ("hotfix/login-crash", "feature/ci-coverage"):
            with self.subTest(branch=branch):
                self.git("checkout", "-q", "-b", branch)
                self.assertTrue(self.edit("src/app.py").allow)

    def test_marker_on_a_hotfix_branch(self):
        self.git("checkout", "-q", "-b", "hotfix/login-crash")
        data = state.start(load(self.repo), self.package("HOTFIX-login-crash"), "hotfix/login-crash")
        self.assertEqual(data, state.active_spec(load(self.repo), "hotfix/login-crash"))

    def test_story_key_comes_from_the_branch(self):
        config = load(self.repo)
        for branch, story in (("feature/PROJ-2-quotes", "PROJ-2"), ("fix/PROJ-2.1-null-check", "PROJ-2.1"),
                              ("feature/HU-WEB-13-advisors", "HU-WEB-13"), ("hotfix/login-crash", None),
                              ("feature/ci-coverage", None), ("feat/PROJ-2-quotes", None)):
            with self.subTest(branch=branch):
                self.assertEqual(story, state.story_of(config, branch))

    def test_patches_are_gated(self):
        raw = {"tool_name": "apply_patch", "tool_input": {"command": PATCH}, "cwd": str(self.repo)}
        self.assertFalse(gates.evaluate(gates.normalize_event(raw, "pre-tool"), load(self.repo)).allow)


class ShellGate(GitRepo):
    def run_command(self, command):
        raw = {"tool_name": "Bash", "tool_input": {"command": command}, "cwd": str(self.repo)}
        return gates.evaluate(gates.normalize_event(raw, "pre-tool"), load(self.repo))

    def test_commit_message_must_be_conventional(self):
        self.assertFalse(self.run_command('git commit -m "update stuff"').allow)
        self.assertTrue(self.run_command('git commit -m "docs(readme): PROJ-1 clarify setup"').allow)

    def test_commit_on_a_story_branch_names_the_story(self):
        decision = self.run_command('git commit -m "docs(readme): clarify setup"')
        self.assertFalse(decision.allow)
        self.assertIn("STORY", decision.reason)
        self.assertFalse(self.run_command('git commit -m "docs(readme): PROJ-10 clarify setup"').allow)
        self.assertTrue(self.run_command('git commit -m "docs(readme): clarify setup (PROJ-1)"').allow)

    def test_no_verify_is_denied(self):
        self.assertFalse(self.run_command('git commit --no-verify -m "feat: PROJ-1 x"').allow)

    def test_force_push_and_protected_targets_are_denied(self):
        for command in ("git push --force", "git push -f origin feature/PROJ-1-sample", "git push origin main",
                        "git push origin HEAD:refs/heads/dev", "git push origin +feature/PROJ-1-sample"):
            with self.subTest(command=command):
                self.assertFalse(self.run_command(command).allow)
        self.assertTrue(self.run_command("git push -u origin feature/PROJ-1-sample").allow)


    def test_compound_commands_are_inspected(self):
        self.assertFalse(self.run_command('git add . && git commit -m "wip"').allow)


class ProtectedBranch(GitRepo):
    branch = "main"

    def test_commit_on_main_is_denied(self):
        raw = {"tool_name": "Bash", "tool_input": {"command": 'git commit -m "fix: PROJ-1 x"'}, "cwd": str(self.repo)}
        decision = gates.evaluate(gates.normalize_event(raw, "pre-tool"), load(self.repo))
        self.assertFalse(decision.allow)
        self.assertIn("PROTECTED-BRANCH", decision.reason)
        self.assertFalse(gates.git_pre_commit(load(self.repo)).allow)


class CommitContent(GitRepo):
    def test_staged_secret_is_denied_without_printing_it(self):
        value = "ghp_" + "Ab1C" * 9
        self.write("src/settings.py", f'TOKEN = "{value}"\n')
        self.git("add", "src/settings.py")
        decision = gates.git_pre_commit(load(self.repo))
        self.assertFalse(decision.allow)
        self.assertNotIn(value, decision.reason)
        self.assertNotIn(value[4:12], decision.reason)

    def test_product_commit_needs_the_story_package(self):
        self.write("src/app.py", "def run():\n    return 1\n")
        self.git("add", "src/app.py")
        decision = gates.git_commit_msg(load(self.repo), "fix(app): PROJ-1 return a value\n\nSPEC-EXEMPT: small")
        self.assertFalse(decision.allow)
        self.assertIn("spec new PROJ-1", decision.reason)
        self.package()
        self.assertTrue(gates.git_commit_msg(load(self.repo), "fix(app): PROJ-1 return a value").allow)
        self.assertFalse(gates.git_commit_msg(load(self.repo), "fix(app): return a value").allow)

    def test_docs_commit_needs_no_spec(self):
        self.write("README.md", "# Sample\n\nMore.\n")
        self.git("add", "README.md")
        self.assertTrue(gates.git_commit_msg(load(self.repo), "docs(readme): PROJ-1 explain").allow)

    def test_adr_gate_on_base_image_change(self):
        self.write("Dockerfile", "FROM python:3.13-slim\n")
        self.git("add", "Dockerfile")
        self.package()
        message = "build(docker): PROJ-1 new base image"
        decision = gates.git_commit_msg(load(self.repo), message)
        self.assertFalse(decision.allow)
        self.assertIn("ADR GATE", decision.reason)
        self.assertTrue(gates.git_commit_msg(load(self.repo), message + "\nADR-EXEMPT: reviewed with the team").allow)
        self.write("docs/adr/0001-base-image.md", "# ADR 0001\n")
        self.git("add", "docs/adr/0001-base-image.md")
        self.assertTrue(gates.git_commit_msg(load(self.repo), message).allow)

    def test_commit_msg_ignores_comment_lines(self):
        self.assertTrue(gates.git_commit_msg(load(self.repo), "# Please enter the message\nchore: PROJ-1 tidy\n").allow)


class BranchWithoutStory(GitRepo):
    branch = "hotfix/login-crash"

    def test_hotfix_commits_need_no_story_or_package(self):
        self.write("src/app.py", "def run():\n    return 1\n")
        self.git("add", "src/app.py")
        self.assertTrue(gates.git_commit_msg(load(self.repo), "fix(auth): reject expired tokens").allow)

    def test_secrets_and_conventions_still_apply(self):
        self.assertFalse(gates.git_commit_msg(load(self.repo), "reject expired tokens").allow)
        self.write("src/settings.py", 'TOKEN = "' + "ghp_" + "Zq7W" * 9 + '"\n')
        self.git("add", "src/settings.py")
        self.assertFalse(gates.git_commit_msg(load(self.repo), "fix(auth): rotate token").allow)


class OtherBranch(GitRepo):
    branch = "feature/ci-coverage"

    def test_branches_without_a_story_are_not_gated_by_story(self):
        self.write("src/app.py", "def run():\n    return 1\n")
        self.git("add", "src/app.py")
        self.assertTrue(gates.git_commit_msg(load(self.repo), "ci: measure coverage").allow)


class PrePush(GitRepo):
    def test_push_to_protected_ref_is_denied(self):
        head = self.git("rev-parse", "HEAD").strip()
        self.assertFalse(gates.git_pre_push(load(self.repo), f"refs/heads/x {head} refs/heads/main {'0' * 40}\n").allow)
        self.assertTrue(gates.git_pre_push(load(self.repo), f"refs/heads/x {head} refs/heads/{self.branch} {'0' * 40}\n").allow)

    def test_rewriting_history_is_denied(self):
        self.write("src/b.py", "x = 1\n")
        self.git("add", ".")
        self.git("commit", "-q", "-m", "feat: PROJ-1 b")
        remote = self.git("rev-parse", "HEAD").strip()
        self.git("reset", "-q", "--hard", "HEAD~1")
        self.write("src/c.py", "y = 2\n")
        self.git("add", ".")
        self.git("commit", "-q", "-m", "feat: PROJ-1 c")
        local = self.git("rev-parse", "HEAD").strip()
        self.assertFalse(gates.git_pre_push(load(self.repo), f"refs/heads/x {local} refs/heads/{self.branch} {remote}\n").allow)


class StopGate(GitRepo):
    def test_stop_blocks_once_while_the_active_spec_is_invalid(self):
        package = self.repo / "specs" / "PROJ-1-sample"
        package.mkdir(parents=True)
        (package / "spec.md").write_text("# PROJ-1 · Sample\n", encoding="utf-8")
        state.start(load(self.repo), package)
        event = gates.normalize_event({"cwd": str(self.repo)}, "stop")
        self.assertFalse(gates.evaluate(event, load(self.repo)).allow)
        again = gates.normalize_event({"cwd": str(self.repo), "stop_hook_active": True}, "stop")
        self.assertTrue(gates.evaluate(again, load(self.repo)).allow)

    def test_stop_without_active_spec_is_allowed(self):
        self.assertTrue(gates.evaluate(gates.normalize_event({"cwd": str(self.repo)}, "stop"), load(self.repo)).allow)


class GateRunner(GitRepo):
    def run_gate(self, payload, *flags):
        return subprocess.run([sys.executable, str(FRAMEWORK / "hooks" / "run.py"), "pre-tool", *flags],
                              input=json.dumps(payload) if isinstance(payload, dict) else payload,
                              capture_output=True, text=True, cwd=self.repo)

    def test_deny_exits_2_with_the_reason_on_stderr(self):
        result = self.run_gate({"tool_name": "Read", "tool_input": {"file_path": ".env"}, "cwd": str(self.repo)})
        self.assertEqual(2, result.returncode)
        self.assertIn("SECRETS", result.stderr)

    def test_json_answer(self):
        allowed = self.run_gate({"command": "ls", "cwd": str(self.repo)}, "--json")
        self.assertEqual((0, "allow"), (allowed.returncode, json.loads(allowed.stdout)["decision"]))
        denied = self.run_gate({"command": "cat .env", "cwd": str(self.repo)}, "--json")
        self.assertEqual((2, "deny"), (denied.returncode, json.loads(denied.stdout)["decision"]))

    def test_unreadable_input_fails_open(self):
        result = self.run_gate("not json")
        self.assertEqual(0, result.returncode)
        self.assertIn("allowing", result.stderr)


if __name__ == "__main__":
    unittest.main()
