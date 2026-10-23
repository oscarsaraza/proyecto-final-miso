import json
import re
import unicodedata
from datetime import date
from pathlib import Path

from .config import Config
from .markdown import Document, key_values


def slugify(text: str) -> str:
    plain = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", plain.lower()).strip("-")[:48]


def marker(config: Config) -> Path:
    return config.state_dir / "active-spec.json"


def story_of(config: Config, branch: str):
    match = re.match(config["storyBranch"], branch or "")
    return match.group("story") if match else None


def story_package(config: Config, story: str):
    for package in sorted(config.specs_dir.glob(f"{story}*")):
        if package.is_dir() and (package.name == story or package.name.startswith(f"{story}-")):
            return package
    return None


def active_spec(config: Config, branch: str = ""):
    story = story_of(config, branch)
    if story:
        package = story_package(config, story)
        if package is None:
            return None
        return {"id": story, "slug": package.name, "path": package.relative_to(config.root).as_posix(), "branch": branch}
    path = marker(config)
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (ValueError, OSError):
        return None


def find_package(config: Config, reference: str) -> Path:
    candidate = Path(reference)
    if not candidate.is_absolute():
        candidate = config.root / candidate
    if candidate.is_dir():
        return candidate
    matches = sorted(p for p in config.specs_dir.glob(f"{reference}*") if p.is_dir())
    if len(matches) == 1:
        return matches[0]
    raise FileNotFoundError(f"no single spec package matches '{reference}' under {config.specs_dir}")


def spec_header(package: Path) -> dict:
    spec = package / "spec.md"
    if not spec.exists():
        return {}
    document = Document(str(spec), spec.read_text(encoding="utf-8"))
    return {k: v for k, (v, _) in key_values(document.sections[0]).items()} if document.sections else {}


def start(config: Config, package: Path, branch: str = "") -> dict:
    header = spec_header(package)
    data = {
        "id": header.get("ID", package.name),
        "slug": package.name,
        "path": package.relative_to(config.root).as_posix(),
        "story": header.get("USER STORY", ""),
        "branch": branch,
        "started": date.today().isoformat(),
    }
    path = marker(config)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    worklog = config.state_dir / "worklogs" / f"{package.name}.md"
    worklog.parent.mkdir(parents=True, exist_ok=True)
    if not worklog.exists():
        worklog.write_text(f"# Worklog · {package.name}\n\nWorking memory only. The spec is the source of truth.\n", encoding="utf-8")
    return data


def stop(config: Config) -> bool:
    path = marker(config)
    existed = path.exists()
    if existed:
        path.unlink()
    return existed
