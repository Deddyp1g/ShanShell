"""ShanShell AI 命令纠错引擎。"""

from shansh.models import Candidate, Diagnostic


class CorrectionEngine:
    _typo_map = {
        "gti": "git",
        "igt": "git",
        "gitt": "git",
        "pyhton": "python",
        "dcoker": "docker",
        "statsu": "status",
        "stattus": "status",
        "mkidr": "mkdir",
        "mkdr": "mkdir",
        "ehco": "echo",
        "grpe": "grep",
        "hsitory": "history",
    }

    _apt_to_dnf = {
        "apt install": "sudo dnf install",
        "apt remove": "sudo dnf remove",
        "apt update": "sudo dnf check-update",
        "apt upgrade": "sudo dnf upgrade",
        "apt search": "dnf search",
        "apt-get install": "sudo dnf install",
    }

    _package_completions = {
        "nginx": "nginx",
        "ng": "nginx",
        "httpd": "httpd",
        "apache": "httpd",
        "mariadb": "mariadb",
    }

    _nl_patterns = {
        "查看磁盘空间": "df -h",
        "查看内存": "free -h",
        "查看内存使用": "free -h",
        "解压": None,
    }

    _flag_corrections = {
        "-z": "-l",
    }

    def correct(self, buffer: str, context: dict = None) -> dict:
        trimmed = buffer.strip()
        if not trimmed:
            return {"candidates": [], "diagnostics": [], "replacement": ""}

        candidates = []
        diagnostics = []

        nl_result = self._try_nl2cmd_short(trimmed, context)
        if nl_result:
            return nl_result

        apt_result = self._try_apt_to_dnf(trimmed)
        if apt_result:
            return apt_result

        tar_result = self._try_tar(trimmed)
        if tar_result:
            return tar_result

        flag_result = self._try_flag_correction(trimmed)
        if flag_result:
            return flag_result

        parts = trimmed.split()
        corrected_parts = []
        has_correction = False

        for i, part in enumerate(parts):
            if part in self._typo_map:
                corrected = self._typo_map[part]
                corrected_parts.append(corrected)
                start = len(" ".join(parts[:i])) + (1 if i > 0 else 0)
                end = start + len(part)
                diagnostics.append(Diagnostic(
                    start=start, end=end, severity="warning",
                    message=f"'{part}' 应为 '{corrected}'"
                ))
                has_correction = True
            else:
                corrected_parts.append(part)

        if has_correction:
            replacement = " ".join(corrected_parts)
            candidates.append(Candidate(
                cmd=replacement,
                ghost_text="",
                explanation=f"自动纠错: {trimmed} → {replacement}",
                confidence=0.85,
                source="rules"
            ))

        return {
            "candidates": candidates,
            "diagnostics": diagnostics,
            "replacement": candidates[0].cmd if candidates else "",
        }

    def _try_nl2cmd_short(self, buffer: str, context: dict = None) -> dict:
        if buffer in ("查看磁盘空间", "查看内存", "查看内存使用"):
            cmd = self._nl_patterns.get(buffer, "")
            if cmd:
                return {
                    "candidates": [Candidate(
                        cmd=cmd, ghost_text="", explanation=f"自然语言: {buffer} → {cmd}",
                        confidence=0.90, source="nl2cmd"
                    )],
                    "diagnostics": [Diagnostic(
                        start=0, end=len(buffer), severity="info",
                        message=f"转换为命令: {cmd}"
                    )],
                    "replacement": cmd,
                }
        if buffer.startswith("解压 ") and buffer.endswith(".tar.gz"):
            filename = buffer[3:]
            cmd = f"tar -zxvf {filename}"
            return {
                "candidates": [Candidate(
                    cmd=cmd, ghost_text="", explanation=f"解压 {filename}",
                    confidence=0.90, source="nl2cmd"
                )],
                "diagnostics": [Diagnostic(
                    start=0, end=len(buffer), severity="info",
                    message=f"转换为命令: {cmd}"
                )],
                "replacement": cmd,
            }
        return {}

    def _try_apt_to_dnf(self, buffer: str) -> dict:
        for apt_cmd, dnf_cmd in self._apt_to_dnf.items():
            if buffer.startswith(apt_cmd):
                rest = buffer[len(apt_cmd):].strip()
                if rest and len(rest) <= 10:
                    for short, full in self._package_completions.items():
                        if rest == short:
                            replacement = f"{dnf_cmd} {full}"
                            return {
                                "candidates": [Candidate(
                                    cmd=replacement, ghost_text="",
                                    explanation=f"包管理适配: {buffer} → {replacement} (openEuler 使用 dnf)",
                                    confidence=0.92, source="distro"
                                )],
                                "diagnostics": [Diagnostic(
                                    start=0, end=len(apt_cmd), severity="warning",
                                    message=f"openEuler 使用 dnf 而非 apt"
                                )],
                                "replacement": replacement,
                            }
                replacement = dnf_cmd + (" " + rest if rest else "")
                return {
                    "candidates": [Candidate(
                        cmd=replacement, ghost_text="",
                        explanation=f"包管理适配: {buffer} → {replacement} (openEuler 使用 dnf)",
                        confidence=0.92, source="distro"
                    )],
                    "diagnostics": [Diagnostic(
                        start=0, end=len(apt_cmd), severity="warning",
                        message=f"openEuler 使用 dnf 而非 apt"
                    )],
                    "replacement": replacement,
                }
        return {}

    def _try_tar(self, buffer: str) -> dict:
        if buffer.startswith("解压 ") and buffer.endswith(".tar.gz"):
            filename = buffer[3:]
            cmd = f"tar -zxvf {filename}"
            return {
                "candidates": [Candidate(
                    cmd=cmd, ghost_text="", explanation=f"解压 {filename}",
                    confidence=0.90, source="nl2cmd"
                )],
                "diagnostics": [Diagnostic(
                    start=0, end=len(buffer), severity="info",
                    message=f"转换为命令: {cmd}"
                )],
                "replacement": cmd,
            }
        return {}

    def _try_flag_correction(self, buffer: str) -> dict:
        parts = buffer.split()
        corrected_parts = []
        diagnostics = []
        has_correction = False

        for i, part in enumerate(parts):
            if part in self._flag_corrections:
                corrected = self._flag_corrections[part]
                corrected_parts.append(corrected)
                start = len(" ".join(parts[:i])) + (1 if i > 0 else 0)
                end = start + len(part)
                diagnostics.append(Diagnostic(
                    start=start, end=end, severity="warning",
                    message=f"选项 '{part}' 可能应为 '{corrected}'"
                ))
                has_correction = True
            else:
                corrected_parts.append(part)

        if has_correction:
            replacement = " ".join(corrected_parts)
            return {
                "candidates": [Candidate(
                    cmd=replacement, ghost_text="",
                    explanation=f"选项修正: {buffer} → {replacement}",
                    confidence=0.75, source="rules"
                )],
                "diagnostics": diagnostics,
                "replacement": replacement,
            }
        return {}
