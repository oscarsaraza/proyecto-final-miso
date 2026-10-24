"""SDD CLI: spec packages, security gate, scanners and git hooks. Standard library only."""
import argparse
import json
import re
import subprocess
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from sddlib import dependencies, paths, secrets, state  # noqa: E402
from sddlib.config import CONFIG_FILE, load  # noqa: E402
from sddlib.markdown import Document, normalize  # noqa: E402
from sddlib.spec import GATE_STATES, Validator  # noqa: E402

CONFIG = None


def config():
    global CONFIG
    if CONFIG is None:
        CONFIG = load(Path.cwd())
    return CONFIG


def _utf8_output():
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass


def _packages(args) -> list:
    specs = config().specs_dir
    if getattr(args, "all", False) or not getattr(args, "packages", None):
        return sorted(p for p in specs.iterdir() if p.is_dir() and (p / "spec.md").exists()) if specs.exists() else []
    return [Path(p) for p in args.packages]


# -- spec ---------------------------------------------------------------------------------------


def spec_new(args) -> int:
    cfg = config()
    identifier = args.id.strip()
    target = cfg.specs_dir / f"{identifier}-{state.slugify(args.title)}"
    if target.exists():
        print(f"{target.relative_to(cfg.root).as_posix()} already exists", file=sys.stderr)
        return 1
    target.mkdir(parents=True)
    for template in sorted((cfg.root / "sdd" / "templates" / "spec").glob("*.md")):
        text = (template.read_text(encoding="utf-8").replace("{{ID}}", identifier).replace("{{TITLE}}", args.title)
                .replace("{{DATE}}", date.today().isoformat()).replace("{{SPEC_PATH}}", target.relative_to(cfg.root).as_posix()))
        (target / template.name).write_text(text, encoding="utf-8")
    slug = state.slugify(args.title)
    branch = f"hotfix/{slug}" if identifier.upper() == "HOTFIX" else f"feature/{identifier}-{slug}"
    print(f"Created {target.relative_to(cfg.root).as_posix()}. Fill every <fill: …>, then run the spec-review skill. "
          f"Work on the branch {branch}.")
    return 0


def _print_result(result, summary: bool):
    print(f"\n== {result.package} ==")
    print(f"Profile:         {result.profile or '—'}")
    print(f"Spec status:     {result.spec_status or '—'}")
    print(f"Declared gate:   {result.declared or '—'}")
    print(f"Computed gate:   {result.computed}")
    for finding in result.findings:
        print(f"  {finding}")
    if not summary and result.reasons:
        print("  To move the gate forward:")
        seen = set()
        for gate_state, message in sorted(result.reasons, key=lambda r: GATE_STATES.index(r[0])):
            if (gate_state, message) not in seen:
                seen.add((gate_state, message))
                print(f"    [{gate_state}] {message}")
    print(f"  {len(result.errors)} errors, {len(result.warnings)} warnings")


def spec_validate(args) -> int:
    packages = _packages(args)
    if not packages:
        print("No spec packages to validate.")
        return 0
    results = [Validator(p, config()).validate() for p in packages]
    if args.json:
        print(json.dumps([{
            "package": r.package, "profile": r.profile, "spec_status": r.spec_status, "declared": r.declared,
            "computed": r.computed, "findings": [f.__dict__ for f in r.findings],
            "reasons": [{"state": s, "reason": m} for s, m in r.reasons],
        } for r in results], ensure_ascii=False, indent=2))
    else:
        for result in results:
            _print_result(result, args.summary)
    return 1 if any(r.errors for r in results) else 0


def _branch() -> str:
    try:
        return subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=config().root, capture_output=True, text=True, check=True).stdout.strip()
    except (subprocess.CalledProcessError, OSError):
        return ""


def spec_start(args) -> int:
    cfg = config()
    package = state.find_package(cfg, args.reference)
    data = state.start(cfg, package, args.branch or _branch())
    print(f"Active spec: {data['id']} ({data['path']}) on branch {data['branch'] or 'unset'}. Product edits are unlocked.")
    return 0


def spec_status(args) -> int:
    cfg = config()
    active = state.active_spec(cfg, _branch())
    if not active:
        print("No active spec in this working copy.")
        return 0
    print(json.dumps(active, indent=2))
    package = cfg.root / active["path"]
    if package.is_dir():
        _print_result(Validator(package, cfg).validate(), summary=False)
    return 0


def spec_stop(args) -> int:
    print("Active spec released." if state.stop(config()) else "There was no active spec.")
    return 0


# -- scanners -----------------------------------------------------------------------------------


