# Ecosystems

| Ecosystem | Manifest | Lockfile | Audit command | OSV ecosystem |
|---|---|---|---|---|
| Python (Poetry) | `pyproject.toml` | `poetry.lock` | `poetry export -f requirements.txt \| pip-audit -r /dev/stdin` | `PyPI` |
| Python (uv) | `pyproject.toml` | `uv.lock` | `uv export \| pip-audit -r /dev/stdin` | `PyPI` |
| Python (pip) | `requirements*.txt` | pinned requirements | `pip-audit -r requirements.txt` | `PyPI` |
| JavaScript (npm) | `package.json` | `package-lock.json` | `npm audit --omit=dev` | `npm` |
| JavaScript (pnpm) | `package.json` | `pnpm-lock.yaml` | `pnpm audit --prod` | `npm` |
| Android / JVM | `build.gradle(.kts)`, `libs.versions.toml` | `gradle.lockfile` (if enabled) | OSV query or the OWASP Dependency-Check plugin | `Maven` |
| Go | `go.mod` | `go.sum` | `govulncheck ./...` | `Go` |

OSV batch query (public package names and versions only):

```bash
curl -s https://api.osv.dev/v1/querybatch -d '{"queries":[{"package":{"name":"fastapi","ecosystem":"PyPI"},"version":"0.115.0"}]}'
```
