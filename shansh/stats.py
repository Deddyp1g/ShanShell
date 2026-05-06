"""ShanShell AI 使用统计与历史记录模块。

历史文件: ~/.shansh/history.json
格式: [{"cmd": "...", "exit_code": 0, "cwd": "...", "ts": 1234567890.0}, ...]
"""

import os
import json
import time
from collections import Counter


HISTORY_DIR = os.path.expanduser("~/.shansh")
HISTORY_FILE = os.path.join(HISTORY_DIR, "history.json")
MAX_HISTORY = 2000


def _ensure_dir():
    os.makedirs(HISTORY_DIR, exist_ok=True)


def _load_history() -> list:
    _ensure_dir()
    try:
        with open(HISTORY_FILE) as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
    except (FileNotFoundError, json.JSONDecodeError):
        pass
    return []


def _save_history(history: list):
    _ensure_dir()
    with open(HISTORY_FILE, "w") as f:
        json.dump(history[-MAX_HISTORY:], f, ensure_ascii=False)


def record_command(cmd: str, exit_code: int = 0, cwd: str = ""):
    if not cmd or not cmd.strip():
        return
    history = _load_history()
    history.append({
        "cmd": cmd.strip(),
        "exit_code": exit_code,
        "cwd": cwd,
        "ts": time.time(),
    })
    _save_history(history)


def get_recent_commands(n: int = 20) -> list:
    history = _load_history()
    return history[-n:]


def get_frequency(cmd: str) -> int:
    history = _load_history()
    count = 0
    for entry in history:
        if entry.get("cmd", "") == cmd:
            count += 1
    return count


class StatsTracker:
    def __init__(self):
        self.completion_count = 0
        self.correction_count = 0
        self.workflow_hits = 0
        self.risk_blocks = 0
        self.command_counter = Counter()
        self.suggestion_accepted = Counter()

    def record_completion(self):
        self.completion_count += 1

    def record_correction(self):
        self.correction_count += 1

    def record_workflow_hit(self):
        self.workflow_hits += 1

    def record_risk_block(self):
        self.risk_blocks += 1

    def record_command(self, command: str):
        self.command_counter[command] += 1

    def record_acceptance(self, suggestion: str):
        self.suggestion_accepted[suggestion] += 1

    def get_top_commands(self, n=10):
        return self.command_counter.most_common(n)

    def get_summary(self):
        return {
            "completions": self.completion_count,
            "corrections": self.correction_count,
            "workflow_hits": self.workflow_hits,
            "risk_blocks": self.risk_blocks,
            "top_commands": self.get_top_commands(5),
        }


_stats_tracker = None


def get_stats():
    global _stats_tracker
    if _stats_tracker is None:
        _stats_tracker = StatsTracker()
    return _stats_tracker
