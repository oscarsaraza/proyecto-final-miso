import re
from dataclasses import dataclass, field
from pathlib import Path

from . import paths as critical_paths
from . import secrets
from .config import Config, load
from .markdown import Document, key_values, normalize

FILES = ("spec.md", "security.md", "test-cases.md", "gate.md")

GATE_STATES = (
    "BLOCKED", "IN_PROGRESS", "IMPLEMENTED", "SECURITY_TESTS_PENDING",
    "SECURITY_REVIEW_PENDING", "RISK_ACCEPTED", "SECURITY_VERIFIED",
)
RANK = {state: i for i, state in enumerate(GATE_STATES)}
SPEC_STATUSES = ("DRAFT", "READY", "IN_PROGRESS", "IN_REVIEW", "DONE", "BLOCKED")

PROFILES = ("LOW", "MEDIUM", "HIGH", "CRITICAL")
LIKELIHOODS = ("LOW", "MEDIUM", "HIGH")
IMPACTS = ("LOW", "MEDIUM", "HIGH", "CRITICAL")
MATRIX = {
    "LOW": {"LOW": "LOW", "MEDIUM": "LOW", "HIGH": "MEDIUM"},
    "MEDIUM": {"LOW": "LOW", "MEDIUM": "MEDIUM", "HIGH": "HIGH"},
    "HIGH": {"LOW": "MEDIUM", "MEDIUM": "HIGH", "HIGH": "CRITICAL"},
    "CRITICAL": {"LOW": "HIGH", "MEDIUM": "CRITICAL", "HIGH": "CRITICAL"},
}
CLASSIFICATIONS = ("PUBLIC", "INTERNAL", "CONFIDENTIAL", "RESTRICTED")
DOMAINS = ("BACKEND", "API", "WEB", "MOBILE", "INFRA", "DATA", "CRYPTO", "SECRETS", "PROCESS")

TRIGGERS = (
    ("PERSONAL_DATA", "PERSONAL DATA"),
    ("SENSITIVE_DATA", "SENSITIVE"),
    ("AUTHENTICATION", "AUTHENTICATION"),
    ("AUTHORIZATION", "AUTHORIZATION"),
    ("PAYMENTS", "PAYMENTS"),
    ("INTEGRATIONS", "THIRD-PARTY"),
    ("INFRASTRUCTURE", "INFRASTRUCTURE"),
    ("MULTI_TENANT", "TENANT"),
    ("MOBILE", "MOBILE"),
    ("WEB", "BROWSER"),
    ("DEPENDENCIES", "DEPENDENCIES"),
    ("CRITICAL_PATHS", "CRITICAL PATHS"),
)
HIGH_TRIGGERS = {"AUTHENTICATION", "AUTHORIZATION", "PAYMENTS", "SENSITIVE_DATA", "INFRASTRUCTURE", "MULTI_TENANT", "CRITICAL_PATHS"}
MEDIUM_TRIGGERS = {"PERSONAL_DATA", "INTEGRATIONS", "MOBILE", "WEB", "DEPENDENCIES"}
THREAT_MODEL_TRIGGERS = {"SENSITIVE_DATA", "AUTHENTICATION", "AUTHORIZATION", "PAYMENTS", "INTEGRATIONS", "INFRASTRUCTURE", "MULTI_TENANT", "CRITICAL_PATHS"}
DOMAIN_FOR_TRIGGER = {"MOBILE": "MOBILE", "WEB": "WEB", "INFRASTRUCTURE": "INFRA"}

LIFECYCLE = (
    ("CONTAIN", "what it contains"),
    ("WHY", "why it is needed"),
    ("WHO CAN ACCESS", "who can access it"),
    ("CAPTURED", "where it is captured"),
    ("TRANSMITTED", "how it is transmitted"),
    ("STORED", "where it is stored"),
    ("COPIES", "copies, caches and backups"),
    ("HOW LONG", "how long it is kept"),
    ("AUDITED", "how access is audited"),
    ("DELETED", "how it is deleted or anonymized"),
    ("LEAK", "what happens if it leaks"),
    ("THIRD PARTIES", "transfers to third parties"),
)
CRYPTO_FIELDS = ("PROTECTS", "TYPE", "ALGORITHM", "RATIONALE", "KEY MANAGEMENT", "PERMISSIONS", "ROTATION", "RECOVERY", "FAILURE", "TESTS")
CRYPTO_TYPES = ("TLS", "AT_REST", "APP_LEVEL", "PASSWORD_HASH", "MAC", "SIGNATURE", "TOKENIZATION", "HASH")
AUTH_CHECKS = (
    "USER IDENTIFICATION", "SECURE AUTHENTICATION", "SESSION MANAGEMENT", "TOKEN EXPIRATION", "REVOCATION",
    "SERVER-SIDE PERMISSION", "PER-RESOURCE ACCESS", "ROLES", "PRIVILEGE SEPARATION", "BRUTE-FORCE",
    "RATE LIMITING", "OTP", "ENUMERATION", "CSRF",
)
TENANCY_CHECKS = (
    "TENANT ISOLATION", "SERVER-SIDE AUTHORIZATION", "HORIZONTAL", "VERTICAL", "RESOURCE IDENTIFIERS",
    "QUERIES AND FILTERS", "SHARED CACHES", "STORAGE AND LOGS", "NEGATIVE CROSS-TENANT TESTS",
)
TEST_CATEGORIES = (
    "UNAUTHENTICATED", "WITHOUT PERMISSIONS", "ANOTHER USER", "CROSS-TENANT", "MALICIOUS INPUT",
    "EXPIRED", "REVOKED", "TAMPERED", "WRONG KEYS", "EXTERNAL SERVICE", "RACE",
    "INFORMATION EXPOSURE", "SECRETS IN CODE", "INSECURE CONFIGURATION", "VULNERABLE DEPENDENCIES",
)
TEST_KINDS = ("FUNCTIONAL", "QUALITY", "SECURITY")
TEST_LEVELS = ("UNIT", "INTEGRATION", "CONTRACT", "E2E", "PERFORMANCE", "ACCESSIBILITY", "STATIC")
QUALITY_CATEGORIES = ("PERFORMANCE", "AVAILABILITY", "ACCESSIBILITY", "USABILITY", "COMPATIBILITY", "MAINTAINABILITY")
QUALITY_LEVELS = {"PERFORMANCE": ("PERFORMANCE",), "ACCESSIBILITY": ("ACCESSIBILITY",)}
SCENARIO_KINDS = (
    "MAIN FLOW", "ALTERNATE", "INVALID INPUT", "LIMITS", "RELATED FLOWS", "SEVERAL USERS", "STATE AND TIME",
)
SCENARIO_KINDS_FOR_TRIGGER = {
    "AUTHENTICATION": ("RELATED FLOWS", "STATE AND TIME"),
    "AUTHORIZATION": ("SEVERAL USERS",),
    "MULTI_TENANT": ("SEVERAL USERS",),
}
_OUT_OF_SCOPE = re.compile(r"^OUT OF SCOPE\s*:\s*\S.{9,}")
_DERIVED = re.compile(r"^DERIVED\s*:\s*\S.{9,}")
TEST_FIELDS = ("COVERS", "KIND", "LEVEL", "PRECONDITIONS", "PROCEDURE", "EXPECTED RESULT", "TOOL", "AUTOMATION", "ENVIRONMENT", "STATUS")

