import hashlib
import hmac
import re
import secrets as _random
import subprocess
from dataclasses import dataclass
from pathlib import Path

from .paths import merge_base, untracked

PATTERNS = (
    ("AWS access key", re.compile(r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b")),
    ("Private key", re.compile(r"-----BEGIN (?:[A-Z]+ )?PRIVATE KEY-----")),
    ("GitHub token", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{36,}\b")),
    ("GitLab token", re.compile(r"\bglpat-[A-Za-z0-9_-]{20,}\b")),
    ("Slack token", re.compile(r"\bxox[abprs]-[A-Za-z0-9-]{10,}\b")),
    ("Twilio account SID", re.compile(r"\bAC[0-9a-f]{32}\b")),
    ("Twilio API key", re.compile(r"\bSK[0-9a-f]{32}\b")),
    ("Google API key", re.compile(r"\bAIza[0-9A-Za-z_-]{35}\b")),
    ("Stripe secret key", re.compile(r"\b[rs]k_live_[0-9A-Za-z]{16,}\b")),
    ("JWT", re.compile(r"\beyJ[A-Za-z0-9_-]{10,}\.eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}")),
    ("Credential in URL", re.compile(r"\b[a-z][a-z0-9+.-]*://[^\s:/@'\"]+:([^\s:/@'\"]{3,})@")),
    (
        "Hard-coded secret",
        re.compile(
            r"(?i)(?:password|passwd|secret|token|api[_-]?key|auth[_-]?token|private[_-]?key|contrase[ñn]a)\w*"
            r"[\"']?(?:\s*:\s*[A-Za-z_][\w\[\], .|]*?)?\s*[:=]\s*[\"']([^\"'\s]{8,})[\"']"
        ),
    ),
    (
        "Secret in environment file",
        re.compile(
            r"^\s*(?:export\s+)?[A-Z0-9_]*(?:PASSWORD|SECRET|TOKEN|API_KEY|AUTH_TOKEN|PRIVATE_KEY)[A-Z0-9_]*"
            r"\s*[:=]\s*([^\s\"'#]{8,})\s*$"
        ),
    ),
)

GENERIC = ("Hard-coded secret", "Secret in environment file", "Credential in URL")
IGNORE_MARKER = "sdd:allow-secret"
_PLACEHOLDERS = (
    "EXAMPLE", "CHANGEME", "CHANGE_ME", "PLACEHOLDER", "DUMMY", "FAKE", "XXXX", "****", "YOUR_", "REPLACE",
    "REDACTED", "TOK_", "EJEMPLO", "CAMBIAR",
)
_REFERENCE = re.compile(r"[<>${}()\[\]]|^\w+\.\w+")
_TYPE_NAMES = {"SecretStr", "SecretBytes"}
_TEST_PATH = re.compile(
    r"(^|/)(tests?|__tests__|androidTest|spec|fixtures)/"
    r"|(^|/)(test_[^/]*|[^/]*_test\.(py|go)|conftest\.py|[^/]*\.(spec|test)\.[jt]sx?|[^/]*Tests?\.(kt|java|swift))$"
)
_TF_VARIABLE = re.compile(r'^\s*variable\s+"([^"]+)"')
_TF_DEFAULT = re.compile(r'^\s*default\s*=\s*"([^"\s]{8,})"')
_SENSITIVE_NAME = re.compile(r"(?i)password|passwd|secret|token|api_?key|private_?key")
_SKIP_DIRS = {".git", "node_modules", "build", "dist", ".gradle", ".venv", "venv", "__pycache__", ".angular", "coverage", ".sdd"}
_MAX_BYTES = 2_000_000

# A fresh key per run: the fingerprint correlates findings within one run but cannot be used
# to confirm guessed passwords from a public CI log.
_FINGERPRINT_KEY = _random.token_bytes(32)


@dataclass
class Finding:
    path: str
    line: int
    kind: str
    fingerprint: str
    length: int

    def __str__(self) -> str:
        return f"{self.path}:{self.line} {self.kind} (fingerprint {self.fingerprint}, {self.length} chars)"


def is_test_path(path: str) -> bool:
    return bool(_TEST_PATH.search(path.replace("\\", "/")))


def _placeholder(value: str) -> bool:
    upper = value.upper()
    return (any(p in upper for p in _PLACEHOLDERS) or len(set(value)) <= 2 or bool(_REFERENCE.search(value))
            or value in _TYPE_NAMES)


def _fingerprint(value: str) -> str:
    return hmac.new(_FINGERPRINT_KEY, value.encode("utf-8"), hashlib.sha256).hexdigest()[:10]


def scan_line(line: str, generic: bool = True):
    if IGNORE_MARKER in line:
        return []
    found = []
    for kind, pattern in PATTERNS:
        if kind in GENERIC and not generic:
            continue
        for m in pattern.finditer(line):
            value = m.group(1) if m.groups() else m.group(0)
            if kind in GENERIC:
                if _placeholder(value):
                    continue
            elif "EXAMPLE" in m.group(0).upper():
                continue
            found.append((kind, value))
    return found


def scan_text(text: str, path: str, include_tests: bool = False) -> list:
    generic = include_tests or not is_test_path(path)
    terraform = path.endswith(".tf")
    findings, variable = [], None
    for number, line in enumerate(text.splitlines(), start=1):
        for kind, value in scan_line(line, generic):
            findings.append(Finding(path, number, kind, _fingerprint(value), len(value)))
        if not terraform:
            continue
        m = _TF_VARIABLE.match(line)
        if m:
            variable = m.group(1)
        elif line.startswith("}"):
            variable = None
        elif variable and _SENSITIVE_NAME.search(variable) and IGNORE_MARKER not in line:
            d = _TF_DEFAULT.match(line)
            if d and not _placeholder(d.group(1)):
                findings.append(Finding(path, number, "Secret default in Terraform variable", _fingerprint(d.group(1)), len(d.group(1))))
    return findings


def _files(path: Path):
    if path.is_file():
        yield path
        return
    for child in sorted(path.rglob("*")):
        if child.is_file() and not (set(child.relative_to(path).parts) & _SKIP_DIRS):
            yield child


def scan_paths(paths, root: Path = None, include_tests: bool = False) -> list:
    findings = []
    for path in paths:
        for file in _files(Path(path)):
            if file.stat().st_size > _MAX_BYTES:
                continue
            try:
                text = file.read_text(encoding="utf-8")
            except (UnicodeDecodeError, OSError):
                continue
            name = file.relative_to(root).as_posix() if root and file.is_relative_to(root) else file.as_posix()
            findings.extend(scan_text(text, name, include_tests))
    return findings


def _scan_unified_diff(output: str, include_tests: bool) -> list:
    findings, path, number = [], None, 0
    for line in output.splitlines():
        if line.startswith("+++ "):
            path = line[6:] if line.startswith("+++ b/") else None
        elif line.startswith("@@"):
            m = re.search(r"\+(\d+)", line)
            number = int(m.group(1)) if m else 0
        elif line.startswith("+") and path:
            generic = include_tests or not is_test_path(path)
            for kind, value in scan_line(line[1:], generic):
                findings.append(Finding(path, number, kind, _fingerprint(value), len(value)))
            number += 1
    return findings


def _git_diff(root: Path, *args) -> str:
    return subprocess.run(
        ["git", "diff", "--unified=0", "--no-color", "--no-ext-diff", *args],
        cwd=root, capture_output=True, text=True, encoding="utf-8", errors="replace", check=True,
    ).stdout


def scan_diff(base_ref: str, root: Path, include_tests: bool = False) -> list:
    """Lines added since the fork point, including uncommitted changes and untracked files."""
    findings = _scan_unified_diff(_git_diff(root, merge_base(base_ref, root)), include_tests)
    new_files = [root / r for r in untracked(root)]
    return findings + scan_paths([f for f in new_files if f.is_file()], root, include_tests)


def scan_staged(root: Path, include_tests: bool = False) -> list:
    return _scan_unified_diff(_git_diff(root, "--cached"), include_tests)
