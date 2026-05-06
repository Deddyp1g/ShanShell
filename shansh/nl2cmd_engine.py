"""ShanShell AI 自然语言转命令引擎。

优先级:
1. 内置规则匹配 (nl_map) -> 始终可用
2. MockProvider (内置 NL 映射表) -> 始终可用
3. 根据 llm.mode 调用 remote provider
4. 所有 LLM 输出经过 RiskEngine 二审，high risk 拒绝
5. 任何失败回退到 MockProvider
"""

from shansh.models import Candidate
from shansh.config import config_get
from shansh.risk_engine import RiskEngine


_NL_MAP = {
    "查看磁盘空间": "df -h",
    "查看内存使用": "free -h",
    "查看内存": "free -h",
    "查看当前目录文件": "ls -lah",
    "查看当前路径": "pwd",
    "查找最近修改的大文件": "find . -type f -mtime -7 -size +100M -ls",
}


def _get_provider(mode: str):
    if mode == "rules_only":
        from shansh.providers.mock_provider import MockProvider
        return MockProvider()
    elif mode == "remote":
        from shansh.providers.openai_compatible import OpenAICompatibleProvider
        cfg = {"api_key_env": config_get("remote.api_key_env") or "SHANSH_API_KEY",
               "base_url": config_get("remote.base_url") or "https://api.deepseek.com/v1",
               "model": config_get("remote.model") or "deepseek-chat",
               "timeout": int(config_get("remote.timeout") or 5)}
        return OpenAICompatibleProvider(**cfg)
    else:
        from shansh.providers.mock_provider import MockProvider
        return MockProvider()


class NL2CmdEngine:
    def __init__(self):
        pass

    def translate(self, buffer: str, context: dict = None) -> list:
        trimmed = buffer.strip()
        if not trimmed:
            return []

        if trimmed in _NL_MAP:
            cmd = _NL_MAP[trimmed]
            return [Candidate(
                cmd=cmd,
                ghost_text="",
                explanation=f"自然语言: {trimmed} → {cmd}",
                confidence=0.90,
                source="nl2cmd"
            )]

        try:
            mode = config_get("llm.mode") or "rules_only"
        except Exception:
            mode = "rules_only"

        provider = None
        try:
            provider = _get_provider(mode)
        except Exception:
            pass

        if provider is None:
            return self._mock_fallback(trimmed)

        result = None
        try:
            result = provider.suggest({"buffer": trimmed, **(context or {})})
        except Exception:
            result = None

        if not result or not result.get("replacement"):
            return self._mock_fallback(trimmed)

        replacement = result["replacement"]
        risk = RiskEngine().check(replacement)
        if risk["risk"] == "high":
            return [Candidate(
                cmd=trimmed,
                ghost_text="",
                explanation=f"LLM 生成命令被风险引擎拦截: {risk['explanation']}",
                confidence=0.0,
                source="nl2cmd",
                risk="high",
            )]

        return [Candidate(
            cmd=result["replacement"],
            ghost_text="",
            explanation=result.get("explanation", ""),
            confidence=min(float(result.get("confidence", 0.8)), 0.95),
            source="nl2cmd",
            risk=risk["risk"],
        )]

    def _mock_fallback(self, trimmed: str) -> list:
        from shansh.providers.mock_provider import MockProvider
        mock = MockProvider()
        mock_result = mock.suggest({"buffer": trimmed})
        if mock_result and mock_result.get("replacement"):
            return [Candidate(
                cmd=mock_result["replacement"],
                ghost_text="",
                explanation=mock_result.get("explanation", ""),
                confidence=mock_result.get("confidence", 0.8),
                source="mock",
            )]
        return []
