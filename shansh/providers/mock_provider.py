"""Mock Provider — 零依赖 NL 转命令。

覆盖常用自然语言请求，始终可用。
"""

from .base import LLMProvider


class MockProvider(LLMProvider):
    _nl_map = {
        "查看磁盘空间": ("df -h", "查看磁盘使用情况"),
        "查看内存使用": ("free -h", "查看内存使用情况"),
        "查看内存": ("free -h", "查看内存使用情况"),
        "查看当前目录文件": ("ls -lah", "列出当前目录所有文件含隐藏文件"),
        "查看当前路径": ("pwd", "显示当前工作目录"),
        "查找最近修改的大文件": ("find . -type f -mtime -7 -size +100M -ls", "查找 7 天内修改的超过 100M 的文件"),
        "查看监听端口": ("ss -tulnp", "查看所有监听端口及对应进程"),
        "查看系统版本": ("cat /etc/os-release", "查看操作系统发行版信息"),
        "查看进程": ("ps aux --sort=-%mem | head -20", "按内存排序查看前 20 进程"),
        "查看当前进程": ("ps aux --sort=-%mem | head -20", "按内存排序查看前 20 进程"),
        "查看网络连接": ("ss -tuln", "查看所有 TCP/UDP 监听连接"),
        "查看 CPU 信息": ("lscpu", "查看 CPU 架构和参数"),
        "查看 IP 地址": ("ip addr", "查看网络接口 IP 地址"),
        "查看当前用户": ("whoami", "显示当前登录用户名"),
        "复制整个目录": ("cp -r", "递归复制目录及其内容"),
        "重启网络服务": ("systemctl restart network", "重启网络服务"),
    }

    def suggest(self, context: dict) -> dict:
        buffer = context.get("buffer", "").strip() if context else ""
        if buffer in self._nl_map:
            cmd, expl = self._nl_map[buffer]
            return {
                "replacement": cmd,
                "explanation": f"自然语言: {buffer} → {cmd} | {expl}",
                "confidence": 0.90,
                "diagnostics": [],
            }
        return {
            "replacement": "",
            "explanation": "MockProvider: 无匹配规则",
            "confidence": 0.0,
            "diagnostics": [],
        }

    def is_available(self) -> bool:
        return True
