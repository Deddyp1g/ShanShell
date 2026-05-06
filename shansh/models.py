"""ShanShell AI 数据模型定义。"""

from dataclasses import dataclass, field, asdict
from typing import Optional


@dataclass
class Candidate:
    cmd: str = ""
    ghost_text: str = ""
    explanation: str = ""
    confidence: float = 0.0
    source: str = ""
    risk: str = "low"

    def to_dict(self):
        return asdict(self)


@dataclass
class Diagnostic:
    start: int = 0
    end: int = 0
    severity: str = "info"
    message: str = ""

    def to_dict(self):
        return asdict(self)


@dataclass
class SuggestRequest:
    buffer: str = ""
    cursor: int = 0
    cwd: str = "/"
    shell: str = ""
    os_info: dict = field(default_factory=dict)
    files: list[str] = field(default_factory=list)
    last_commands: list[str] = field(default_factory=list)
    git_info: dict = field(default_factory=dict)

    def to_dict(self):
        return asdict(self)


@dataclass
class SuggestResponse:
    mode: str = "completion"
    replacement: str = ""
    ghost_text: str = ""
    explanation: str = ""
    confidence: float = 0.0
    risk: str = "low"
    source: str = ""
    candidates: list = field(default_factory=list)
    diagnostics: list = field(default_factory=list)

    def to_dict(self):
        d = asdict(self)
        d["candidates"] = [
            c.to_dict() if hasattr(c, "to_dict") else c for c in self.candidates
        ]
        d["diagnostics"] = [
            diag.to_dict() if hasattr(diag, "to_dict") else diag for diag in self.diagnostics
        ]
        return d
