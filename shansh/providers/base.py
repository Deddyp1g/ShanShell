"""ShanShell AI LLM Provider 抽象基类。"""

from abc import ABC, abstractmethod


class LLMProvider(ABC):

    @abstractmethod
    def suggest(self, context: dict) -> dict:
        """返回 {"replacement": "...", "explanation": "...", "confidence": 0.8, "diagnostics": [...]}"""
        ...

    @abstractmethod
    def is_available(self) -> bool:
        ...
