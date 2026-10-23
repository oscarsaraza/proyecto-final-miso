"""Gate entry point for git hooks and for any AI agent that supports command hooks.

    run.py <event> [file] [--json]

events: pre-tool (stdin: JSON describing the tool call), stop,
        git-pre-commit, git-commit-msg <file>, git-pre-push (stdin: git's ref updates)

An agent hook blocks with exit code 2 and the reason on stderr; --json also prints
{"decision": "allow"|"deny", "reason": ...} for agents that read a JSON answer. Git hooks block with exit 1.
The gate fails open on unreadable input or an internal error, and says so on stderr.
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))

from sddlib import gates  # noqa: E402
from sddlib.config import load  # noqa: E402


def _emit(decision: gates.Decision, git: bool, as_json: bool) -> int:
    if as_json:
        print(json.dumps({"decision": "allow" if decision.allow else "deny", "reason": decision.reason}))
    if decision.allow:
        return 0
    print(decision.reason, file=sys.stderr)
    return 1 if git else 2


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="sdd-gate")
    parser.add_argument("event")
    parser.add_argument("file", nargs="?")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    git = args.event.startswith("git-")
    try:
        if git:
            config = load(Path.cwd())
            if args.event == "git-pre-commit":
                decision = gates.git_pre_commit(config)
            elif args.event == "git-commit-msg":
                decision = gates.git_commit_msg(config, Path(args.file).read_text(encoding="utf-8"))
            else:
                decision = gates.git_pre_push(config, sys.stdin.read())
            return _emit(decision, True, False)
        raw = sys.stdin.read()
        try:
            data = json.loads(raw) if raw.strip() else {}
        except ValueError:
            print("sdd: unreadable hook input; allowing", file=sys.stderr)
            return _emit(gates.ALLOW, False, args.json)
        event = gates.normalize_event(data if isinstance(data, dict) else {}, args.event)
        return _emit(gates.evaluate(event), False, args.json)
    except Exception as exc:  # fail open: a broken gate must not brick the session or the commit
        print(f"sdd: gate error ({type(exc).__name__}: {exc}); allowing", file=sys.stderr)
        return 0


if __name__ == "__main__":
    sys.exit(main())