def scan_secrets(args) -> int:
    cfg = config()
    if args.diff:
        findings = secrets.scan_diff(args.diff, cfg.root, args.include_tests)
    else:
        targets = [Path(p) for p in args.paths] or [cfg.root]
        findings = secrets.scan_paths(targets, cfg.root, args.include_tests)
    for finding in findings:
        print(f"SECRET {finding}")
    print(f"{len(findings)} possible secrets. Values are never printed; the fingerprint correlates findings within this run.")
    return 1 if findings else 0


def _dependency_rows():
    rows = []
    for package in _packages(argparse.Namespace(all=True)):
        file = package / "security.md"
        if not file.exists():
            continue
        document = Document(str(file), file.read_text(encoding="utf-8"))
        table = document.table(document.find("DEPENDENCIES", level=2), "DEPENDENCY", "STATUS")
        if table is not None:
            rows += [(package.name, r.get(table, "DEPENDENCY"), normalize(r.get(table, "STATUS"))) for r in table.rows]
    return rows


def scan_deps(args) -> int:
    cfg = config()
    changed = dependencies.changes(dependencies.manifests(cfg.root, args.base), dependencies.manifests(cfg.root))
    if not changed:
        print(f"No new or updated dependencies since {args.base}.")
        return 0
    rows = _dependency_rows()
    missing = 0
    for dep in changed:
        name = dependencies.normalize_name(dep.name)
        short = name.split(":")[-1]
        covering = [(p, s) for p, text, s in rows
                    if name in dependencies.normalize_name(text)
                    or re.search(rf"(?<![\w-]){re.escape(short)}(?![\w-])", dependencies.normalize_name(text))]
        evaluated = [p for p, s in covering if s == "EVALUATED"]
        status = f"EVALUATED in {', '.join(evaluated)}" if evaluated else ("registered, not evaluated" if covering else "NOT EVALUATED")
        print(f"{dep.manifest}: {dep.name} {dep.version or ''} -> {status}")
        missing += 0 if evaluated else 1
    print(f"{len(changed)} new or updated dependencies; {missing} without a recorded evaluation in a spec package.")
    return 1 if args.require_evaluation and missing else 0


def scan_paths(args) -> int:
    cfg = config()
    critical = paths.load_critical_paths(cfg.root, cfg["criticalPathsFile"])
    if not critical:
        print(f"No critical paths registry at {cfg['criticalPathsFile']}.", file=sys.stderr)
        return 1
    changed = paths.changed_files(args.base, cfg.root)
    exemption = re.search(r"SPEC-EXEMPT:\s*(.+)", paths.commit_messages(args.base, cfg.root))
    specs_prefix = cfg["specsDir"].rstrip("/") + "/"
    touched_packages = {Path(c).parts[1] for c in changed if c.startswith(specs_prefix) and len(Path(c).parts) > 2}
    declared = {}
    for name in touched_packages:
        spec = cfg.specs_dir / name / "spec.md"
        if spec.exists():
            document = Document(str(spec), spec.read_text(encoding="utf-8"))
            table = document.table(document.find("AFFECTED PATHS"), "PATH")
            declared[name] = [r.get(table, "PATH").strip("`") for r in table.rows] if table else []
    uncovered = 0
    for file in changed:
        hits = [c for c in critical if c.covers(file)]
        if not hits:
            continue
        covered_by = [p for p, patterns in declared.items() if any(paths.matches(pattern, file) for pattern in patterns)]
        if covered_by:
            print(f"OK       {file} ({hits[0].area}) -> {', '.join(covered_by)}")
        elif exemption:
            print(f"EXEMPT   {file} ({hits[0].area}) -> SPEC-EXEMPT: {exemption.group(1).strip()}")
        else:
            uncovered += 1
            print(f"MISSING  {file} ({hits[0].area}, minimum profile {hits[0].minimum_profile}): no spec package changed in this branch declares it")
    print(f"{uncovered} critical files without an updated spec package.")
    return 1 if uncovered else 0


def gate(args) -> int:
    cfg = config()
    codes = [spec_validate(argparse.Namespace(all=True, packages=[], json=False, summary=True))]
    print("\n== Secrets in the framework and the specs ==")
    codes.append(scan_secrets(argparse.Namespace(diff=None, paths=[str(cfg.root / "sdd"), str(cfg.specs_dir)], include_tests=False)))
    if args.base:
        print(f"\n== Secrets in lines added since {args.base} ==")
        codes.append(scan_secrets(argparse.Namespace(diff=args.base, paths=[], include_tests=False)))
        print("\n== Critical paths ==")
        codes.append(scan_paths(args))
        print("\n== Dependencies ==")
        codes.append(scan_deps(argparse.Namespace(base=args.base, require_evaluation=True)))
    return 1 if any(codes) else 0


# -- hooks and doctor ---------------------------------------------------------------------------


