"""Deterministic gates shared by git hooks and by any AI agent that supports command hooks."""
import os
import re
import shlex
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

from . import secrets
from .config import Config, load
from .paths import matches_any
from .spec import Validator
from .state import active_spec, story_of

_READ_TOOLS = re.compile(r"(?i)^(read|view|cat|open|readfile|read_file|view_file|grep|glob|search|ls|list_directory|read_many_files)$")
_EDIT_TOOLS = re.compile(r"(?i)(write|edit|create|patch|replace|insert|notebook|multiedit|str_replace|delete|move|rename)")
_PATCH_FILE = re.compile(r"^\*\*\* (?:Add|Update|Delete) File: (.+)$|^\*\*\* Move to: (.+)$", re.M)
_SECRET_READERS = re.compile(r"(?i)(?:^|[;&|(\s])(cat|less|more|head|tail|type|bat|nl|grep|rg|awk|sed|cp|scp|base64|xxd|od|strings|source|\.|get-content|gc|select-string)\s")
_ENV_DUMP = re.compile(r"(?i)(?:^|[;&|]\s*)(printenv|env|set|export\s+-p|get-childitem\s+env:|dir\s+env:)\s*(?:$|[;&|>])")
_SECRET_VARIABLE = re.compile(r"(?i)(?:echo|print|printf|write-output|write-host)\b[^;&|]*\$\{?(?:env:)?[A-Z0-9_]*(?:SECRET|TOKEN|PASSWORD|PASSWD|API_?KEY|PRIVATE_?KEY|CREDENTIAL)[A-Z0-9_]*")
_CREDENTIAL_COMMANDS = re.compile(r"(?i)\b(gh\s+auth\s+token|glab\s+auth\s+status\s+[^;&|]*(?:-t|--show-token)|aws\s+configure\s+get\s+\S*secret|git\s+credential\s+fill|security\s+find-(?:generic|internet)-password\s+[^;&|]*-w|op\s+read|vault\s+kv\s+get)")


@dataclass
class Event:
    kind: str
    tool: str = ""
    command: str = ""
    paths: list = field(default_factory=list)
    cwd: Path = None
    stop_active: bool = False


@dataclass
class Decision:
    allow: bool
    reason: str = ""


ALLOW = Decision(True)


def deny(reason: str) -> Decision:
    return Decision(False, reason)


# -- input normalization --------------------------------------------------------------------------


def _first(mapping: dict, *keys):
    for key in keys:
        value = mapping.get(key) if isinstance(mapping, dict) else None
        if value:
            return value
    return None


def normalize_event(raw: dict, event: str) -> Event:
    tool = str(_first(raw, "tool_name", "toolName", "tool") or "")
    tool_input = _first(raw, "tool_input", "toolInput", "args", "input") or {}
    if not isinstance(tool_input, dict):
        tool_input = {"input": tool_input}
    command = _first(tool_input, "command", "cmd") or _first(raw, "command") or ""
    if isinstance(command, list):
        command = " ".join(str(c) for c in command)
    paths = []
    for key in ("file_path", "path", "filePath", "absolute_path", "notebook_path", "target_file", "filename"):
        value = tool_input.get(key) or raw.get(key)
        if isinstance(value, str) and value:
            paths.append(value)
    for key in ("paths", "file_paths"):
        value = tool_input.get(key)
        if isinstance(value, list):
            paths += [str(v) for v in value]
    patch = _first(tool_input, "patch", "input") or (command if "*** Begin Patch" in str(command) else "")
    if isinstance(patch, str) and "*** " in patch:
        paths += [a or b for a, b in _PATCH_FILE.findall(patch)]
    cwd = Path(_first(raw, "cwd", "workspace_root", "directory") or os.getcwd())
    stop_active = bool(raw.get("stop_hook_active")) or int(raw.get("loop_count") or 0) > 0

    if event == "stop":
        kind = event
    elif event == "read" or (_READ_TOOLS.match(tool) and not command):
        kind = "read"
    elif command and "*** Begin Patch" not in str(command):
        kind = "shell"
    elif paths or _EDIT_TOOLS.search(tool):
        kind = "edit"
    else:
        kind = "other"
    return Event(kind, tool, str(command), paths, cwd, stop_active)


# -- helpers --------------------------------------------------------------------------------------


def _relative(path: str, root: Path) -> str:
    candidate = Path(path)
    if not candidate.is_absolute():
        posix = candidate.as_posix()
        return posix[2:] if posix.startswith("./") else posix
    try:
        return candidate.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return candidate.as_posix()


def _is_secret_file(path: str, config: Config) -> bool:
    rel = _relative(path, config.root)
    rules = config["secrets"]
    return matches_any(rules["denyRead"], rel) and not matches_any(rules["allowRead"], rel)


def _git(root: Path, *args) -> str:
    try:
        return subprocess.run(["git", *args], cwd=root, capture_output=True, text=True, encoding="utf-8", check=True).stdout
    except (subprocess.CalledProcessError, OSError):
        return ""


def current_branch(root: Path) -> str:
    branch = _git(root, "rev-parse", "--abbrev-ref", "HEAD").strip()
    return "" if branch == "HEAD" else branch


