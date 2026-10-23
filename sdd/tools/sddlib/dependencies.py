import json
import re
import subprocess
import tomllib
from dataclasses import dataclass
from pathlib import PurePosixPath


@dataclass(frozen=True)
class Dependency:
    manifest: str
    name: str
    version: str


def normalize_name(name: str) -> str:
    name = re.sub(r"\[.*?\]", "", name.strip().strip("`"))
    return re.sub(r"[-_.]+", "-", name).lower()


def _pep508(spec: str):
    m = re.match(r"\s*([A-Za-z0-9][A-Za-z0-9._-]*)(\[[^\]]*\])?\s*(.*)", spec)
    return (m.group(1), m.group(3).split(";")[0].strip()) if m else None


def _pyproject(text: str) -> dict:
    data = tomllib.loads(text)
    deps = {}
    poetry = data.get("tool", {}).get("poetry", {})
    groups = [poetry.get("dependencies", {}), poetry.get("dev-dependencies", {})]
    groups += [g.get("dependencies", {}) for g in poetry.get("group", {}).values()]
    for group in groups:
        for name, value in group.items():
            if name.lower() != "python":
                deps[name] = value.get("version", "") if isinstance(value, dict) else str(value)
    project = data.get("project", {})
    specs = list(project.get("dependencies", []))
    for extra in project.get("optional-dependencies", {}).values():
        specs += extra
    for group in data.get("dependency-groups", {}).values():
        specs += [s for s in group if isinstance(s, str)]
    for spec in specs:
        pair = _pep508(spec)
        if pair:
            deps[pair[0]] = pair[1]
    return deps


def _requirements(text: str) -> dict:
    deps = {}
    for line in text.splitlines():
        line = line.split("#")[0].strip()
        if line and not line.startswith("-"):
            pair = _pep508(line)
            if pair:
                deps[pair[0]] = pair[1]
    return deps


def _package_json(text: str) -> dict:
    data = json.loads(text)
    deps = {}
    for key in ("dependencies", "devDependencies", "optionalDependencies", "peerDependencies"):
        deps.update(data.get(key, {}))
    return deps


def _version_catalog(text: str) -> dict:
    data = tomllib.loads(text)
    versions = data.get("versions", {})

    def resolve(value) -> str:
        if isinstance(value, dict):
            if "ref" in value:
                return str(versions.get(value["ref"], ""))
            return str(value.get("strictly") or value.get("require") or value.get("prefer") or "")
        return str(value or "")

    deps = {}
    for entry in data.get("libraries", {}).values():
        if isinstance(entry, str):
            parts = entry.split(":")
            deps[":".join(parts[:2])] = parts[2] if len(parts) > 2 else ""
            continue
        module = entry.get("module") or f"{entry.get('group', '')}:{entry.get('name', '')}"
        ref = entry.get("version.ref")
        deps[module] = str(versions.get(ref, "")) if ref else resolve(entry.get("version"))
    for entry in data.get("plugins", {}).values():
        if isinstance(entry, str):
            name, _, version = entry.partition(":")
            deps[name] = version
            continue
        ref = entry.get("version.ref")
        deps[entry.get("id", "")] = str(versions.get(ref, "")) if ref else resolve(entry.get("version"))
    return deps


_COORDINATE = re.compile(
    r"""(?:implementation|api|kapt|ksp|testImplementation|androidTestImplementation|debugImplementation|compileOnly|runtimeOnly)"""
    r"""\s*\(\s*["']([\w.-]+):([\w.-]+):([\w.+-]+)["']"""
)


def _gradle(text: str) -> dict:
    return {f"{g}:{a}": v for g, a, v in _COORDINATE.findall(text)}


def _go_mod(text: str) -> dict:
    return dict(re.findall(r"^\s*(?:require\s+)?([\w.\-/]+\.[\w.\-/]+)\s+(v[\w.\-+]+)", text, re.M))


READERS = (
    ("pyproject.toml", _pyproject),
    ("requirements*.txt", _requirements),
    ("package.json", _package_json),
    ("libs.versions.toml", _version_catalog),
    ("build.gradle.kts", _gradle),
    ("build.gradle", _gradle),
    ("go.mod", _go_mod),
)


def _reader(path: str):
    name = PurePosixPath(path)
    for pattern, reader in READERS:
        if name.match(pattern):
            return reader
    return None


def _git(root, *args) -> str:
    return subprocess.run(["git", *args], cwd=root, capture_output=True, text=True, encoding="utf-8", check=True).stdout


def manifests(root, ref: str = None) -> dict:
    listing = _git(root, "ls-tree", "-r", "--name-only", ref) if ref else _git(root, "ls-files")
    result = {}
    for path in listing.splitlines():
        if "node_modules/" in path or _reader(path) is None:
            continue
        try:
            text = _git(root, "show", f"{ref}:{path}") if ref else (root / path).read_text(encoding="utf-8")
            result[path] = _reader(path)(text)
        except (subprocess.CalledProcessError, ValueError, OSError, tomllib.TOMLDecodeError):
            continue
    return result


def changes(before: dict, after: dict) -> list:
    changed = []
    for manifest, deps in after.items():
        previous = {normalize_name(n): v for n, v in before.get(manifest, {}).items()}
        for name, version in deps.items():
            key = normalize_name(name)
            if key not in previous or previous[key] != version:
                changed.append(Dependency(manifest, name, version))
    return changed