def hooks_cmd(args) -> int:
    root = config().root
    if args.action == "install":
        subprocess.run(["git", "config", "core.hooksPath", "sdd/hooks"], cwd=root, check=True)
        for hook in (root / "sdd" / "hooks").iterdir():
            hook.chmod(0o755)
        print("Git hooks installed: pre-commit, commit-msg and pre-push run the SDD gates.")
    else:
        subprocess.run(["git", "config", "--unset", "core.hooksPath"], cwd=root, check=False)
        print("Git hooks uninstalled.")
    return 0


def doctor(args) -> int:
    cfg = config()
    checks = []

    def check(name, ok, hint=""):
        checks.append(ok)
        print(f"{'OK  ' if ok else 'FAIL'} {name}" + (f" — {hint}" if hint and not ok else ""))

    check("Python 3.11+", sys.version_info >= (3, 11), "install Python 3.11 or newer")
    check("AGENTS.md exists", (cfg.root / "AGENTS.md").exists())
    check(f"{CONFIG_FILE.as_posix()} is valid JSON", _valid_json(cfg.root / CONFIG_FILE))
    check("spec templates exist", len(list((cfg.root / "sdd" / "templates" / "spec").glob("*.md"))) == 4)
    check("critical paths registry", bool(paths.load_critical_paths(cfg.root, cfg["criticalPathsFile"])), cfg["criticalPathsFile"])
    hooks_path = subprocess.run(["git", "config", "--get", "core.hooksPath"], cwd=cfg.root, capture_output=True, text=True).stdout.strip()
    check("git hooks installed", hooks_path == "sdd/hooks", "python sdd/tools/sdd.py hooks install")
    ignored = subprocess.run(["git", "check-ignore", "-q", f"{cfg['stateDir']}/active-spec.json"], cwd=cfg.root).returncode == 0
    check(f"{cfg['stateDir']}/ is gitignored", ignored, f"add '{cfg['stateDir']}/' to .gitignore")
    return 0 if all(checks) else 1


def _valid_json(path: Path) -> bool:
    if not path.exists():
        return True
    try:
        json.loads(path.read_text(encoding="utf-8"))
        return True
    except ValueError:
        return False


def main(argv=None) -> int:
    _utf8_output()
    parser = argparse.ArgumentParser(prog="sdd", description="Spec-driven development with a mandatory security gate")
    sub = parser.add_subparsers(dest="command", required=True)

    spec = sub.add_parser("spec", help="spec packages").add_subparsers(dest="action", required=True)
    p = spec.add_parser("new", help="create a spec package from the templates")
    p.add_argument("id")
    p.add_argument("title")
    p.set_defaults(func=spec_new)
    p = spec.add_parser("validate", help="validate packages and compute the security gate")
    p.add_argument("packages", nargs="*")
    p.add_argument("--all", action="store_true")
    p.add_argument("--json", action="store_true")
    p.add_argument("--summary", action="store_true", help="omit what is pending per state")
    p.set_defaults(func=spec_validate)
    p = spec.add_parser("start", help="make a spec the active one in this working copy (unlocks product edits)")
    p.add_argument("reference", help="spec ID prefix or package path")
    p.add_argument("--branch", default="")
    p.set_defaults(func=spec_start)
    spec.add_parser("status", help="show the active spec and its gate").set_defaults(func=spec_status)
    spec.add_parser("stop", help="release the active spec").set_defaults(func=spec_stop)

    scan = sub.add_parser("scan", help="secrets, dependencies and critical paths").add_subparsers(dest="action", required=True)
    p = scan.add_parser("secrets", help="find secrets without printing their values")
    p.add_argument("paths", nargs="*")
    p.add_argument("--diff", metavar="REF", help="only lines added since REF")
    p.add_argument("--include-tests", action="store_true")
    p.set_defaults(func=scan_secrets)
    p = scan.add_parser("deps", help="new or changed dependencies and their evaluation")
    p.add_argument("--base", required=True)
    p.add_argument("--require-evaluation", action="store_true")
    p.set_defaults(func=scan_deps)
    p = scan.add_parser("paths", help="critical paths changed without a spec package")
    p.add_argument("--base", required=True)
    p.set_defaults(func=scan_paths)

    p = sub.add_parser("gate", help="every check the CI gate runs")
    p.add_argument("--base", help="base branch of the change (e.g. origin/dev)")
    p.set_defaults(func=gate)

    p = sub.add_parser("hooks", help="install the git hooks")
    p.add_argument("action", choices=["install", "uninstall"])
    p.set_defaults(func=hooks_cmd)

    sub.add_parser("doctor", help="check the installation").set_defaults(func=doctor)

    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except (FileNotFoundError, subprocess.CalledProcessError) as exc:
        print(f"sdd: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
