"""OpenAI Compatible Provider — 远程大模型接入。

支持 OpenAI 及兼容 API (DeepSeek, Moonshot 等)。
API Key 从 SHANSH_API_KEY 或配置指定的环境变量读取。
Key 永远不会被打印。
"""

import os
import json
import urllib.request
import urllib.error

from .base import LLMProvider


def _load_prompt() -> str:
    import __main__
    prompt_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "prompts", "nl2cmd_system.txt")
    try:
        with open(prompt_path) as f:
            return f.read()
    except Exception:
        return "You are a Linux shell assistant. Return only JSON."


class OpenAICompatibleProvider(LLMProvider):
    def __init__(self, api_key_env="SHANSH_API_KEY", base_url="https://api.example.com/v1", model="your-model", timeout=8):
        self.api_key = os.environ.get(api_key_env, "")
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout

    def _has_key(self) -> bool:
        return bool(self.api_key)

    def suggest(self, context: dict) -> dict:
        if not self._has_key():
            return {"replacement": "", "explanation": "API Key 未配置", "confidence": 0.0, "diagnostics": []}

        buffer = context.get("buffer", "").strip() if context else ""
        if not buffer:
            return {"replacement": "", "explanation": "", "confidence": 0.0, "diagnostics": []}

        system_prompt = _load_prompt()

        user_prompt = f"用户输入: {buffer}\n"
        if context:
            cwd = context.get("cwd", "")
            if cwd:
                user_prompt += f"当前目录: {cwd}\n"
            os_info = context.get("os_info", {})
            if os_info:
                user_prompt += f"操作系统: {os_info.get('pretty_name', '')}\n"

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.0,
            "max_tokens": 256,
            "stream": False,
            "thinking": {"type": "disabled"},
        }

        try:
            data = json.dumps(payload).encode("utf-8")
            url = f"{self.base_url}/chat/completions"
            req = urllib.request.Request(
                url,
                data=data,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.api_key}",
                },
                method="POST",
            )
            resp = urllib.request.urlopen(req, timeout=self.timeout)
            body = resp.read().decode("utf-8")
            result = json.loads(body)
            content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
            return self._parse_response(content)
        except Exception:
            return {"replacement": "", "explanation": "远程 API 不可用", "confidence": 0.0, "diagnostics": []}

    def _parse_response(self, content: str) -> dict:
        content = content.strip()
        if content.startswith("```"):
            lines = content.split("\n")
            content = "\n".join(lines[1:-1]) if len(lines) > 2 else content
        try:
            parsed = json.loads(content)
            return {
                "replacement": str(parsed.get("replacement", "")),
                "explanation": str(parsed.get("explanation", "")),
                "confidence": float(parsed.get("confidence", 0.5)),
                "diagnostics": parsed.get("diagnostics", []),
            }
        except (json.JSONDecodeError, ValueError):
            if len(content) < 200 and "\n" not in content:
                return {
                    "replacement": content,
                    "explanation": "LLM 原始输出",
                    "confidence": 0.5,
                    "diagnostics": [],
                }
            return {"replacement": "", "explanation": "LLM 输出解析失败", "confidence": 0.0, "diagnostics": []}

    def is_available(self) -> bool:
        return self._has_key()
