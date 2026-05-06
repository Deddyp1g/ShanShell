"""ShanShell AI 会话上下文收集。"""

import os
import json
import subprocess

from shansh.stats import get_recent_commands as _load_recent_commands


def collect_context(buffer: str, cwd: str) -> dict:
    cursor = len(buffer)

    shell = os.environ.get("SHELL", os.environ.get("SHANSH_SHELL", "/bin/zsh"))

    os_info = _collect_os_info()
    files = _collect_files(cwd)
    project_types = _detect_project_type(files)
    git_info = _collect_git_info(cwd)
    last_commands = _collect_history()

    return {
        "buffer": buffer,
        "cursor": cursor,
        "cwd": cwd,
        "shell": shell,
        "os_info": os_info,
        "files": files,
        "project_types": project_types,
        "git_info": git_info,
        "last_commands": last_commands,
    }


def _collect_os_info() -> dict:
    info = {}
    try:
        with open("/etc/os-release") as f:
            for line in f:
                line = line.strip()
                if line.startswith("ID="):
                    info["id"] = line.split("=", 1)[1].strip('"')
                elif line.startswith("VERSION_ID="):
                    info["version_id"] = line.split("=", 1)[1].strip('"')
                elif line.startswith("PRETTY_NAME="):
                    info["pretty_name"] = line.split("=", 1)[1].strip('"')
    except Exception:
        info = {"id": "unknown", "version_id": "unknown", "pretty_name": "unknown"}
    return info


def _collect_files(cwd: str) -> list:
    try:
        entries = os.listdir(cwd)
        return sorted(entries)[:100]
    except Exception:
        return []


def _detect_project_type(files: list) -> list:
    types = []
    file_set = set(files)
    if "package.json" in file_set:
        types.append("node")
    if "requirements.txt" in file_set or "pyproject.toml" in file_set or "main.py" in file_set:
        types.append("python")
    if "Dockerfile" in file_set:
        types.append("docker")
    if "Makefile" in file_set:
        types.append("make")
    if "CMakeLists.txt" in file_set:
        types.append("cmake")
    return types


def _collect_git_info(cwd: str) -> dict:
    try:
        branch = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=cwd, capture_output=True, text=True, timeout=5
        )
        if branch.returncode != 0:
            return {"is_repo": False}

        modified = subprocess.run(
            ["git", "diff", "--name-only"],
            cwd=cwd, capture_output=True, text=True, timeout=5
        )
        staged = subprocess.run(
            ["git", "diff", "--cached", "--name-only"],
            cwd=cwd, capture_output=True, text=True, timeout=5
        )

        return {
            "is_repo": True,
            "branch": branch.stdout.strip(),
            "modified_files": [f for f in modified.stdout.strip().split("\n") if f],
            "staged_files": [f for f in staged.stdout.strip().split("\n") if f],
        }
    except Exception:
        return {"is_repo": False}


def _collect_history() -> list:
    records = _load_recent_commands(50)
    return [r.get("cmd", "") for r in records]
