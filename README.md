# ShanShell AI

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.6+](https://img.shields.io/badge/python-3.6+-green.svg)](https://www.python.org/)
[![Shell: Zsh](https://img.shields.io/badge/shell-zsh-orange.svg)](https://www.zsh.org/)

**AI-Powered Terminal Assistant** — 嵌入 Zsh 的智能命令补全、纠错与安全执行系统。

输入缩写自动补全，打错字自动纠正，用中文描述即可生成命令，危险操作自动拦截。

---

## 功能展示

```
$ git st                         $ gti statsu
按 Ctrl-G ▼                      按 Ctrl-G ▼
┌──────────────────────────┐     ┌──────────────────────────┐
│ → git status             │     │  gti statsu              │
│   补全 git st → git status│    │  ^^^ ^^^^^^              │
└──────────────────────────┘     │ → git status             │
按 Tab → 命令自动补全             │   修正: gti→git status→status│
                                 └──────────────────────────┘
$ rm -rf /                       按 Tab → 命令自动纠错
按 Enter ▼
╔═══════════════════════════╗    $ 查看磁盘空间
║ HIGH RISK: 删除根目录      ║    按 Ctrl-G ▼
║ 该命令可能导致系统不可恢复  ║    ┌──────────────────────────┐
╚═══════════════════════════╝    │ → df -h                  │
⚠ 高风险命令已拦截！              │   自然语言→命令            │
                                 └──────────────────────────┘
                                 按 Tab → 执行 df -h
```

## 核心能力

| 功能 | 说明 | 示例 |
|---|---|---|
| 命令补全 | 输入前缀自动补全完整命令 | `git st` → `git status` |
| 命令纠错 | 修正拼写错误并标注位置 | `gti statsu` → `git status` |
| 自然语言转命令 | 用中文描述意图 | "查看磁盘空间" → `df -h` |
| 发行版适配 | 自动识别 openEuler | `apt install` → `sudo dnf install` |
| 工作流预测 | 根据上一步猜下一步 | `git add .` 后预测 `git commit` |
| 高风险拦截 | 危险命令执行前阻止 | `rm -rf /` 被拦截 |
| AI 增强 | 可选接入 LLM API | 中英文都可转命令 |

## 快速开始

### 环境要求

- **Python** 3.6+
- **Zsh** 5.0+
- **Linux** (openEuler / Ubuntu / Fedora / Debian 等)

### 安装

```bash
# 1. 克隆项目
git clone https://github.com/Deddyp1g/ShanShell.git
cd ShanShell

# 2. 一键安装
bash install.sh

# 3. 重新加载终端
exec zsh
```

看到 `[ShanShell] loaded.` 即安装成功。

### 卸载

```bash
bash ShanShell/uninstall.sh
# 彻底删除: rm -rf ShanShell ~/.config/shansh
```

## 使用方法

### 按键映射

| 按键 | 功能 |
|---|---|
| **Ctrl-G** | 手动触发建议 |
| **Ctrl-T** | 开关自动建议模式 |
| **Tab** | 接受当前建议 |
| **Shift+Tab** | 切换下一个候选 |
| **Esc** | 清除建议 |
| **Enter** | 执行命令（含风险检查） |

### 自动建议模式

按 `Ctrl-T` 开启自动建议后，打字时会在规则命中时即时弹出建议。规则未命中时，1秒后自动调用 AI 大模型获取建议——无需额外按键。

## 大模型配置（可选）

默认使用纯规则引擎，无需任何外部依赖。如需 AI 增强，可接入 OpenAI 兼容 API：

```bash
# 1. 设置 API Key（环境变量，不写入文件）
export SHANSH_API_KEY="sk-your-key-here"

# 2. 切换到远程模式
python3 -m shansh.cli config set llm.mode remote
python3 -m shansh.cli config set remote.base_url "https://api.deepseek.com/v1"
python3 -m shansh.cli config set remote.model "deepseek-chat"
```

支持的 API 服务商：DeepSeek、OpenAI、Moonshot 等任何 OpenAI 兼容接口。

## 命令行工具

```bash
# 智能建议
python3 -m shansh.cli suggest --buffer "git st"

# 风险检测
python3 -m shansh.cli risk --cmd "rm -rf /"

# 配置管理
python3 -m shansh.cli config get              # 查看全部配置
python3 -m shansh.cli config set llm.mode remote

# 健康检查
python3 -m shansh.cli doctor

# 运行测试
python3 -m unittest discover -s tests
bash tests/manual_check.sh
```

## 项目结构

```
ShanShell/
├── shell/shansh.zsh          # Zsh ZLE 前端 (widgets + 按键绑定)
├── shansh/                   # Python 后端
│   ├── cli.py                 # CLI 入口
│   ├── config.py              # 配置管理 (~/.config/shansh/config.json)
│   ├── context.py             # 上下文收集 (OS/文件/Git/历史)
│   ├── models.py              # 数据模型
│   ├── completion_engine.py   # 命令补全引擎 (30+ 规则)
│   ├── correction_engine.py   # 命令纠错引擎
│   ├── workflow_engine.py     # 工作流预测引擎 (9 种模式)
│   ├── nl2cmd_engine.py       # 自然语言→命令引擎
│   ├── risk_engine.py         # 风险检测引擎 (15 高危 + 5 中危)
│   ├── ranker.py              # 候选排序器
│   ├── render_protocol.py     # ANSI 渲染引擎
│   └── providers/             # LLM Provider
│       ├── base.py            # 抽象基类
│       ├── mock_provider.py   # 内置规则 (始终可用)
│       └── openai_compatible.py # OpenAI 兼容 API
├── rules/                     # 规则 JSON 配置
├── prompts/                   # LLM 提示词
├── tests/                     # 测试
├── docs/                      # 设计文档
├── install.sh                 # 一键安装
├── uninstall.sh               # 一键卸载
└── LICENSE                    # MIT License
```

## 安全设计

- **多层审查**: 规则引擎 → RiskEngine 一审 → LLM 输出二审 → Enter 前三审
- **高风险拒绝**: risk=high 的命令禁止 Tab 接受，Enter 时拦截
- **API Key 保护**: Key 仅通过环境变量注入，永不写入文件或日志
- **零依赖**: Python 标准库实现，无需 pip install
- **命令不自动执行**: LLM 生成的命令仅为建议，需用户手动确认

## 设计文档

- [架构设计](docs/architecture.md)
- [渲染协议设计](docs/render-design.md)
- [使用指南](docs/user-guide.md)
- [演示脚本](docs/demo-script.md)

## License

MIT License — 详见 [LICENSE](LICENSE)
