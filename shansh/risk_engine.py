"""ShanShell AI 风险检测引擎。"""

import re


class RiskEngine:
    _high_patterns = [
        (r"rm\s+-rf\s+/$", "删除根目录 \"rm -rf /\" 将导致系统不可恢复"),
        (r"rm\s+-rf\s+/\*", "删除根目录下所有文件 \"rm -rf /*\" 将导致系统不可恢复"),
        (r"rm\s+-rf\s+/root", "删除 /root 目录将导致管理员数据丢失"),
        (r"rm\s+-rf\s+/home", "删除 /home 目录将导致所有用户数据丢失"),
        (r"dd\s+if=/dev/zero\s+of=/dev/sd[a-z]", "直接写入块设备将覆盖磁盘数据，不可恢复"),
        (r"mkfs\.\S+\s+/dev/sd[a-z]", "格式化磁盘将导致数据永久丢失"),
        (r"chmod\s+-R\s+777\s+/", "递归修改根目录权限为 777 将导致严重安全风险"),
        (r"chown\s+-R\s+root\s+/", "递归修改根目录所有者为 root 可能导致权限异常"),
        (r":\(\)\s*\{\s*:\s*\|\s*:\s*&\s*\}\s*;\s*:", "Fork Bomb，将耗尽系统资源导致系统崩溃"),
    ]

    _medium_patterns = [
        (r"sudo\s+rm", "使用 sudo rm 删除文件，请确认目标正确"),
        (r"chmod\s+777", "修改权限为 777 可能带来安全风险"),
        (r"curl\s+.*\s*\|\s*(ba)?sh", "curl 管道执行脚本存在安全风险，请确认来源可信"),
        (r"wget\s+.*\s*\|\s*(ba)?sh", "wget 管道执行脚本存在安全风险，请确认来源可信"),
    ]

    def check(self, command: str) -> dict:
        if not command or not command.strip():
            return {"risk": "low", "explanation": "命令为空，无风险"}

        cmd_clean = command.strip()

        for pattern, explanation in self._high_patterns:
            if re.search(pattern, cmd_clean):
                return {"risk": "high", "explanation": explanation}

        for pattern, explanation in self._medium_patterns:
            if re.search(pattern, cmd_clean):
                return {"risk": "medium", "explanation": explanation}

        return {"risk": "low", "explanation": "未检测到明显风险"}