ID_PATTERN = re.compile(r"\b(AC|QR|SR|UC|AB|SC|DATA|THR|CTL|CRY|DEP|RISK|DEC|T|TC|EV)-\d{2,3}\b")
_DATE = re.compile(r"\b\d{4}-\d{2}-\d{2}\b")
_EMPTY = {"", "-", "—", "–", "?", "...", "…", "TBD"}
_AI = re.compile(r"\b(CLAUDE|CODEX|CURSOR|GEMINI|COPILOT|CHATGPT|GPT[\w.-]*|OPENAI|ANTHROPIC|OPENCODE|WINDSURF|DEVIN|LLM|AI|IA|BOT|AGENT|AGENTE|ASSISTANT|ASISTENTE|MODEL)\b")
_COMPLIANCE_CLAIMS = (
    re.compile(r"\b(?:IS|ARE|BE|BEEN)\s+(?:FULLY\s+)?COMPLIANT\b"),
    re.compile(r"\bCOMPL(?:Y|IES) (?:FULLY )?WITH\b"),
    re.compile(r"\b(?:IS|ARE|WAS|WERE|BEEN)\s+CERTIFIED\b"),
    re.compile(r"\bCERTIF(?:IED|ICATION)\s+(?:FOR\s+|UNDER\s+|AGAINST\s+|WITH\s+)?(?:ISO|PCI|SOC ?2|ASVS|MASVS|HIPAA)"),
    re.compile(r"\b(?:FULL|COMPLETE|GUARANTEED)\s+COMPLIANCE\b"),
    re.compile(r"\bGUARANTEES?\s+COMPLIANCE\b"),
    re.compile(r"\bCUMPLE[N]? (?:CON )?(?:LA |EL |LOS |LAS )?(?:LEY|DECRETO|NORMA|CIRCULAR|ASVS|MASVS|OWASP|ISO|PCI)"),
    re.compile(r"\b(?:ESTA|ESTAN|ES|SON)\s+CERTIFICAD[OA]S?\b"),
)
_NEGATION = re.compile(r"\b(?:NOT|NO|N'T|NEVER|DOES NOT|DO NOT)\s+(?:YET\s+|FULLY\s+)?$")
_EVIDENCE_PATH = re.compile(r"`?([\w.-]+(?:/[\w.\-\[\]]+)+\.\w+)(?:::(?:\"([^\"]+)\"|([\w\[\]-]+)))?`?")
_EMAIL = re.compile(r"\b[\w.+-]+@((?:[\w-]+\.)+[A-Za-z]{2,})\b")
_PHONE = re.compile(r"(?<![\w+])(?:\+57[\s-]?3\d{2}[\s-]?\d{3}[\s-]?\d{4}|3\d{2}[\s-]?\d{3}[\s-]?\d{4}|\+\d{1,3}[\s-]?\d{3}[\s-]?\d{3}[\s-]?\d{3,4})(?!\d)")
_RESERVED_DOMAINS = ("example.com", "example.org", "example.net", ".example", ".test", ".invalid", ".localhost")


@dataclass
class Finding:
    severity: str
    code: str
    path: str
    line: int
    message: str

    def __str__(self) -> str:
        return f"{self.severity} {self.code} {self.path}:{self.line} {self.message}"


@dataclass
class Record:
    id: str
    fields: dict
    path: str
    line: int
    lines: dict = field(default_factory=dict)

    def __getitem__(self, key: str) -> str:
        key = normalize(key)
        for name, value in self.fields.items():
            if key in name:
                return value
        return ""


@dataclass
class Result:
    package: str
    profile: str = ""
    spec_status: str = ""
    declared: str = ""
    computed: str = "SECURITY_VERIFIED"
    findings: list = field(default_factory=list)
    reasons: list = field(default_factory=list)

    @property
    def errors(self) -> list:
        return [f for f in self.findings if f.severity == "ERROR"]

    @property
    def warnings(self) -> list:
        return [f for f in self.findings if f.severity == "WARNING"]


def empty(value: str) -> bool:
    n = normalize(value)
    return n in _EMPTY or "<FILL" in n


def unknown(value: str) -> bool:
    n = normalize(value)
    return n.startswith("UNKNOWN") or n.startswith("DESCONOCIDO")


def ids(value: str, *prefixes: str) -> list:
    found = [m.group(0) for m in ID_PATTERN.finditer(value or "")]
    if prefixes:
        found = [i for i in found if i.split("-")[0] in prefixes]
    return list(dict.fromkeys(found))


def is_yes(value: str) -> bool:
    return normalize(value) in ("YES", "Y", "SI", "TRUE")


def is_ai(name: str) -> bool:
    return bool(_AI.search(normalize(name)))


