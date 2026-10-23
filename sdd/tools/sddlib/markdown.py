import re
import unicodedata
from dataclasses import dataclass, field

_COMMENT = re.compile(r"<!--.*?-->", re.S)
_HEADING = re.compile(r"^(#{1,6})\s+(.*?)\s*#*\s*$")
_SEPARATOR = re.compile(r"^\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)*\|?\s*$")
_NOT_APPLICABLE = re.compile(r"^\W*N/?A\W*[:\-–—]\s*(.+)$|^\W*NOT APPLICABLE\W*[:\-–—]\s*(.+)$")


def normalize(text: str) -> str:
    decomposed = unicodedata.normalize("NFKD", text)
    plain = "".join(c for c in decomposed if not unicodedata.combining(c))
    plain = plain.replace("**", "").replace("`", "").replace("’", "'")
    return re.sub(r"\s+", " ", plain).strip().upper()


@dataclass
class Row:
    cells: dict
    line: int

    def get(self, table: "Table", key: str) -> str:
        name = table.column(key)
        return self.cells.get(name, "") if name else ""


@dataclass
class Table:
    columns: list
    rows: list
    line: int

    def column(self, key: str):
        key = normalize(key)
        for name in self.columns:
            if key in name:
                return name
        return None

    def has(self, key: str) -> bool:
        return self.column(key) is not None


@dataclass
class Section:
    level: int
    title: str
    line: int
    start: int
    end: int = 0
    tree_end: int = 0
    tables: list = field(default_factory=list)

    @property
    def key(self) -> str:
        return normalize(re.sub(r"^\s*\d+(\.\d+)*\.?\s*", "", self.title))


class Document:
    def __init__(self, path: str, text: str):
        self.path = path
        self.lines = _COMMENT.sub(lambda m: "\n" * m.group(0).count("\n"), text).splitlines()
        self.sections = self._sections()
        for section in self.sections:
            section.tables = self._tables(section.start, section.end)

    def _sections(self) -> list:
        sections, in_code = [], False
        for i, line in enumerate(self.lines):
            if line.lstrip().startswith("```"):
                in_code = not in_code
                continue
            m = None if in_code else _HEADING.match(line)
            if m:
                sections.append(Section(len(m.group(1)), m.group(2), i + 1, i + 1))
        for idx, section in enumerate(sections):
            section.end = sections[idx + 1].line - 1 if idx + 1 < len(sections) else len(self.lines)
            section.tree_end = len(self.lines)
            for later in sections[idx + 1:]:
                if later.level <= section.level:
                    section.tree_end = later.line - 1
                    break
        return sections

    def _tables(self, start: int, end: int) -> list:
        tables, i = [], start
        while i < end:
            line = self.lines[i].strip()
            if line.startswith("|") and i + 1 < end and _SEPARATOR.match(self.lines[i + 1].strip()):
                columns = [normalize(c) for c in _cells(line)]
                table = Table(columns, [], i + 1)
                i += 2
                while i < end and self.lines[i].strip().startswith("|"):
                    values = _cells(self.lines[i].strip())
                    values += [""] * (len(columns) - len(values))
                    table.rows.append(Row(dict(zip(columns, values)), i + 1))
                    i += 1
                tables.append(table)
            else:
                i += 1
        return tables

    def find(self, *keys: str, level: int = None, within: Section = None):
        wanted = [normalize(k) for k in keys]
        pool = self.children(within) if within else self.sections
        for section in pool:
            if level is not None and section.level != level:
                continue
            if all(k in section.key for k in wanted):
                return section
        return None

    def children(self, section: Section) -> list:
        return [s for s in self.sections if s.level > section.level and section.line < s.line <= section.tree_end]

    def table(self, section: Section, *columns: str, tree: bool = False):
        if section is None:
            return None
        pool = [section, *self.children(section)] if tree else [section]
        for candidate in pool:
            for table in candidate.tables:
                if all(table.has(c) for c in columns):
                    return table
        return None

    def text(self, section: Section, tree: bool = False) -> str:
        return "\n".join(self.lines[section.start:section.tree_end if tree else section.end])

    def prose(self, section: Section, tree: bool = False) -> str:
        lines = self.lines[section.start:section.tree_end if tree else section.end]
        return "\n".join(l for l in lines if l.strip() and not l.strip().startswith("|") and not _HEADING.match(l))

    def has_tables(self, section: Section) -> bool:
        return any(s.tables for s in [section, *self.children(section)])

    def not_applicable(self, section: Section):
        if self.has_tables(section):
            return None
        for line in self.prose(section, tree=True).splitlines():
            m = _NOT_APPLICABLE.match(normalize(line))
            if m:
                return (m.group(1) or m.group(2) or "").strip()
        return None


def _cells(line: str) -> list:
    content = line.strip()
    if content.startswith("|"):
        content = content[1:]
    if content.endswith("|") and not content.endswith("\\|"):
        content = content[:-1]
    return [p.strip().replace("\\|", "|") for p in re.split(r"(?<!\\)\|", content)]


def key_values(section: Section) -> dict:
    """Two-column table (Field | Value) as {normalized field: (value, line)}."""
    result = {}
    for table in section.tables:
        if len(table.columns) < 2:
            continue
        for row in table.rows:
            name = normalize(row.cells.get(table.columns[0], ""))
            if name:
                result[name] = (row.cells.get(table.columns[1], ""), row.line)
    return result
