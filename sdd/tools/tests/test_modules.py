import hashlib
import time
import unittest

import base  # noqa: F401
from sddlib import dependencies, paths, secrets
from sddlib.markdown import Document, normalize


def _scan(text, path="x"):
    return secrets.scan_text(text, path)


class Secrets(unittest.TestCase):
    def test_detects_known_patterns(self):
        cases = {
            "AWS access key": "key = " + "AKIA" + "Z9Y8" * 4,
            "GitHub token": "ghp_" + "a1B2" * 9,
            "GitLab token": "glpat-" + "a1B2c3D4" * 3,
            "Private key": "-----BEGIN " + "RSA PRIVATE KEY-----",
            "Twilio account SID": "sid " + "AC" + "0f" * 16,
            "Hard-coded secret": 'JWT_SECRET_KEY = "' + "k3y-" * 4 + '"',
            "Secret in environment file": "TWILIO_AUTH_TOKEN=" + "9f3c" * 8,
            "Credential in URL": "postgresql://user:" + "Cl4ve" + "Larga@db:5432/x",
        }
        for kind, line in cases.items():
            with self.subTest(kind=kind):
                self.assertEqual([kind], [f.kind for f in _scan(line)])

    def test_ignores_placeholders_and_references(self):
        for line in ("aws_key = " + "AKIA" + "IOSFODNN7" + "EXAMPLE", 'password = "${DB_PASSWORD}"',
                     "JWT_SECRET_KEY=<generate-with-openssl>", "token = settings.JWT_SECRET_KEY",
                     'password = "changeme-please"', "DB_PASSWORD=" + "a" * 12):
            with self.subTest(line=line):
                self.assertEqual([], _scan(line))

    def test_python_type_annotation(self):
        self.assertEqual(["Hard-coded secret"], [f.kind for f in _scan('    JWT_SECRET_KEY: str = "' + "s3cr" * 5 + '"')])
        self.assertEqual([], _scan("    JWT_SECRET_KEY: SecretStr"))
        self.assertEqual(["Secret in environment file"], [f.kind for f in _scan("JWT_SECRET_KEY: SecretStrong" + "9f3c" * 4)])

    def test_terraform_variable_default(self):
        hcl = 'variable "db_password" {\n  type = string\n  default = "' + "Pa55w" * 3 + '"\n}\nvariable "region" {\n  default = "us-east-1-long"\n}\n'
        self.assertEqual([(3, "Secret default in Terraform variable")], [(f.line, f.kind) for f in _scan(hcl, "terraform/variables.tf")])

    def test_generic_patterns_skip_test_files_but_provider_keys_do_not(self):
        line = 'password = "' + "Pr0b4ndo" * 2 + '"'
        self.assertEqual([], secrets.scan_text(line, "backend/tests/unit/test_x.py"))
        self.assertEqual(1, len(secrets.scan_text(line, "backend/tests/unit/test_x.py", include_tests=True)))
        self.assertEqual(1, len(secrets.scan_text("AKIA" + "Q7RZ" * 4, "web/src/app/x.spec.ts")))

    def test_explicit_false_positive_marker(self):
        self.assertEqual([], _scan("ghp_" + "a1B2" * 9 + "  # " + secrets.IGNORE_MARKER))

    def test_never_prints_the_value_and_fingerprint_is_not_reproducible(self):
        value = "ghp_" + "Zx9Q" * 9
        finding = _scan("token: " + value)[0]
        self.assertNotIn(value, str(finding))
        self.assertNotIn(value[4:12], str(finding))
        self.assertNotEqual(hashlib.sha256(value.encode()).hexdigest()[:10], finding.fingerprint)
        self.assertEqual(finding.fingerprint, _scan("other: " + value)[0].fingerprint)

    def test_pathological_input_is_fast(self):
        start = time.perf_counter()
        _scan(("password = '" + "a" * 50_000 + " ") * 4 + "x" * 200_000, "x.py")
        _scan("postgres://" + "u" * 100_000 + ":" * 1000, "x.env")
        self.assertLess(time.perf_counter() - start, 2.0)


