"""ShanShell AI 渲染协议与 ANSI 渲染引擎。

提供三级渲染:
  Level 1: zle -M 纯文本
  Level 2: ANSI 颜色 + 下划线 + 诊断行
  Level 3: undercurl 扩展 (未来)
"""

import json
import sys
import os
from shansh.models import SuggestResponse


ANSI = {
    "gray": "\033[90m",
    "red": "\033[31m",
    "yellow": "\033[33m",
    "blue": "\033[34m",
    "underline": "\033[4m",
    "red_bg_white": "\033[41;97m",
    "reset": "\033[0m",
}

SEVERITY_COLORS = {
    "error": ANSI["red"],
    "warning": ANSI["yellow"],
    "info": ANSI["blue"],
}


def _supports_color() -> bool:
    if os.environ.get("NO_COLOR"):
        return False
    if os.environ.get("TERM", "") in ("dumb", ""):
        return False
    if not sys.stdout.isatty():
        return False
    if os.environ.get("SHANSH_NO_COLOR"):
        return False
    return True


def detect_render_level() -> int:
    if not _supports_color():
        return 1
    term = os.environ.get("TERM", "")
    if "256color" in term or "truecolor" in term or "kitty" in term:
        return 2
    if "xterm" in term or "screen" in term:
        return 2
    return 2


def _ansi(text: str, code: str) -> str:
    return f"{code}{text}{ANSI['reset']}"


def _build_diagnostic_line(buffer: str, diagnostics: list) -> str:
    if not diagnostics:
        return ""
    max_end = 0
    for d in diagnostics:
        if d.get("end", d.end if hasattr(d, "end") else 0) > max_end:
            max_end = d.get("end", d.end if hasattr(d, "end") else 0)
    max_end = max(max_end, len(buffer))
    marker = [" "] * max_end
    for d in diagnostics:
        start = d.get("start", d.start if hasattr(d, "start") else 0)
        end = d.get("end", d.end if hasattr(d, "end") else 0)
        sev = d.get("severity", d.severity if hasattr(d, "severity") else "warning")
        ch = "~" if sev == "info" else "^"
        for i in range(start, min(end, len(buffer))):
            marker[i] = ch
    return " " * 1 + "".join(marker)


class RenderEngine:
    def __init__(self, level: int = None):
        self.level = level if level is not None else detect_render_level()
        self.use_color = _supports_color() and self.level >= 2

    def render(self, buffer: str, response: SuggestResponse) -> dict:
        diag_line = ""
        diags = response.diagnostics if hasattr(response, "diagnostics") else []
        if diags:
            dlist = []
            for d in diags:
                if hasattr(d, "to_dict"):
                    dlist.append(d.to_dict())
                elif isinstance(d, dict):
                    dlist.append(d)
                else:
                    dlist.append({"start": getattr(d, "start", 0), "end": getattr(d, "end", 0), "severity": getattr(d, "severity", "info")})
            diag_line = _build_diagnostic_line(buffer, dlist)

        inline_message = self._build_inline(response, diag_line)
        ansi_preview = self._build_ansi_preview(buffer, response)

        return {
            "render_level": self.level,
            "inline_message": inline_message,
            "diagnostic_line": diag_line,
            "ansi_preview": ansi_preview,
        }

    def _build_inline(self, response: SuggestResponse, diag_line: str) -> str:
        repl = response.replacement or ""
        expl = response.explanation or ""
        mode = response.mode or ""

        parts = ["[ShanShell]"]

        if response.risk == "high":
            if self.use_color:
                parts.append(_ansi(" HIGH RISK ", ANSI["red_bg_white"]))
            else:
                parts.append(" HIGH RISK ")
        elif response.risk == "medium":
            if self.use_color:
                parts.append(_ansi(" MEDIUM RISK ", ANSI["yellow"]))
            else:
                parts.append(" MEDIUM RISK ")

        mode_labels = {"completion": "+", "correction": "*", "workflow": ">", "nl2cmd": "#"}
        prefix = mode_labels.get(mode, "→")

        parts.append(f" {prefix} {repl}")
        if expl:
            parts.append(f" | {expl}")

        msg = " ".join(parts)
        if diag_line:
            msg += "\n" + diag_line

        return msg

    def _build_ansi_preview(self, buffer: str, response: SuggestResponse) -> str:
        if not self.use_color:
            return f"→ {response.replacement}"

        diags = response.diagnostics if hasattr(response, "diagnostics") else []
        dlist = []
        for d in diags:
            if hasattr(d, "to_dict"):
                dlist.append(d.to_dict())
            elif isinstance(d, dict):
                dlist.append(d)
            else:
                dlist.append({"start": getattr(d, "start", 0), "end": getattr(d, "end", 0), "severity": getattr(d, "severity", "info")})

        error_ranges = []
        for d in dlist:
            sev = d.get("severity", "info")
            color = SEVERITY_COLORS.get(sev, ANSI["blue"])
            error_ranges.append((d["start"], d["end"], color))

        error_ranges.sort(key=lambda x: x[0])

        chars = list(buffer)
        pos_color = {}
        for start, end, color in error_ranges:
            for i in range(start, min(end, len(chars))):
                pos_color[i] = color

        buf_colored = ""
        i = 0
        while i < len(chars):
            if i in pos_color:
                color = pos_color[i]
                start = i
                while i < len(chars) and i in pos_color and pos_color[i] == color:
                    i += 1
                segment = "".join(chars[start:i])
                buf_colored += _ansi(segment, color) + _ansi("", ANSI["underline"])
            else:
                buf_colored += chars[i]
                i += 1

        ghost = response.ghost_text or ""
        ghost_part = _ansi(ghost, ANSI["gray"]) if ghost else ""

        return f"{buf_colored}{ghost_part}  →  {response.replacement}"


REQUEST_SCHEMA = {
    "type": "object",
    "required": ["type", "input"],
    "properties": {
        "type": {"enum": ["complete", "correct", "predict", "nl2cmd", "risk_check", "shutdown"]},
        "input": {"type": "string"},
        "cwd": {"type": "string"},
        "history": {"type": "array", "items": {"type": "string"}},
    }
}

RESPONSE_SCHEMA = {
    "type": "object",
    "required": ["type"],
    "properties": {
        "type": {"enum": ["complete", "correct", "predict", "nl2cmd", "risk_check", "shutdown"]},
        "suggestions": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "text": {"type": "string"},
                    "score": {"type": "number"},
                    "source": {"enum": ["rules", "llm", "history", "distro"]},
                    "description": {"type": "string"},
                }
            }
        },
        "error": {"type": "string"},
    }
}


def read_request():
    line = sys.stdin.readline()
    if not line:
        return None
    return json.loads(line)


def write_response(response: dict):
    sys.stdout.write(json.dumps(response, ensure_ascii=False) + "\n")
    sys.stdout.flush()
