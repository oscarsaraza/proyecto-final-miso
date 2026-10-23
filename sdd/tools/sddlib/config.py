import json
from dataclasses import dataclass, field
from pathlib import Path

CONFIG_FILE = Path("sdd") / "config.json"

DEFAULTS = {
    "specsDir": "specs",
    "stateDir": ".sdd",
    "protectedBranches": ["main", "master", "dev", "develop", "qa"],
    "storyBranch": r"^(feature|fix)/(?P<story>[A-Z][A-Z0-9]*(?:-[A-Z0-9]+)*-\d+(?:\.\d+)?)-[a-z0-9][a-z0-9.-]*$",
    "commitPattern": r"^(feat|fix|chore|docs|refactor|test|perf|ci|build|security|revert|style)(\([a-z0-9._/-]+\))?!?: \S.+",
    "spec": {
        "required": ["**"],
        "exempt": [
            "**/*.md", "docs/**", "specs/**", "sdd/**", ".sdd/**", ".gitignore", ".gitattributes", "LICENSE",
        ],
    },
    "adr": {
        "dir": "docs/adr",
        "triggers": [
            {"files": ["**/Dockerfile*"], "added": r"^\s*FROM\s", "reason": "a container base image change"},
            {"files": ["**/*.tf", "**/*.tfvars.example"], "added": r"\b(aws_kms_key|aws_iam_|aws_db_instance|aws_lb_listener|aws_security_group|google_kms|azurerm_key_vault)", "reason": "an infrastructure security or topology change"},
            {"files": ["**/pyproject.toml", "**/requirements*.txt", "**/package.json", "**/*.gradle*", "**/libs.versions.toml", "**/go.mod", "**/Cargo.toml", "**/pom.xml"], "added": r"(?i)\b(jwt|jose|oauth|openid|passlib|bcrypt|argon2|cryptography|bouncycastle|tink|keycloak|auth0|cognito|openai|anthropic|langchain)\b", "reason": "a new authentication, cryptography or AI SDK"},
        ],
    },
    "secrets": {
        "denyRead": [
            ".env", ".env.*", "**/.env", "**/.env.*", "**/*.pem", "**/*.key", "**/*.p12", "**/*.pfx",
            "**/id_rsa*", "**/id_ed25519*", "**/*.keystore", "**/*.jks", "**/credentials", "**/credentials.json",
            "**/*.tfstate", "**/*.tfstate.*", "**/*.tfvars", "**/secrets.*", "**/.netrc", "**/.npmrc", "**/.pypirc",
        ],
        "allowRead": ["**/.env.example", "**/.env.sample", "**/*.tfvars.example"],
    },
    "criticalPathsFile": "sdd/security/critical-paths.md",
    "requireSignatures": True,
}


@dataclass
class Config:
    root: Path
    data: dict = field(default_factory=dict)

    def __getitem__(self, key):
        return self.data[key]

    @property
    def specs_dir(self) -> Path:
        return self.root / self.data["specsDir"]

    @property
    def state_dir(self) -> Path:
        return self.root / self.data["stateDir"]


def _merge(base: dict, override: dict) -> dict:
    merged = dict(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def find_root(start: Path) -> Path:
    start = start.resolve()
    for candidate in [start, *start.parents]:
        if (candidate / ".git").exists() or (candidate / CONFIG_FILE).exists():
            return candidate
    return start


def load(root: Path = None) -> Config:
    root = find_root(root or Path.cwd())
    path = root / CONFIG_FILE
    data = DEFAULTS
    if path.exists():
        data = _merge(DEFAULTS, json.loads(path.read_text(encoding="utf-8")))
    return Config(root, data)
