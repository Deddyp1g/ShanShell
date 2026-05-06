"""ShanShell AI 命令补全引擎。"""

import os
from shansh.models import Candidate


class CompletionEngine:
    def __init__(self):
        self._aliases = {
            "git st": ("git status", "atus"),
            "git sta": ("git status", "tus"),
            "git co": None,
            "git p": None,
            "git br": ("git branch", "anch"),
            "git ch": ("git checkout", "eckout"),
            "git sw": ("git switch", "itch"),
            "git cm": ("git commit", "mmit"),
            "git ps": ("git push", "ush"),
            "git pl": ("git pull", "ull"),
            "git df": ("git diff", "ff"),
            "git lg": ("git log --oneline --graph --all", "og --oneline --graph --all"),
            "dnf ins": ("sudo dnf install", "tall"),
            "dnf se": ("dnf search", "arch"),
            "dnf up": ("sudo dnf upgrade", "grade"),
            "systemctl sta": ("systemctl status", "tus"),
            "systemctl en": ("sudo systemctl enable --now", "able --now"),
            "systemctl re": ("sudo systemctl restart", "start"),
            "docker bu": None,
            "docker ps -": ("docker ps -a", "a"),
            "docker ru": ("docker run --rm ", "n --rm "),
            "docker im": ("docker images", "ages"),
            "pip install -r": None,
            "npm r": None,
            "npm i": ("npm install", "nstall"),
            "python m": None,
            "python -m": None,
            "pytest": ("pytest -q", " -q"),
            "make": None,
            "cd": None,
        }

    def complete(self, buffer: str, context: dict = None) -> list:
        trimmed = buffer.strip()
        if not trimmed:
            return []

        results = []

        results.extend(self._complete_git_co(trimmed))
        results.extend(self._complete_git_p(trimmed))
        results.extend(self._complete_project_aware(trimmed, context))
        results.extend(self._complete_cd(trimmed, context))
        results.extend(self._complete_standard_alias(trimmed))

        return results

    def _complete_git_co(self, trimmed: str) -> list:
        if trimmed == "git co":
            return [
                Candidate(cmd="git commit", ghost_text="mmit", explanation="git commit 提交变更", confidence=0.85, source="rules"),
                Candidate(cmd="git checkout", ghost_text="heckout", explanation="git checkout 切换分支", confidence=0.80, source="rules"),
                Candidate(cmd="git clone", ghost_text="lone", explanation="git clone 克隆仓库", confidence=0.70, source="rules"),
            ]
        return []

    def _complete_git_p(self, trimmed: str) -> list:
        if trimmed == "git p":
            return [
                Candidate(cmd="git push", ghost_text="ush", explanation="git push 推送远程", confidence=0.88, source="rules"),
                Candidate(cmd="git pull", ghost_text="ull", explanation="git pull 拉取远程", confidence=0.82, source="rules"),
            ]
        return []

    def _complete_project_aware(self, trimmed: str, context: dict) -> list:
        files = set(context.get("files", [])) if context else set()
        project_types = context.get("project_types", []) if context else []
        cwd = context.get("cwd", "") if context else ""

        if trimmed == "python m" and "main.py" in files:
            return [Candidate(cmd="python main.py", ghost_text="ain.py", explanation="运行当前目录的 main.py", confidence=0.90, source="rules")]

        if trimmed == "python -m" and "python" in project_types:
            return [Candidate(cmd="python -m pytest", ghost_text=" pytest", explanation="python -m pytest 运行项目测试", confidence=0.80, source="rules")]

        if trimmed == "pip install -r" and "requirements.txt" in files:
            return [Candidate(cmd="pip install -r requirements.txt", ghost_text=" requirements.txt", explanation="安装 requirements.txt 中的依赖", confidence=0.92, source="rules")]

        if trimmed == "npm r" and "package.json" in files:
            return [Candidate(cmd="npm run dev", ghost_text="un dev", explanation="npm run dev 启动开发服务器", confidence=0.88, source="rules")]

        if trimmed == "docker bu" and "Dockerfile" in files:
            dirname = os.path.basename(cwd.rstrip("/")) if cwd else "app"
            return [Candidate(cmd=f"docker build -t {dirname} .", ghost_text=f"ild -t {dirname} .", explanation=f"构建 Docker 镜像 {dirname}", confidence=0.90, source="rules")]

        if trimmed == "make" and "Makefile" in files:
            return [Candidate(cmd="make all", ghost_text=" all", explanation="执行 Makefile 的 all 目标", confidence=0.80, source="rules")]

        return []

    def _complete_cd(self, trimmed: str, context: dict) -> list:
        if not trimmed.startswith("cd ") and trimmed != "cd":
            return []
        cwd = context.get("cwd", os.getcwd()) if context else os.getcwd()
        try:
            prefix = ""
            if trimmed != "cd":
                prefix = trimmed[3:].lstrip()
            subdirs = []
            for entry in sorted(os.listdir(cwd)):
                full = os.path.join(cwd, entry)
                if os.path.isdir(full) and entry.startswith(prefix):
                    subdirs.append(entry)
            results = []
            for d in subdirs[:5]:
                ghost = d[len(prefix):]
                cmd = f"cd {prefix}{d}" if prefix else f"cd {d}"
                results.append(Candidate(cmd=cmd, ghost_text=ghost, explanation=f"进入目录 {d}", confidence=0.75, source="rules"))
            return results
        except Exception:
            return []

    def _complete_standard_alias(self, trimmed: str) -> list:
        if trimmed not in self._aliases:
            return []
        value = self._aliases[trimmed]
        if value is None:
            return []
        cmd, ghost = value
        return [Candidate(cmd=cmd, ghost_text=ghost, explanation=f"补全 {trimmed} → {cmd}", confidence=0.90, source="rules")]