def _missing_spec(config: Config, branch: str, path: str) -> str:
    story = story_of(config, branch)
    if not story or active_spec(config, branch) is not None:
        return ""
    return (f"SPEC-FIRST: {path} belongs to {story}, which has no spec package yet. Create it with the spec-create "
            f"skill (python sdd/tools/sdd.py spec new {story} \"<title>\").")


def _split(command: str) -> list:
    try:
        return shlex.split(command, posix=True)
    except ValueError:
        return command.split()


def _git_subcommands(command: str) -> list:
    """Each `git <sub> ...` invocation in a compound shell command, as token lists."""
    result = []
    for part in re.split(r"&&|\|\||;|\|", command):
        tokens = _split(part.strip())
        while tokens and ("=" in tokens[0] and not tokens[0].startswith("-")):
            tokens = tokens[1:]
        if len(tokens) >= 2 and Path(tokens[0]).name in ("git", "git.exe"):
            index = 1
            while index < len(tokens) and tokens[index].startswith("-"):
                index += 2 if tokens[index] in ("-C", "-c") else 1
            if index < len(tokens):
                result.append(tokens[index:])
    return result


def _commit_message(args: list) -> str:
    for i, token in enumerate(args):
        if token in ("-m", "--message") and i + 1 < len(args):
            return args[i + 1]
        if token.startswith("--message="):
            return token.split("=", 1)[1]
        if token.startswith("-m") and len(token) > 2 and not token.startswith("--"):
            return token[2:]
    return ""


# -- gates ----------------------------------------------------------------------------------------


def secrets_gate(event: Event, config: Config) -> Decision:
    if event.kind in ("read", "edit"):
        for path in event.paths:
            if _is_secret_file(path, config):
                verb = "reading" if event.kind == "read" else "writing"
                return deny(f"SECRETS: {verb} '{_relative(path, config.root)}' is blocked. Secrets never enter the agent context "
                            "or the repository. Use the secrets manager and reference variables by name.")
        return ALLOW
    if event.kind != "shell":
        return ALLOW
    command = event.command
    if _ENV_DUMP.search(command) or _SECRET_VARIABLE.search(command) or _CREDENTIAL_COMMANDS.search(command):
        return deny("SECRETS: this command would print environment secrets or credentials into the session. "
                    "Check for the presence of a variable by name (e.g. `test -n \"$VAR\"`) instead of printing it.")
    if _SECRET_READERS.search(f" {command}"):
        for token in _split(command):
            cleaned = token.strip("'\"<>")
            if cleaned and not cleaned.startswith("-") and _is_secret_file(cleaned, config):
                return deny(f"SECRETS: this command reads '{cleaned}', which is a secret file. "
                            "Never print secret files; ask the user to verify values outside the session.")
    return ALLOW


def spec_gate(event: Event, config: Config) -> Decision:
    if event.kind != "edit":
        return ALLOW
    rules = config["spec"]
    branch = None
    for path in event.paths:
        rel = _relative(path, config.root)
        if Path(rel).is_absolute() or matches_any(rules["exempt"], rel) or not matches_any(rules["required"], rel):
            continue
        branch = current_branch(config.root) if branch is None else branch
        reason = _missing_spec(config, branch, rel)
        if reason:
            return deny(reason + " Docs, markdown and framework files are exempt.")
    return ALLOW


def shell_gate(event: Event, config: Config) -> Decision:
    if event.kind != "shell":
        return ALLOW
    root = config.root
    protected = set(config["protectedBranches"])
    for args in _git_subcommands(event.command):
        sub, rest = args[0], args[1:]
        if sub in ("commit", "push") and any(a == "--no-verify" or (a == "-n" and sub == "commit") for a in rest):
            return deny("HOOKS: --no-verify bypasses the git hooks that enforce the SDD gates. Fix the cause instead.")
        if sub == "commit":
            branch = current_branch(root)
            if branch in protected:
                return deny(f"PROTECTED-BRANCH: do not commit on '{branch}'. Work on the story's branch (feature/<story>-<slug>) "
                            "or a hotfix branch, and open a merge request.")
            message = _commit_message(rest)
            if message:
                for decision in (commit_message_gate(message, config, branch), commit_content_gate(config, message, branch)):
                    if not decision.allow:
                        return decision
        if sub == "push":
            branch = current_branch(root)
            forced = any(a in ("--force", "-f", "--force-with-lease", "--force-if-includes") or a.startswith("--force") or a.startswith("+") for a in rest)
            if forced:
                return deny("PROTECTED-BRANCH: force-push is blocked. Push a new commit instead of rewriting shared history.")
            targets = [a.split(":")[-1].replace("refs/heads/", "") for a in rest if not a.startswith("-")][1:]
            if (branch in protected and not targets) or any(t in protected for t in targets):
                return deny(f"PROTECTED-BRANCH: pushing to {', '.join(sorted(protected))} is blocked. Push the feature branch and open a merge request.")
    return ALLOW