class Validator:
    def __init__(self, package, config: Config = None):
        self.path = Path(package).resolve()
        self.config = config or load(self.path)
        self.root = self.config.root
        self.r = Result(self.path.name)
        self.docs = {}
        self.triggers = {}
        self.profile = "LOW"
        self.defined = {}
        self.ac, self.qr, self.sr, self.uc, self.ab, self.t = {}, {}, {}, {}, {}, {}
        self.qr_na = False
        self.data, self.lifecycle, self.thr, self.ctl, self.cry = {}, {}, {}, {}, {}
        self.dep, self.risk, self.dec, self.tc, self.ev, self.sc = {}, {}, {}, {}, {}, {}
        self.reviews, self.acceptances, self.checklists, self.coverage, self.closeout = [], [], [], [], {}

    # -- helpers ------------------------------------------------------------------------------

    def error(self, code, path, line, message):
        self.r.findings.append(Finding("ERROR", code, path, line, message))

    def warn(self, code, path, line, message):
        self.r.findings.append(Finding("WARNING", code, path, line, message))

    def reason(self, state, message):
        self.r.reasons.append((state, message))

    def on(self, trigger) -> bool:
        return self.triggers.get(trigger, False)

    def _records(self, file, section, columns, prefix, required=True) -> dict:
        doc = self.docs.get(file)
        if doc is None or section is None:
            return {}
        table = doc.table(section, *columns, tree=True)
        if table is None:
            if required:
                self.error("E04", file, section.line, f"'{section.title}' needs a table with columns: {', '.join(columns)}")
            return {}
        records = {}
        for row in table.rows:
            values = dict(row.cells)
            identifier = normalize(next(iter(values.values()), ""))
            if all(empty(v) for v in values.values()):
                continue
            if not re.fullmatch(rf"{prefix}-\d{{2,3}}", identifier):
                self.error("E05", file, row.line, f"invalid identifier '{identifier}'; expected {prefix}-NN")
                continue
            if identifier in records or identifier in self.defined:
                self.error("E06", file, row.line, f"{identifier} is defined more than once")
                continue
            records[identifier] = Record(identifier, values, file, row.line)
            self.defined[identifier] = (file, row.line)
        return records

    def _blocks(self, file, section, prefix, define=True) -> dict:
        doc = self.docs.get(file)
        if doc is None or section is None:
            return {}
        blocks = {}
        for sub in doc.children(section):
            found = ids(sub.title, prefix)
            if not found:
                continue
            values = key_values(sub)
            for identifier in found:
                if define:
                    if identifier in self.defined:
                        self.error("E06", file, sub.line, f"{identifier} is defined more than once")
                        continue
                    self.defined[identifier] = (file, sub.line)
                blocks[identifier] = Record(identifier, {k: v[0] for k, v in values.items()}, file, sub.line,
                                            {k: v[1] for k, v in values.items()})
        return blocks

    def _required(self, record, key, name=None):
        value = record[key]
        if empty(value):
            self.error("E05", record.path, record.line, f"{record.id}: missing '{name or key.lower()}'")
            return None
        return value

    def _enum(self, record, key, allowed, name=None):
        value = self._required(record, key, name)
        if value is None:
            return None
        n = normalize(value).replace(" ", "_") if "_" in "".join(allowed) else normalize(value)
        if n not in allowed:
            self.error("E27", record.path, record.line, f"{record.id}: '{value}' is not a valid {name or key.lower()} ({' | '.join(allowed)})")
            return None
        return n

    def _section(self, file, key, name, na_allowed: bool, why: str = "", level=None):
        doc = self.docs.get(file)
        if doc is None:
            return None, False
        section = doc.find(key, level=level)
        if section is None:
            self.error("E02", file, 1, f"missing section '{name}'")
            return None, False
        reason = doc.not_applicable(section)
        if reason is not None:
            if "<FILL" in reason:
                self.error("E05", file, section.line, f"'{name}' still has a template placeholder in its N/A rationale")
            elif not na_allowed:
                self.error("E03", file, section.line, f"'{name}' cannot be N/A: {why}")
            elif len(reason) < 10:
                self.error("E11", file, section.line, f"'{name}' is N/A without a sufficient rationale")
            return section, True
        return section, False

    # -- entry --------------------------------------------------------------------------------

    def validate(self) -> Result:
        if not self.path.is_dir():
            self.error("E01", str(self.path), 0, "the package does not exist")
            return self.r
        for name in FILES:
            file = self.path / name
            if not file.exists():
                self.error("E01", name, 0, "missing package file")
                continue
            self.docs[name] = Document(name, file.read_text(encoding="utf-8"))
        if "spec.md" in self.docs:
            self._spec()
            self._security()
            self._test_cases()
            self._gate()
            self._traceability()
            self._references()
            self._text_checks()
        return self._close()

    # -- spec.md ------------------------------------------------------------------------------

    def _spec(self):
        doc = self.docs["spec.md"]
        meta = key_values(doc.sections[0]) if doc.sections else {}
        declared = None
        for key, (value, line) in meta.items():
            if "PROFILE" in key:
                declared = normalize(value)
                if declared not in PROFILES:
                    self.error("E27", "spec.md", line, f"security profile '{value}' is invalid ({' | '.join(PROFILES)})")
                    declared = None
            elif key == "STATUS":
                status = normalize(value).replace(" ", "_")
                if status not in SPEC_STATUSES:
                    self.error("E27", "spec.md", line, f"spec status '{value}' is invalid ({' | '.join(SPEC_STATUSES)})")
                else:
                    self.r.spec_status = status
        if not any("PROFILE" in k for k in meta):
            self.error("E05", "spec.md", 1, "the header does not declare the 'Security profile'")

        requirements = doc.find("REQUIREMENTS", level=2)
        design = doc.find("DESIGN", level=2)
        tasks = doc.find("TASKS", level=2)
        for section, name in ((requirements, "1. Requirements"), (design, "2. Design"), (tasks, "3. Tasks")):
            if section is None:
                self.error("E02", "spec.md", 1, f"missing section '{name}'")

        triggers = doc.find("SECURITY TRIGGERS")
        if triggers is None:
            self.error("E02", "spec.md", 1, "missing section 'Security triggers'")
        else:
            table = doc.table(triggers, "TRIGGER", "APPLIES", "RATIONALE")
            if table is None:
                self.error("E04", "spec.md", triggers.line, "'Security triggers' needs the table Trigger | Applies | Rationale")
            else:
                for key, text in TRIGGERS:
                    row = next((r for r in table.rows if text in normalize(r.get(table, "TRIGGER"))), None)
                    if row is None:
                        self.error("E04", "spec.md", table.line, f"missing trigger '{text.lower()}'")
                        continue
                    applies = normalize(row.get(table, "APPLIES"))
                    if applies not in ("YES", "Y", "SI", "NO", "N"):
                        self.error("E27", "spec.md", row.line, f"trigger '{text.lower()}': Applies must be YES or NO")
                    if empty(row.get(table, "RATIONALE")):
                        self.error("E05", "spec.md", row.line, f"trigger '{text.lower()}' has no rationale")
                    self.triggers[key] = is_yes(applies)

        minimum = "LOW"
        if any(self.on(k) for k in MEDIUM_TRIGGERS):
            minimum = "MEDIUM"
        if any(self.on(k) for k in HIGH_TRIGGERS):
            minimum = "HIGH"
        self.profile = declared or minimum
        if declared and PROFILES.index(declared) < PROFILES.index(minimum):
            self.error("E24", "spec.md", 1, f"declared profile {declared} is below the minimum {minimum} the triggers require")
        self.r.profile = self.profile

        story = doc.find("USER STORY", within=requirements) if requirements is not None else None
        if story is None or not doc.prose(story, tree=True).strip() or "<FILL" in normalize(doc.prose(story, tree=True)):
            self.error("E02", "spec.md", story.line if story else 1, "the requirements need a 'User story' section with the story as written on the board")
        if doc.find("PROBLEM") is None or not doc.prose(doc.find("PROBLEM"), tree=True).strip():
            self.error("E02", "spec.md", 1, "the requirements need a 'Problem and outcome' section with content")
        self._affected_paths(doc)

        self.uc = self._records("spec.md", doc.find("USE CASES"), ("ID", "ACTOR", "USE CASE"), "UC")
        if doc.find("USE CASES") is None:
            self.error("E02", "spec.md", 1, "missing section 'Use cases'")

        section, na = self._section("spec.md", "ABUSE CASES", "Abuse cases", self.profile == "LOW", "the profile requires abuse cases")
        if section and not na:
            self.ab = self._records("spec.md", section, ("ID", "ABUSE CASE", "THREAT", "EXPECTED RESPONSE", "TEST"), "AB")
            for record in self.ab.values():
                self._required(record, "ABUSE CASE")
                self._required(record, "EXPECTED RESPONSE", "expected response")
                if not ids(record["THREAT"], "THR"):
                    self.error("E05", "spec.md", record.line, f"{record.id}: must cite the threat (THR) it materializes")
                if not ids(record["TEST"], "TC"):
                    self.error("E10", "spec.md", record.line, f"{record.id}: the abuse case has no test case")

        criteria = doc.find("ACCEPTANCE CRITERIA")
        if criteria is None:
            self.error("E02", "spec.md", 1, "missing section 'Acceptance criteria'")
        self.ac = self._records("spec.md", criteria, ("ID", "CRITERION", "SOURCE"), "AC")
        for record in self.ac.values():
            self._required(record, "CRITERION")
            source = normalize(record["SOURCE"])
            if source == "STATED":
                continue
            if source.startswith("DERIVED"):
                if not _DERIVED.match(source):
                    self.error("E11", "spec.md", record.line, f"{record.id} is DERIVED without saying why the feature needs it")
            elif not empty(record["SOURCE"]):
                self.error("E27", "spec.md", record.line, f"{record.id}: source '{record['SOURCE']}' is invalid (STATED | DERIVED: <why>)")
            else:
                self.error("E05", "spec.md", record.line, f"{record.id}: missing 'source'")
        if self.ac and not any(normalize(r["SOURCE"]) == "STATED" for r in self.ac.values()):
            self.error("E05", "spec.md", criteria.line, "no acceptance criterion comes from the story (Source: STATED)")

        section, self.qr_na = self._section("spec.md", "QUALITY REQUIREMENTS", "Quality requirements", True)
        if section and not self.qr_na:
            self.qr = self._records("spec.md", section, ("ID", "CATEGORY", "REQUIREMENT", "TARGET"), "QR")
            for record in self.qr.values():
                self._required(record, "REQUIREMENT")
                self._required(record, "TARGET", "target and conditions")
                record.category = self._enum(record, "CATEGORY", QUALITY_CATEGORIES)

        section = doc.find("SECURITY REQUIREMENTS")
        if section is None:
            self.error("E02", "spec.md", 1, "missing section 'Security requirements'")
        self.sr = self._records("spec.md", section, ("ID", "REQUIREMENT", "SOURCE", "CONTROLS", "PRIORITY"), "SR", required=self.profile != "LOW")
        for record in self.sr.values():
            self._required(record, "REQUIREMENT")
            self._enum(record, "PRIORITY", ("HIGH", "MEDIUM", "LOW"))
            if not ids(record["SOURCE"], "DATA", "THR", "RISK"):
                self.error("E05", "spec.md", record.line, f"{record.id}: the source must cite a DATA, THR or RISK")
        if self.profile != "LOW" and not self.sr:
            self.error("E04", "spec.md", section.line if section else 1, f"a {self.profile} profile needs security requirements")

        if design is not None:
            for key, name in (("COMPONENTS", "Components"), ("SECURITY DESIGN", "Security design decisions")):
                sub = doc.find(key, within=design)
                if sub is None:
                    self.error("E02", "spec.md", design.line, f"missing section '{name}' in Design")
                elif not doc.text(sub, tree=True).strip():
                    self.error("E03", "spec.md", sub.line, f"'{name}' is empty")
            decisions = doc.find("SECURITY DESIGN", within=design)
            if decisions is not None and self.profile != "LOW" and not ids(doc.text(decisions, tree=True), "CTL", "CRY"):
                self.error("E05", "spec.md", decisions.line, "security design decisions must cite the controls (CTL) or mechanisms (CRY) they implement")
            adrs = doc.find("ARCHITECTURE DECISIONS", within=design)
            if adrs is not None:
                self._evidence_in_repo(Record("ADR", {}, "spec.md", adrs.line), doc.text(adrs, tree=True))

        self.t = self._records("spec.md", tasks, ("ID", "TASK", "TRACES", "CONTROLS", "STATUS", "EVIDENCE"), "T")
        for task in self.t.values():
            self._required(task, "TASK")
            status = self._enum(task, "STATUS", ("TODO", "IN_PROGRESS", "DONE"))
            if status == "DONE":
                if empty(task["EVIDENCE"]):
                    self.error("E28", "spec.md", task.line, f"{task.id} is DONE without evidence")
                self._evidence_in_repo(task, task["EVIDENCE"])
            elif status:
                if ids(task["TRACES"], "AC"):
                    self.reason("IN_PROGRESS", f"{task.id} (functional) is still {status}")
                else:
                    self.reason("IMPLEMENTED", f"{task.id} (security) is still {status}")

    def _affected_paths(self, doc):
        section = doc.find("AFFECTED PATHS")
        if section is None:
            self.error("E02", "spec.md", 1, "missing section 'Affected paths'")
            return
        table = doc.table(section, "PATH")
        if table is None:
            if doc.not_applicable(section) is None:
                self.error("E04", "spec.md", section.line, "'Affected paths' needs a table with a Path column")
            return
        critical = critical_paths.load_critical_paths(self.root, self.config["criticalPathsFile"])
        touched = []
        for row in table.rows:
            path = row.get(table, "PATH").strip("`")
            if empty(path):
                continue
            touched += [(c, row.line) for c in critical if critical_paths.overlap(c.pattern, path)]
        if touched and not self.on("CRITICAL_PATHS"):
            self.error("E24", "spec.md", touched[0][1], f"'{touched[0][0].pattern}' is a critical path; the critical paths trigger must be YES")
        for path, line in touched:
            minimum = path.minimum_profile if path.minimum_profile in PROFILES else "HIGH"
            if PROFILES.index(self.profile) < PROFILES.index(minimum):
                self.error("E24", "spec.md", line, f"'{path.pattern}' requires profile {minimum} or higher")

    # -- security.md --------------------------------------------------------------------------

    def _security(self):
        doc = self.docs.get("security.md")
        if doc is None:
            return
        low = self.profile == "LOW"

        section, na = self._section("security.md", "DATA INVENTORY", "Data inventory and classification", low, "the profile requires a data inventory", level=2)
        if section and not na:
            self.data = self._records("security.md", section, ("ID", "DATA", "CLASSIFICATION", "PERSONAL", "SENSITIVE", "PURPOSE"), "DATA")
        self._inventory()

        protected = [d for d in self.data.values() if self._level(d) >= 2]
        section, na = self._section("security.md", "DATA LIFECYCLE", "Data lifecycle", not protected, "there is confidential or restricted data", level=2)
        if section and not na:
            self.lifecycle = self._blocks("security.md", section, "DATA", define=False)
        for record in protected:
            self._lifecycle(record)

        for key, name in (("ACTORS", "Actors and roles"), ("TRUST BOUNDARIES", "Trust boundaries"),
                          ("DATA FLOWS", "Data flows"), ("ATTACK SURFACE", "Attack surface")):
            section, na = self._section("security.md", key, name, low, f"the {self.profile} profile requires it", level=2)
            if section and not na and not (doc.has_tables(section) or doc.prose(section, tree=True).strip()):
                self.error("E03", "security.md", section.line, f"'{name}' is empty")

        section, na = self._section("security.md", "THIRD-PARTY", "Third-party services", not self.on("INTEGRATIONS"), "the third-party trigger is YES", level=2)
        if section and not na and doc.table(section, "SERVICE", "DATA") is None:
            self.error("E04", "security.md", section.line, "'Third-party services' needs the table Service | Use | Data shared | Location | Controls")

        required = any(self.on(k) for k in THREAT_MODEL_TRIGGERS)
        section, na = self._section("security.md", "THREAT MODEL", "Threat model", not required,
                                    "the change touches sensitive data, authentication, authorization, payments, integrations, infrastructure or critical paths", level=2)
        if section and not na:
            self.thr = self._records("security.md", section, ("ID", "STRIDE", "ASSET", "THREAT", "LIKELIHOOD", "IMPACT", "RISK", "CONTROLS"), "THR")

        section, _ = self._section("security.md", "CONTROLS", "Controls", False, "every package declares its controls", level=2)
        if section:
            self.ctl = self._records("security.md", section, ("ID", "CONTROL", "DOMAIN", "STATUS", "MITIGATES", "TESTS", "TASKS", "RATIONALE"), "CTL")

        section, na = self._section("security.md", "CRYPTOGRAPHY", "Cryptography", low, f"the {self.profile} profile requires analysis of encryption in transit and at rest", level=2)
        if section and not na:
            self.cry = self._blocks("security.md", section, "CRY")
            if not self.cry:
                self.error("E04", "security.md", section.line, "'Cryptography' needs at least one ### CRY-NN block")

        needs_secrets = any(self.on(k) for k in ("AUTHENTICATION", "INTEGRATIONS", "INFRASTRUCTURE", "PAYMENTS"))
        section, na = self._section("security.md", "SECRETS", "Secrets and keys", not needs_secrets, "there is authentication, integrations, payments or infrastructure", level=2)
        if section and not na:
            self._secrets_table(doc, section)

        needs_auth = self.on("AUTHENTICATION") or self.on("AUTHORIZATION")
        section, na = self._section("security.md", "AUTHENTICATION", "Authentication, authorization and sessions", not needs_auth, "the authentication or authorization trigger is YES", level=2)
        if section and not na:
            self._checklist("security.md", section, AUTH_CHECKS, "authentication and sessions", needs_test=False)

        section, na = self._section("security.md", "MULTI-TENANCY", "Data isolation and multi-tenancy", not self.on("MULTI_TENANT"), "the multi-tenant trigger is YES", level=2)
        if section and not na:
            self._checklist("security.md", section, TENANCY_CHECKS, "multi-tenant isolation", needs_test=True)

        section, na = self._section("security.md", "DEPENDENCIES", "Dependencies", low and not self.on("DEPENDENCIES"), "there are new dependencies or the profile is above LOW", level=2)
        if section and not na:
            self.dep = self._records("security.md", section, ("ID", "DEPENDENCY", "VERSION", "CRITICALITY", "EVALUATION", "RESULT", "STATUS"), "DEP")

        section, na = self._section("security.md", "RISK REGISTER", "Risk register and residual risk", low, f"the {self.profile} profile requires a risk register", level=2)
        if section and not na:
            self.risk = self._records("security.md", section, ("ID", "RISK", "THREATS", "LIKELIHOOD", "IMPACT", "LEVEL", "TREATMENT", "RESIDUAL", "STATUS"), "RISK")

        section, na = self._section("security.md", "PENDING DECISIONS", "Pending decisions", True, level=2)
        if section and not na:
            self.dec = self._records("security.md", section, ("ID", "DECISION", "RECOMMENDATION", "DECIDER", "BLOCKS", "STATUS"), "DEC", required=False)

    @staticmethod
    def _level(record) -> int:
        n = normalize(record["CLASSIFICATION"])
        return CLASSIFICATIONS.index(n) if n in CLASSIFICATIONS else 0

    def _inventory(self):
        personal = sensitive = False
        for record in self.data.values():
            self._required(record, "DATA")
            self._required(record, "PURPOSE")
            level = self._enum(record, "CLASSIFICATION", CLASSIFICATIONS, "classification")
            is_personal, is_sensitive = is_yes(record["PERSONAL"]), is_yes(record["SENSITIVE"])
            personal |= is_personal
            sensitive |= is_sensitive
            if level and is_personal and CLASSIFICATIONS.index(level) < 2:
                self.error("E14", record.path, record.line, f"{record.id} is personal data and cannot be classified below CONFIDENTIAL")
            if level and is_sensitive and level != "RESTRICTED":
                self.error("E14", record.path, record.line, f"{record.id} is sensitive data and must be RESTRICTED")
        if self.data:
            if personal != self.on("PERSONAL_DATA"):
                self.error("E24", "spec.md", 1, "the personal data trigger does not match the data inventory")
            if sensitive and not self.on("SENSITIVE_DATA"):
                self.error("E24", "spec.md", 1, "the inventory has sensitive data but the sensitive data trigger is NO")

    def _lifecycle(self, record):
        block = self.lifecycle.get(record.id)
        if block is None:
            self.error("E14", record.path, record.line, f"{record.id} is {normalize(record['CLASSIFICATION'])} and has no documented lifecycle")
            return
        for key, name in LIFECYCLE:
            value = next((v for k, v in block.fields.items() if key in k), None)
            line = next((l for k, l in block.lines.items() if key in k), block.line)
            if value is None or empty(value):
                self.error("E14", block.path, line, f"{record.id}: lifecycle is missing '{name}'")
            elif unknown(value):
                self.reason("IMPLEMENTED", f"{record.id}: '{name}' is unknown")

    def _secrets_table(self, doc, section):
        table = doc.table(section, "SECRET", "LOCATION", "ACCESS", "ROTATION", "REVOCATION", "LEAK")
        if table is None:
            self.error("E04", "security.md", section.line, "'Secrets and keys' needs the table Secret | Location | Access | Environments | Rotation | Revocation | Leak detection")
            return
        for row in table.rows:
            name = row.get(table, "SECRET")
            for column in table.columns[1:]:
                value = row.cells.get(column, "")
                if empty(value):
                    self.error("E05", "security.md", row.line, f"secret '{name}': missing '{column.lower()}'")
                elif unknown(value):
                    self.reason("IMPLEMENTED", f"secret '{name}': '{column.lower()}' is unknown")

    def _checklist(self, file, section, checks, name, needs_test):
        doc = self.docs[file]
        table = doc.table(section, "CHECK", "APPLIES", "CONTROLS")
        if table is None:
            self.error("E04", file, section.line, f"the {name} checklist needs the table Check | Applies | Controls | Tests | Rationale")
            return
        for check in checks:
            row = next((r for r in table.rows if check in normalize(r.get(table, "CHECK"))), None)
            if row is None:
                self.error("E04", file, table.line, f"missing check '{check.lower()}' in {name}")
                continue
            self.checklists.append((table, row, check, needs_test, file))

    # -- test-cases.md -------------------------------------------------------------------------

    def _test_cases(self):
        doc = self.docs.get("test-cases.md")
        if doc is None:
            return
        section = doc.find("TEST CASES", level=2)
        if section is None:
            self.error("E02", "test-cases.md", 1, "missing section 'Test cases'")
        else:
            self.tc = self._blocks("test-cases.md", section, "TC")
        for record in self.tc.values():
            self._test_case(record)
        self._scenarios(doc)

        section, na = self._section("test-cases.md", "SECURITY TEST COVERAGE", "Security test coverage", self.profile == "LOW", "the profile requires reviewing every category")
        if section and not na:
            table = doc.table(section, "CATEGORY", "APPLIES", "TEST CASES")
            if table is None:
                self.error("E04", "test-cases.md", section.line, "coverage needs the table Category | Applies | Test cases | Rationale")
            else:
                for category in TEST_CATEGORIES:
                    row = next((r for r in table.rows if category in normalize(r.get(table, "CATEGORY"))), None)
                    if row is None:
                        self.error("E04", "test-cases.md", table.line, f"missing category '{category.lower()}' in the coverage")
                    else:
                        self.coverage.append((table, row, category))

    def _scenarios(self, doc):
        low = self.profile == "LOW"
        why = "the profile requires deriving scenarios from the story"
        section, na = self._section("test-cases.md", "SCENARIOS", "Scenarios", low, why, level=2)
        if section and not na:
            self.sc = self._records("test-cases.md", section, ("ID", "FROM", "SCENARIO", "DISPOSITION"), "SC")
        for record in self.sc.values():
            self._required(record, "SCENARIO")
            if not ids(record["FROM"], "UC", "AC"):
                self.error("E05", record.path, record.line, f"{record.id}: must cite the use case (UC) or acceptance criterion (AC) it comes from")
            if not ids(record["DISPOSITION"], "TC") and not _OUT_OF_SCOPE.match(normalize(record["DISPOSITION"])):
                self.error("E37", record.path, record.line, f"{record.id}: the disposition must be a test case (TC-NN) "
                           "or 'OUT OF SCOPE: <why>'")
        if self.sc:
            for uc in self.uc.values():
                if not any(uc.id in ids(s["FROM"], "UC") for s in self.sc.values()):
                    self.error("E37", "spec.md", uc.line, f"{uc.id} has no scenario in test-cases.md")

        section, na = self._section("test-cases.md", "SCENARIO COVERAGE", "Scenario coverage", low, why, level=2)
        if section is None or na:
            return
        table = doc.table(section, "KIND", "APPLIES", "SCENARIOS")
        if table is None:
            self.error("E04", "test-cases.md", section.line, "'Scenario coverage' needs the table Kind | Applies | Scenarios | Rationale")
            return
        required = {kind for trigger, kinds in SCENARIO_KINDS_FOR_TRIGGER.items() if self.on(trigger) for kind in kinds}
        for kind in SCENARIO_KINDS:
            row = next((r for r in table.rows if kind in normalize(r.get(table, "KIND"))), None)
            if row is None:
                self.error("E04", "test-cases.md", table.line, f"missing kind '{kind.lower()}' in the scenario coverage")
                continue
            applies = normalize(row.get(table, "APPLIES"))
            if is_yes(applies):
                if not [s for s in ids(row.get(table, "SCENARIOS"), "SC") if s in self.sc]:
                    self.error("E37", "test-cases.md", row.line, f"scenario kind '{kind.lower()}' applies and cites no scenarios")
            elif applies in ("NO", "N"):
                if kind in required:
                    self.error("E37", "test-cases.md", row.line, f"scenario kind '{kind.lower()}' is required by the security triggers")
                if empty(row.get(table, "RATIONALE")):
                    self.error("E11", "test-cases.md", row.line, f"scenario kind '{kind.lower()}' is NO without a rationale")
            else:
                self.error("E27", "test-cases.md", row.line, f"scenario kind '{kind.lower()}': Applies must be YES or NO")

    def _test_case(self, record):
        for key in TEST_FIELDS:
            if empty(record[key]):
                self.error("E18", record.path, record.line, f"{record.id}: missing '{key.lower()}'")
        kind = normalize(record["KIND"])
        if kind and kind not in TEST_KINDS:
            self.error("E27", record.path, record.line, f"{record.id}: kind '{record['KIND']}' is invalid ({' | '.join(TEST_KINDS)})")
        record.kind = kind
        level = normalize(record["LEVEL"])
        if level and level not in TEST_LEVELS:
            self.error("E27", record.path, record.line, f"{record.id}: level '{record['LEVEL']}' is invalid ({' | '.join(TEST_LEVELS)})")
        record.level = level
        if not ids(record["COVERS"], "AC", "QR", "SR"):
            self.error("E18", record.path, record.line, f"{record.id}: must cite the acceptance criteria (AC), quality requirements (QR) or security requirements (SR) it covers")
        if kind == "SECURITY" and not ids(record["RISK COVERED"], "THR", "RISK"):
            self.error("E18", record.path, record.line, f"{record.id}: a security test must cite the threat (THR) or risk (RISK) it covers")
        automation = normalize(record["AUTOMATION"])
        if automation and automation not in ("AUTOMATED", "MANUAL"):
            self.error("E27", record.path, record.line, f"{record.id}: automation '{record['AUTOMATION']}' is invalid (AUTOMATED | MANUAL)")
        if automation == "MANUAL" and len(re.findall(r"(?:^|\s|<br>)\d+[.)]\s", record["PROCEDURE"])) < 2:
            self.error("E18", record.path, record.line, f"{record.id}: a manual test needs reproducible numbered steps")
        if "PRODUCTION" in normalize(record["ENVIRONMENT"]) and empty(record["AUTHORIZATION"]):
            self.error("E29", record.path, record.line, f"{record.id}: a test against production needs the recorded authorization")
        status = normalize(record["STATUS"]).replace(" ", "_")
        record.status = status
        if status not in ("PENDING", "PASS", "FAIL", "BLOCKED", "N/A"):
            if status:
                self.error("E27", record.path, record.line, f"{record.id}: status '{record['STATUS']}' is invalid (PENDING | PASS | FAIL | BLOCKED | N/A)")
            return
        if status == "PASS":
            if empty(record["EVIDENCE"]) or normalize(record["EVIDENCE"]).startswith("PENDING"):
                self.error("E19", record.path, record.line, f"{record.id} is PASS without evidence")
            self._evidence_in_repo(record, record["TOOL"] + " " + record["EVIDENCE"])
        elif status == "FAIL":
            self.reason("BLOCKED" if kind == "SECURITY" else "IN_PROGRESS", f"{record.id} fails")
        elif status in ("PENDING", "BLOCKED"):
            self.reason("SECURITY_TESTS_PENDING" if kind == "SECURITY" else "IN_PROGRESS", f"{record.id} is {status}")
            self._evidence_in_repo(record, record["TOOL"], file_only=True)
        elif status == "N/A" and empty(record["EVIDENCE"]):
            self.error("E11", record.path, record.line, f"{record.id} is N/A without a rationale in Evidence")

    def _evidence_in_repo(self, record, text, file_only=False):
        for m in _EVIDENCE_PATH.finditer(text or ""):
            path, name = m.group(1), m.group(2) or m.group(3)
            if "://" in text[max(0, m.start() - 8):m.start()]:
                continue
            file = self.root / path
            if not file.exists():
                if file_only and name is None:
                    continue
                self.error("E20", record.path, record.line, f"{record.id}: the evidence cites '{path}', which does not exist in the repository")
                continue
            if name and not file_only:
                try:
                    content = file.read_text(encoding="utf-8")
                except (UnicodeDecodeError, OSError):
                    continue
                if (name if m.group(2) else name.split("[")[0]) not in content:
                    self.error("E20", record.path, record.line, f"{record.id}: '{name}' does not appear in {path}")

    # -- gate.md ------------------------------------------------------------------------------

    def _gate(self):
        doc = self.docs.get("gate.md")
        if doc is None:
            return
        meta = key_values(doc.sections[0]) if doc.sections else {}
        status = next(((v, l) for k, (v, l) in meta.items() if "STATUS" in k), None)
        if status is None or empty(status[0]):
            self.error("E05", "gate.md", 1, "the header does not declare the 'Security status'")
        else:
            declared = normalize(status[0]).replace(" ", "_")
            if declared not in GATE_STATES:
                self.error("E27", "gate.md", status[1], f"status '{status[0]}' is invalid ({' | '.join(GATE_STATES)})")
            else:
                self.r.declared = declared

        section = doc.find("SECURITY REVIEWS")
        table = doc.table(section, "REVIEWER", "ROLE", "DATE", "RESULT")
        if section is None or table is None:
            self.error("E04", "gate.md", section.line if section else 1, "'Security reviews' needs the table Reviewer | Role | Date | Scope | Result")
        else:
            for row in table.rows:
                reviewer = row.get(table, "REVIEWER")
                if empty(reviewer):
                    continue
                if is_ai(reviewer):
                    self.error("E26", "gate.md", row.line, f"the security review is signed by '{reviewer}'; a person must sign it, not an AI agent")
                    continue
                result = normalize(row.get(table, "RESULT"))
                if empty(row.get(table, "ROLE")) or not _DATE.search(row.get(table, "DATE")):
                    self.error("E05", "gate.md", row.line, f"the review by '{reviewer}' needs a role and a date (YYYY-MM-DD)")
                elif result not in ("APPROVED", "APPROVED WITH COMMENTS", "REJECTED"):
                    self.error("E27", "gate.md", row.line, "invalid review result (APPROVED | APPROVED WITH COMMENTS | REJECTED)")
                else:
                    self.reviews.append((normalize(reviewer), result))

        section = doc.find("RISK ACCEPTANCE")
        table = doc.table(section, "RISK", "APPROVED BY", "ROLE", "DATE")
        if section is None or table is None:
            self.error("E04", "gate.md", section.line if section else 1, "'Risk acceptance' needs the table Risk | Decision | Approved by | Role | Date | Expires")
        else:
            for row in table.rows:
                risks = ids(row.get(table, "RISK"), "RISK")
                if not risks:
                    continue
                approver = row.get(table, "APPROVED BY")
                valid = True
                if empty(approver) or is_ai(approver):
                    self.error("E22", "gate.md", row.line, f"{', '.join(risks)}: an authorized person must approve the acceptance, never an AI agent")
                    valid = False
                elif empty(row.get(table, "ROLE")) or not _DATE.search(row.get(table, "DATE")):
                    self.error("E22", "gate.md", row.line, f"{', '.join(risks)}: the acceptance needs the approver's role and date")
                    valid = False
                for risk in risks:
                    self.acceptances.append((risk, valid))

        section = doc.find("EVIDENCE")
        if section is None:
            self.error("E02", "gate.md", 1, "missing section 'Evidence'")
        else:
            self.ev = self._records("gate.md", section, ("ID", "EVIDENCE", "SUPPORTS", "LOCATION", "STATUS"), "EV", required=self.profile != "LOW")
            for record in self.ev.values():
                state = self._enum(record, "STATUS", ("PENDING", "AVAILABLE"))
                if not ids(record["SUPPORTS"]):
                    self.error("E05", "gate.md", record.line, f"{record.id}: must cite the requirement, control or test it supports")
                if state == "AVAILABLE":
                    if empty(record["LOCATION"]):
                        self.error("E19", "gate.md", record.line, f"{record.id} is AVAILABLE without a location")
                    else:
                        self._evidence_in_repo(record, record["LOCATION"])
                elif state == "PENDING":
                    self.reason("SECURITY_TESTS_PENDING", f"{record.id}: evidence pending")

        section = doc.find("CLOSEOUT")
        table = doc.table(section, "CRITERION", "RESULT")
        if table is not None:
            for row in table.rows:
                for criterion in ids(row.get(table, "CRITERION"), "AC", "QR"):
                    self.closeout[criterion] = (normalize(row.get(table, "RESULT")), row.get(table, "EVIDENCE"), row.line)

    # -- traceability -------------------------------------------------------------------------

    def _traceability(self):
        applicable = {i for i, c in self.ctl.items() if normalize(c["STATUS"]) != "NOT APPLICABLE"}

        for record in [*self.ac.values(), *self.qr.values()]:
            covering = [t for t in self.tc.values() if record.id in ids(t["COVERS"], "AC", "QR")]
            needed = QUALITY_LEVELS.get(getattr(record, "category", None))
            if not covering:
                self.error("E33", "spec.md", record.line, f"{record.id} has no test case")
            elif needed and not any(getattr(t, "level", "") in needed for t in covering):
                self.error("E36", "spec.md", record.line, f"{record.id} is {record.category} and needs a test case at level {' or '.join(needed)}")
        if (self.on("WEB") or self.on("MOBILE")) and not self.qr_na and not any(getattr(r, "category", "") == "ACCESSIBILITY" for r in self.qr.values()):
            self.warn("W10", "spec.md", 1, "the change touches a web or mobile interface and declares no ACCESSIBILITY quality requirement; add one or mark the section N/A with a rationale")

        for record in self.sr.values():
            if not [c for c in ids(record["CONTROLS"], "CTL") if c in applicable]:
                self.error("E08", "spec.md", record.line, f"{record.id} has no applicable control that mitigates it")
            if not any(record.id in ids(t["COVERS"], "SR") and getattr(t, "kind", "") == "SECURITY" for t in self.tc.values()):
                self.error("E09", "spec.md", record.line, f"{record.id} has no security test case")

        for record in self.ctl.values():
            self._required(record, "CONTROL")
            status = self._enum(record, "STATUS", ("EXISTING", "MISSING", "NOT APPLICABLE"))
            domain = normalize(record["DOMAIN"])
            if not domain or any(d.strip() not in DOMAINS for d in domain.split(",")):
                self.error("E27", record.path, record.line, f"{record.id}: domain '{record['DOMAIN']}' is invalid ({' | '.join(DOMAINS)})")
            if status == "NOT APPLICABLE":
                if empty(record["RATIONALE"]) or len(record["RATIONALE"]) < 10:
                    self.error("E11", record.path, record.line, f"{record.id} is NOT APPLICABLE without a rationale")
                continue
            if status is None:
                continue
            tests = [t for t in ids(record["TESTS"], "TC") if t in self.tc]
            if not [t for t in tests if getattr(self.tc[t], "status", "") != "N/A"]:
                self.error("E10", record.path, record.line, f"{record.id} is {status} and has no applicable test case")
            if status == "MISSING":
                tasks = [t for t in ids(record["TASKS"], "T") if t in self.t]
                if not tasks:
                    self.error("E12", record.path, record.line, f"{record.id} is MISSING and no task implements it")
                elif all(normalize(self.t[t]["STATUS"]) == "DONE" for t in tasks):
                    self.warn("W03", record.path, record.line, f"{record.id} is still MISSING although its tasks are DONE; update its status")
                self.reason("IMPLEMENTED", f"{record.id} is a required control that is missing")
            if not ids(record["MITIGATES"], "THR", "SR", "DATA", "RISK") and not any(record.id in ids(r["CONTROLS"]) for r in self.sr.values()):
                self.warn("W04", record.path, record.line, f"{record.id} is not linked to any threat or requirement")

        for trigger, domain in DOMAIN_FOR_TRIGGER.items():
            if self.on(trigger) and not any(domain in normalize(self.ctl[c]["DOMAIN"]) for c in applicable):
                self.error("E13", "security.md", 1, f"the {trigger.lower()} trigger is YES but there is no applicable {domain} control")

        for record in self.data.values():
            level = self._level(record)
            if level >= 2 and not any(record.id in ids(r["SOURCE"]) for r in self.sr.values()):
                self.error("E15", record.path, record.line, f"{record.id} is {CLASSIFICATIONS[level]} and no security requirement protects it")
            if level == 3 and not any(record.id in ids(c["PROTECTS"]) for c in self.cry.values()):
                self.error("E16", record.path, record.line, f"{record.id} is RESTRICTED and has no documented cryptographic mechanism")

        for record in self.thr.values():
            self._required(record, "THREAT")
            self._required(record, "ASSET")
            letters = re.sub(r"[^A-Z]", "", normalize(record["STRIDE"]))
            if not letters or set(letters) - set("STRIDE"):
                self.error("E27", record.path, record.line, f"{record.id}: STRIDE must use the letters S, T, R, I, D or E")
            risk = self._risk(record, "RISK")
            if risk and PROFILES.index(risk) >= 1 and not [c for c in ids(record["CONTROLS"], "CTL") if c in applicable]:
                self.error("E13", record.path, record.line, f"{record.id} has {risk} risk and no applicable control")

        for record in self.cry.values():
            self._cryptography(record)

        for record in self.dep.values():
            self._required(record, "DEPENDENCY")
            criticality = self._enum(record, "CRITICALITY", ("CRITICAL", "HIGH", "MEDIUM", "LOW"))
            status = self._enum(record, "STATUS", ("EVALUATED", "PENDING", "REJECTED"))
            if status == "EVALUATED":
                if empty(record["EVALUATION"]) or not _DATE.search(record["EVALUATION"]):
                    self.error("E21", record.path, record.line, f"{record.id} is EVALUATED without a method and date (YYYY-MM-DD)")
                if empty(record["RESULT"]):
                    self.error("E21", record.path, record.line, f"{record.id} is EVALUATED without a result")
            elif status == "PENDING":
                self.reason("IMPLEMENTED", f"{record.id} ({criticality or 'no criticality'}) has not been evaluated")
            elif status == "REJECTED":
                self.reason("BLOCKED", f"{record.id} was rejected and is still in use")

        accepted = {}
        for risk, valid in self.acceptances:
            accepted[risk] = accepted.get(risk, False) or valid
        for record in self.risk.values():
            self._required(record, "RISK")
            self._required(record, "RESIDUAL", "residual risk")
            level = self._risk(record, "LEVEL")
            treatment = self._enum(record, "TREATMENT", ("MITIGATE", "ACCEPT", "TRANSFER", "AVOID"))
            status = self._enum(record, "STATUS", ("OPEN", "MITIGATED", "ACCEPTED"))
            if not ids(record["THREATS"], "THR"):
                self.error("E05", record.path, record.line, f"{record.id}: must cite the threats (THR) behind it")
            if level is None or status is None:
                continue
            if status == "ACCEPTED":
                if treatment != "ACCEPT":
                    self.error("E27", record.path, record.line, f"{record.id} is ACCEPTED but its treatment is not ACCEPT")
                if not accepted.get(record.id):
                    self.error("E22", record.path, record.line, f"{record.id} is ACCEPTED without approval by an authorized person in gate.md")
                    self.reason("BLOCKED" if level == "CRITICAL" else "IMPLEMENTED", f"{record.id} ({level}) has no valid acceptance")
                elif level != "LOW":
                    self.reason("RISK_ACCEPTED", f"{record.id} ({level}) formally accepted")
            elif status == "OPEN":
                if level == "CRITICAL":
                    self.reason("BLOCKED", f"{record.id} is CRITICAL with no approved treatment")
                elif level in ("HIGH", "MEDIUM"):
                    self.reason("IMPLEMENTED", f"{record.id} ({level}) is still open")
            elif status == "MITIGATED":
                missing = sorted({c for t in ids(record["THREATS"], "THR") if t in self.thr
                                  for c in ids(self.thr[t]["CONTROLS"], "CTL")
                                  if c in self.ctl and normalize(self.ctl[c]["STATUS"]) == "MISSING"})
                if missing:
                    self.error("E30", record.path, record.line, f"{record.id} is MITIGATED but its controls {', '.join(missing)} are still MISSING")

        for record in self.dec.values():
            self._required(record, "DECISION")
            if is_ai(record["DECIDER"]):
                self.error("E22", record.path, record.line, f"{record.id}: a person must take the decision, not an AI agent")
            status = self._enum(record, "STATUS", ("PENDING", "APPROVED", "REJECTED"))
            if status == "PENDING" and is_yes(record["BLOCKS"]):
                self.reason("IMPLEMENTED", f"{record.id} is a pending decision that blocks the gate")

        for table, row, check, needs_test, file in self.checklists:
            applies = normalize(row.get(table, "APPLIES"))
            if applies not in ("YES", "Y", "SI", "NO", "N"):
                self.error("E27", file, row.line, f"'{check.lower()}': Applies must be YES or NO")
                continue
            if not is_yes(applies):
                if empty(row.get(table, "RATIONALE")):
                    self.error("E11", file, row.line, f"'{check.lower()}' is NO without a rationale")
                continue
            if not [c for c in ids(row.get(table, "CONTROLS"), "CTL") if c in applicable]:
                self.error("E08", file, row.line, f"'{check.lower()}' applies and cites no applicable control")
            if needs_test and not ids(row.get(table, "TESTS"), "TC"):
                self.error("E10", file, row.line, f"'{check.lower()}' applies and has no negative test")

        for table, row, category in self.coverage:
            applies = normalize(row.get(table, "APPLIES"))
            if category == "CROSS-TENANT" and self.on("MULTI_TENANT") and not is_yes(applies):
                self.error("E10", "test-cases.md", row.line, "the multi-tenant trigger is YES: negative cross-tenant tests are required")
            if is_yes(applies):
                if not ids(row.get(table, "TEST CASES"), "TC"):
                    self.error("E10", "test-cases.md", row.line, f"category '{category.lower()}' applies and cites no test cases")
            elif applies in ("NO", "N"):
                if empty(row.get(table, "RATIONALE")):
                    self.error("E11", "test-cases.md", row.line, f"category '{category.lower()}' is NO without a rationale")
            else:
                self.error("E27", "test-cases.md", row.line, f"category '{category.lower()}': Applies must be YES or NO")

    def _risk(self, record, level_key):
        likelihood = self._enum(record, "LIKELIHOOD", LIKELIHOODS)
        impact = self._enum(record, "IMPACT", IMPACTS)
        level = self._enum(record, level_key, PROFILES, level_key.lower())
        if likelihood and impact and level:
            expected = MATRIX[impact][likelihood]
            if PROFILES.index(level) < PROFILES.index(expected):
                self.error("E31", record.path, record.line, f"{record.id}: with {likelihood} likelihood and {impact} impact the level is at least {expected}, not {level}")
        return level

    def _cryptography(self, record):
        for key in CRYPTO_FIELDS:
            value = record[key]
            if empty(value):
                self.error("E16", record.path, record.line, f"{record.id}: missing '{key.lower()}'")
            elif unknown(value):
                self.reason("IMPLEMENTED", f"{record.id}: '{key.lower()}' is unknown")
        kind = normalize(record["TYPE"]).replace(" ", "_")
        algorithm = normalize(record["ALGORITHM"])
        if kind and kind not in CRYPTO_TYPES:
            self.error("E27", record.path, record.line, f"{record.id}: type '{record['TYPE']}' is invalid ({' | '.join(CRYPTO_TYPES)})")
        forbidden = (
            (r"\bMD5\b", "MD5"), (r"\bSHA-?1\b", "SHA-1"), (r"\b3?DES\b|TRIPLE ?DES", "DES/3DES"), (r"\bRC4\b", "RC4"),
            (r"\bECB\b", "ECB mode"), (r"\bSSL ?V?[23]|\bTLS ?1\.[01]\b", "SSL or TLS 1.0/1.1"),
            (r"\bCUSTOM\b|\bHOMEMADE\b|\bHOME-GROWN\b|\bPROPIO\b|\bXOR\b", "a custom algorithm"),
        )
        for pattern, name in forbidden:
            if re.search(pattern, algorithm) and not re.search(r"\bNO\b[^.]*" + pattern, algorithm):
                self.error("E17", record.path, record.line, f"{record.id}: uses {name}, which is not allowed")
        if kind == "PASSWORD_HASH":
            if not re.search(r"ARGON2|SCRYPT|BCRYPT|PBKDF2", algorithm):
                self.error("E17", record.path, record.line, f"{record.id}: passwords need a password hashing function (Argon2id, scrypt, bcrypt or PBKDF2), never reversible encryption or a fast hash")
            elif "ARGON2ID" not in algorithm:
                self.warn("W06", record.path, record.line, f"{record.id}: Argon2id is recommended for new implementations")
        if kind in ("APP_LEVEL", "AT_REST") and re.search(r"\bCBC\b", algorithm) and "HMAC" not in algorithm:
            self.error("E17", record.path, record.line, f"{record.id}: unauthenticated CBC; use authenticated encryption (AES-GCM, ChaCha20-Poly1305)")
        if kind == "APP_LEVEL" and not re.search(r"GCM|POLY1305|SIV|CCM|KMS|KEYSTORE|KEYCHAIN|TINK", algorithm):
            self.warn("W07", record.path, record.line, f"{record.id}: no authenticated encryption mode recognized")
        if kind == "SIGNATURE" and re.search(r"\bHS(256|384|512)\b|HMAC", algorithm):
            self.error("E17", record.path, record.line, f"{record.id}: HMAC/HS256 is a message authentication code, not a digital signature; declare type MAC")
        if kind == "MAC" and "HMAC" not in algorithm and not re.search(r"\bHS(256|384|512)\b|POLY1305|CMAC|GMAC", algorithm):
            self.error("E17", record.path, record.line, f"{record.id}: type MAC does not match the algorithm")
        if kind == "TLS" and not re.search(r"TLS ?1\.[23]", algorithm):
            self.warn("W08", record.path, record.line, f"{record.id}: state the minimum TLS version (1.2 or 1.3)")
        if not ids(record["TESTS"], "TC"):
            self.error("E10", record.path, record.line, f"{record.id}: the mechanism cites no test cases (TC)")

    # -- global checks ------------------------------------------------------------------------

    def _references(self):
        for name, doc in self.docs.items():
            for number, line in enumerate(doc.lines, start=1):
                for identifier in ids(line):
                    if identifier not in self.defined:
                        self.error("E07", name, number, f"{identifier} is cited but not defined in the package")

    def _text_checks(self):
        for name in FILES:
            file = self.path / name
            if not file.exists():
                continue
            text = file.read_text(encoding="utf-8")
            for finding in secrets.scan_text(text, name):
                self.error("E25", name, finding.line, f"possible secret ({finding.kind}, fingerprint {finding.fingerprint}); remove and rotate it")
                self.reason("BLOCKED", f"possible secret exposed in {name}:{finding.line}")
            for number, line in enumerate(text.splitlines(), start=1):
                n = normalize(line)
                for pattern in _COMPLIANCE_CLAIMS:
                    m = pattern.search(n)
                    if m and not _NEGATION.search(n[:m.start()]):
                        self.error("E32", name, number, "compliance or certification claim without evidence; describe controls and evidence, not conformity")
                for m in _EMAIL.finditer(line):
                    domain = m.group(1).lower()
                    if not domain.endswith(_RESERVED_DOMAINS) and not domain.startswith("example."):
                        self.warn("W01", name, number, f"possible real email (…@{domain}); use reserved domains such as example.com")
                if _PHONE.search(line):
                    self.warn("W02", name, number, "possible real phone number; use fictitious data")

    # -- closing ------------------------------------------------------------------------------

    def _close(self) -> Result:
        if self.r.errors:
            self.reason("IN_PROGRESS", f"the package has {len(self.r.errors)} validation errors")
        approved = {r for r, result in self.reviews if result in ("APPROVED", "APPROVED WITH COMMENTS")}
        if any(result == "REJECTED" for _, result in self.reviews):
            self.reason("IMPLEMENTED", "the security review was rejected")
        needed = 2 if self.profile == "CRITICAL" else 1
        if len(approved) < needed:
            self.reason("SECURITY_REVIEW_PENDING", f"{needed - len(approved)} approved human security review(s) missing")

        computed = "SECURITY_VERIFIED"
        for state, _ in self.r.reasons:
            if RANK[state] < RANK[computed]:
                computed = state
        self.r.computed = computed

        if self.r.spec_status == "DONE":
            for record in [*self.ac.values(), *self.qr.values()]:
                result, evidence, _ = self.closeout.get(record.id, ("", "", 0))
                if result != "MET":
                    self.error("E34", "gate.md", 1, f"the spec is DONE but {record.id} is not MET in the closeout")
                elif empty(evidence):
                    self.error("E34", "gate.md", 1, f"{record.id} is MET in the closeout without evidence")
            if computed not in ("SECURITY_VERIFIED", "RISK_ACCEPTED"):
                self.error("E35", "spec.md", 1, f"the spec is DONE but the security gate is {computed}")

        declared = self.r.declared
        if declared:
            if computed == "BLOCKED" and declared != "BLOCKED":
                self.error("E23", "gate.md", 1, f"declared status is {declared}, but blocking conditions exist: it must be BLOCKED")
            elif declared != "BLOCKED" and RANK[declared] > RANK[computed]:
                self.error("E23", "gate.md", 1, f"declared status {declared} exceeds what the evidence supports ({computed})")
            elif declared != computed:
                self.warn("W09", "gate.md", 1, f"declared status {declared} is more conservative than the computed one ({computed})")
        return self.r


def validate(package, config: Config = None) -> Result:
    return Validator(package, config).validate()
