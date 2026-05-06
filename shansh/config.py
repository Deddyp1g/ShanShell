"""ShanShell AI 配置管理。

配置文件: ~/.config/shansh/config.json
支持嵌套路径读写: config.get("llm.mode"), config.set("local.model", "qwen2.5:0.5b")
"""

import os
import json


CONFIG_DIR = os.path.expanduser("~/.config/shansh")
CONFIG_PATH = os.path.join(CONFIG_DIR, "config.json")

DEFAULT_CONFIG = {
    "llm": {
        "mode": "rules_only",
    },
    "remote": {
        "provider": "openai_compatible",
        "base_url": "https://api.deepseek.com/v1",
        "model": "deepseek-chat",
        "api_key_env": "SHANSH_API_KEY",
        "timeout": 5,
    },
    "privacy": {
        "send_cwd": True,
        "send_os_info": True,
        "send_history": False,
    },
}


def _ensure_dir():
    os.makedirs(CONFIG_DIR, exist_ok=True)


def _deep_get(d: dict, path: str):
    keys = path.split(".")
    for k in keys:
        if isinstance(d, dict) and k in d:
            d = d[k]
        else:
            return None
    return d


def _deep_set(d: dict, path: str, value):
    keys = path.split(".")
    for k in keys[:-1]:
        if k not in d:
            d[k] = {}
        d = d[k]
    d[keys[-1]] = value


def load_config() -> dict:
    config = json.loads(json.dumps(DEFAULT_CONFIG))
    _ensure_dir()
    try:
        with open(CONFIG_PATH) as f:
            file_config = json.load(f)
            _deep_merge(config, file_config)
    except (FileNotFoundError, json.JSONDecodeError):
        pass
    return config


def _deep_merge(base: dict, overlay: dict):
    for k, v in overlay.items():
        if isinstance(v, dict) and isinstance(base.get(k), dict):
            _deep_merge(base[k], v)
        else:
            base[k] = v


def save_config(config: dict):
    _ensure_dir()
    with open(CONFIG_PATH, "w") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)


def config_get(path: str) -> any:
    config = load_config()
    return _deep_get(config, path)


def config_set(path: str, value):
    config = load_config()
    _deep_set(config, path, value)
    save_config(config)
