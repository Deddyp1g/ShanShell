"""ShanShell AI 工作流预测引擎。"""

from shansh.models import Candidate


class WorkflowEngine:
    _patterns = [
        ("git add .", "git commit -m \"\"", "git add 后通常执行 git commit 提交"),
        ("git add -A", "git commit -m \"\"", "git add -A 后通常执行 git commit 提交"),
        ("git commit", "git push", None),
        ("git commit -m", "git push", None),
        ("python -m venv", "source .venv/bin/activate", None),
        ("python -m venv .venv", "source .venv/bin/activate", "创建虚拟环境后应激活"),
        ("source .venv/bin/activate", None, None),
        ("sudo dnf install", None, None),
        ("systemctl enable --now", "systemctl status", None),
        ("docker build -t", None, None),
        ("docker build -t ", None, None),
        ("git clone", None, None),
        ("tar -czvf", None, None),
        ("tar -czvf ", None, None),
        ("pip install", None, None),
    ]

    def predict(self, last_commands: list, context: dict = None) -> list:
        if not last_commands:
            return []

        last = last_commands[-1].strip()
        if not last:
            return []

        results = []

        if last == "git add ." or last.startswith("git add "):
            results.append(Candidate(
                cmd="git commit -m \"\"",
                ghost_text="",
                explanation="git add 后通常执行 git commit 提交变更",
                confidence=0.85,
                source="rules"
            ))

        if (last.startswith("git commit -m") or last.startswith("git commit")):
            results.append(Candidate(
                cmd="git push",
                ghost_text="",
                explanation="commit 后通常推送远程",
                confidence=0.80,
                source="rules"
            ))

        if last == "python -m venv .venv" or last == "python3 -m venv .venv":
            results.append(Candidate(
                cmd="source .venv/bin/activate",
                ghost_text="",
                explanation="创建虚拟环境后应激活",
                confidence=0.90,
                source="rules"
            ))

        if last == "source .venv/bin/activate":
            files = context.get("files", []) if context else []
            if "requirements.txt" in files:
                results.append(Candidate(
                    cmd="pip install -r requirements.txt",
                    ghost_text="",
                    explanation="激活虚拟环境后安装依赖",
                    confidence=0.85,
                    source="rules"
                ))

        if last.startswith("sudo dnf install "):
            pkg = last[len("sudo dnf install "):].strip().split()[0] if " " in last[len("sudo dnf install "):] else last[len("sudo dnf install "):].strip()
            if pkg:
                results.append(Candidate(
                    cmd=f"sudo systemctl enable --now {pkg}",
                    ghost_text="",
                    explanation=f"安装 {pkg} 后可启用并启动服务",
                    confidence=0.80,
                    source="rules"
                ))

        if last.startswith("systemctl enable --now "):
            parts = last.split()
            if len(parts) >= 4:
                svc = parts[3]
                results.append(Candidate(
                    cmd=f"systemctl status {svc}",
                    ghost_text="",
                    explanation=f"启用服务后可查看 {svc} 状态",
                    confidence=0.80,
                    source="rules"
                ))

        if last.startswith("docker build -t "):
            parts = last.split()
            name_part = ""
            for p in parts[3:]:
                if p != ".":
                    name_part = p
                else:
                    break
            if name_part:
                results.append(Candidate(
                    cmd=f"docker run --rm {name_part}",
                    ghost_text="",
                    explanation=f"构建镜像后可运行容器",
                    confidence=0.80,
                    source="rules"
                ))

        if last.startswith("git clone "):
            parts = last.split()
            if len(parts) >= 3:
                url = parts[2]
                repo_name = url.rstrip("/").split("/")[-1]
                if repo_name.endswith(".git"):
                    repo_name = repo_name[:-4]
                results.append(Candidate(
                    cmd=f"cd {repo_name}",
                    ghost_text="",
                    explanation=f"clone 后进入仓库目录",
                    confidence=0.85,
                    source="rules"
                ))

        if last.startswith("tar -czvf "):
            parts = last.split()
            if len(parts) >= 3:
                archive = parts[2]
                results.append(Candidate(
                    cmd=f"ls -lh {archive}",
                    ghost_text="",
                    explanation=f"打包后查看归档文件大小",
                    confidence=0.80,
                    source="rules"
                ))

        return results