class Paths(unittest.TestCase):
    def test_globs(self):
        self.assertTrue(paths.matches("backend/app/modules/identity/**", "backend/app/modules/identity/a/b.py"))
        self.assertFalse(paths.matches("backend/app/modules/identity/**", "backend/app/modules/identityx/a.py"))
        self.assertTrue(paths.matches("**/AndroidManifest.xml", "app/src/main/AndroidManifest.xml"))
        self.assertTrue(paths.matches("terraform/", "terraform/modules/alb/main.tf"))
        self.assertTrue(paths.matches("**/.env", ".env"))
        self.assertTrue(paths.matches("./src/**", "src/a.py"))
        self.assertFalse(paths.matches("*.tf", "terraform/main.tf"))

    def test_overlap(self):
        self.assertTrue(paths.overlap("backend/app/modules/**", "backend/app/modules/identity/**"))
        self.assertTrue(paths.overlap("**/identity/**", "backend/app/modules/identity/service.py"))
        self.assertFalse(paths.overlap("backend/app/modules/identity/**", "web/src/app/core/auth.ts"))


class Dependencies(unittest.TestCase):
    def test_poetry_and_changes(self):
        before = dependencies._pyproject('[tool.poetry.dependencies]\npython = ">=3.12"\nfastapi = ">=0.115.0"\n')
        after = dependencies._pyproject('[tool.poetry.dependencies]\npython = ">=3.12"\nfastapi = ">=0.120.0"\nargon2-cffi = ">=23.1"\n'
                                        '[tool.poetry.group.dev.dependencies]\npytest = ">=8"\n')
        changed = dependencies.changes({"pyproject.toml": before}, {"pyproject.toml": after})
        self.assertEqual({"fastapi", "argon2-cffi", "pytest"}, {c.name for c in changed})

    def test_other_manifests(self):
        self.assertEqual({"passlib": ">=1.7.4", "httpx": "==0.28.1"},
                         dependencies._requirements("passlib[bcrypt]>=1.7.4\n# note\nhttpx==0.28.1\n-r other.txt\n"))
        self.assertEqual({"@angular/core": "^22.2.0", "vitest": "^5.0.0"},
                         dependencies._package_json('{"dependencies": {"@angular/core": "^22.2.0"}, "devDependencies": {"vitest": "^5.0.0"}}'))
        catalog = dependencies._version_catalog(
            '[versions]\nbiometric = "1.2.0-alpha05"\n[libraries]\n'
            'androidx-biometric = { group = "androidx.biometric", name = "biometric", version.ref = "biometric" }\n'
            'okhttp = "com.squareup.okhttp3:okhttp:4.12.0"\n')
        self.assertEqual({"androidx.biometric:biometric": "1.2.0-alpha05", "com.squareup.okhttp3:okhttp": "4.12.0"}, catalog)
        self.assertEqual({"github.com/gin-gonic/gin": "v1.10.0"}, dependencies._go_mod("module x\n\nrequire github.com/gin-gonic/gin v1.10.0\n"))

    def test_names(self):
        self.assertEqual("pyjwt", dependencies.normalize_name("PyJWT[crypto]"))
        self.assertEqual("python-multipart", dependencies.normalize_name("python_multipart"))


class Markdown(unittest.TestCase):
    TEXT = """# Title

<!-- ignored guidance: | A | B | -->

## Section 1. One

| ID | Value |
|---|---|
| X-01 | a \\| b |
| X-02 | c |

### Sub

N/A: because it does not apply here

```
## not a heading
```
"""

    def test_tables_sections_and_not_applicable(self):
        document = Document("x.md", self.TEXT)
        section = document.find("ONE", level=2)
        table = document.table(section, "ID", "VALUE")
        self.assertEqual(["a | b", "c"], [r.get(table, "VALUE") for r in table.rows])
        self.assertEqual("BECAUSE IT DOES NOT APPLY HERE", document.not_applicable(document.find("SUB")))
        self.assertIsNone(document.find("NOT A HEADING"))

    def test_normalize(self):
        self.assertEqual("CRITICO SI", normalize("**Crítico** sí"))


if __name__ == "__main__":
    unittest.main()