def commit_message_gate(message: str, config: Config, branch: str = "") -> Decision:
    subject = message.strip().splitlines()[0] if message.strip() else ""
    if subject.startswith(("Merge ", "Revert \"", "fixup! ", "squash! ")):
        return ALLOW
    if not re.match(config["commitPattern"], subject):
        return deny(f"STRUCTURE: '{subject}' is not a Conventional Commit. Use `type(scope): <story> summary`, for example "
                    "`fix(auth): PROJ-12 reject expired tokens`.")
    story = story_of(config, branch)
    if story and not re.search(re.escape(story) + r"(?![\w]|\.\d)", subject):
        return deny(f"STORY: every commit on {branch} names its story: `type(scope): {story} <summary>`.")
    return ALLOW


def _staged(root: Path) -> list:
    return [l for l in _git(root, "diff", "--cached", "--name-only").splitlines() if l.strip()]


def commit_content_gate(config: Config, message: str = "", branch: str = None) -> Decision:
    root = config.root
    branch = current_branch(root) if branch is None else branch
    staged = _staged(root)
    if not staged:
        return ALLOW
    findings = secrets.scan_staged(root)
    if findings:
        where = ", ".join(f"{f.path}:{f.line} ({f.kind})" for f in findings[:5])
        return deny(f"SECRETS: the staged changes contain possible secrets: {where}. Remove them, rotate them, and use "
                    f"the secrets manager. Mark a false positive with '{secrets.IGNORE_MARKER}' on that line.")
    rules = config["spec"]
    product = [s for s in staged if matches_any(rules["required"], s) and not matches_any(rules["exempt"], s)]
    if product:
        reason = _missing_spec(config, branch, product[0])
        if reason:
            return deny(reason)
    if "ADR-EXEMPT:" in message:
        return ALLOW
    adr = config["adr"]
    if any(s.startswith(adr["dir"].rstrip("/") + "/") for s in staged):
        return ALLOW
    for trigger in adr["triggers"]:
        files = [s for s in staged if matches_any(trigger["files"], s)]
        if not files:
            continue
        diff = _git(root, "diff", "--cached", "-U0", "--", *files)
        added = "\n".join(l[1:] for l in diff.splitlines() if l.startswith("+") and not l.startswith("+++"))
        if re.search(trigger["added"], added, re.M):
            return deny(f"ADR GATE: {trigger['reason']} needs an ADR under {adr['dir']}/ in this commit "
                        "(run the adr skill). Waiver: 'ADR-EXEMPT: <reason>' in the commit message, accepted by a person.")
    return ALLOW


def stop_gate(event: Event, config: Config) -> Decision:
    if event.stop_active:
        return ALLOW
    spec = active_spec(config, current_branch(config.root))
    if not spec:
        return ALLOW
    package = config.root / spec.get("path", "")
    if not package.is_dir():
        return ALLOW
    result = Validator(package, config).validate()
    if result.errors:
        top = "; ".join(f"{f.code} {f.path}:{f.line} {f.message}" for f in result.errors[:5])
        return deny(f"VALIDATION LOOP: the active spec {spec.get('id')} has {len(result.errors)} validation errors. Fix them "
                    f"or tell the user why you are stopping: {top}")
    return ALLOW


def evaluate(event: Event, config: Config = None) -> Decision:
    config = config or load(event.cwd)
    if event.kind == "stop":
        return stop_gate(event, config)
    for gate in (secrets_gate, spec_gate, shell_gate):
        decision = gate(event, config)
        if not decision.allow:
            return decision
    return ALLOW


# -- git hooks ------------------------------------------------------------------------------------


def git_pre_commit(config: Config) -> Decision:
    branch = current_branch(config.root)
    if branch in set(config["protectedBranches"]):
        return deny(f"PROTECTED-BRANCH: do not commit on '{branch}'. Create a typed branch and open a merge request.")
    findings = secrets.scan_staged(config.root)
    if findings:
        where = ", ".join(f"{f.path}:{f.line} ({f.kind})" for f in findings[:5])
        return deny(f"SECRETS: the staged changes contain possible secrets: {where}.")
    return ALLOW


def git_commit_msg(config: Config, message: str) -> Decision:
    message = "\n".join(l for l in message.splitlines() if not l.startswith("#"))
    branch = current_branch(config.root)
    decision = commit_message_gate(message, config, branch)
    return decision if not decision.allow else commit_content_gate(config, message, branch)


def git_pre_push(config: Config, updates: str) -> Decision:
    protected = set(config["protectedBranches"])
    zero = "0" * 40
    for line in updates.splitlines():
        parts = line.split()
        if len(parts) != 4:
            continue
        _, local_sha, remote_ref, remote_sha = parts
        branch = remote_ref.replace("refs/heads/", "")
        if branch in protected:
            return deny(f"PROTECTED-BRANCH: pushing to '{branch}' is blocked. Open a merge request.")
        if remote_sha != zero and local_sha != zero:
            ancestor = subprocess.run(["git", "merge-base", "--is-ancestor", remote_sha, local_sha], cwd=config.root, capture_output=True)
            if ancestor.returncode == 1:
                return deny(f"PROTECTED-BRANCH: this push rewrites '{branch}' (force-push). Push a new commit instead.")
    return ALLOW
