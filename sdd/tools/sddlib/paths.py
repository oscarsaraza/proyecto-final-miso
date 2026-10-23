import re
import subprocess
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from .markdown import Document, normalize


@lru_cache(maxsize=512)
def _glob_regex(pattern: str) -> re.Pattern:
    parts, i = [], 0
    while i < len(pattern):
        if pattern.startswith("**/", i):
            parts.append("(?:.*/)?")
            i += 3
        elif pattern.startswith("**", i):
            parts.append(".*")
            i += 2
        elif pattern[i] == "*":
            parts.append("[^/]*")
            i += 1
        elif pattern[i] == "?":
            parts.append("[^/]")
            i += 1
        else:
            parts.append(re.escape(pattern[i]))
            i += 1
    return re.compile("^" + "".join(parts) + "$")


def _clean(value: str) -> str:
    value = value.strip().strip("`").replace("\\", "/")
    return value[2:] if value.startswith("./") else value


def matches(pattern: str, path: str) -> bool:
    pattern, path = _clean(pattern), _clean(path)
    if pattern.endswith("/"):
        pattern += "**"
    return bool(_glob_regex(pattern).match(path))


def matches_any(patterns, path: str) -> bool:
    return any(matches(p, path) for p in patterns)


def overlap(a: str, b: str) -> bool:
    """Two patterns overlap when either covers the other taken literally, or they share a fixed prefix."""
    if matches(a, b) or matches(b, a):
        return True
    fixed_a = re.split(r"[*?]", _clean(a), maxsplit=1)[0]
    fixed_b = re.split(r"[*?]", _clean(b), maxsplit=1)[0]
    return bool(fixed_a) and bool(fixed_b) and (fixed_a.startswith(fixed_b) or fixed_b.startswith(fixed_a))


@dataclass
class CriticalPath:
    pattern: str
    area: str
    reason: str
    minimum_profile: str
    line: int

    def covers(self, path: str) -> bool:
        return matches(self.pattern, path)


def load_critical_paths(root: Path, relative: str) -> list:
    path = root / relative
    if not path.exists():
        return []
    document = Document(str(path), path.read_text(encoding="utf-8"))
    result = []
    for section in document.sections:
        for table in section.tables:
            if not (table.has("PATTERN") and table.has("MINIMUM PROFILE")):
                continue
            for row in table.rows:
                pattern = row.get(table, "PATTERN").strip("`")
                if pattern and not pattern.startswith("<"):
                    result.append(CriticalPath(pattern, row.get(table, "AREA"), row.get(table, "WHY"),
                                               normalize(row.get(table, "MINIMUM PROFILE")), row.line))
    return result


def _git(root: Path, *args) -> str:
    return subprocess.run(["git", *args], cwd=root, capture_output=True, text=True, encoding="utf-8", check=True).stdout


def merge_base(base_ref: str, root: Path) -> str:
    return _git(root, "merge-base", base_ref, "HEAD").strip()


def untracked(root: Path) -> list:
    return [l.strip() for l in _git(root, "ls-files", "--others", "--exclude-standard").splitlines() if l.strip()]


def changed_files(base_ref: str, root: Path) -> list:
    """Changes since the fork point, including uncommitted and untracked files."""
    tracked = _git(root, "diff", "--name-only", "--no-renames", merge_base(base_ref, root)).splitlines()
    return sorted({l.strip() for l in tracked if l.strip()} | set(untracked(root)))


def commit_messages(base_ref: str, root: Path) -> str:
    return _git(root, "log", "--format=%B", f"{merge_base(base_ref, root)}..HEAD")
