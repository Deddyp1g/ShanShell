# ShanShell AI 架构设计

## 整体架构

```
┌──────────────────────────────────────────────────────────────┐
│                       Zsh 终端层                              │
│  shansh.zsh (widgets: suggest/accept/clear/accept-line)     │
│  按键绑定: Ctrl-G  Tab  Shift+Tab  Esc  Enter                │
└──────────────┬───────────────────────────────────────────────┘
               │ KEY=VALUE 协议 (suggest-shell / risk-shell)
┌──────────────▼───────────────────────────────────────────────┐
│                    Python 后端 (shansh/)                     │
│                                                               │
│  ┌─────────────┐  ┌─────────────────────┐                     │
│  │   cli.py    │  │     server.py        │                    │
│  │  CLI 入口   │  │  HTTP 127.0.0.1:8765│                    │
│  └──────┬──────┘  └─────────────────────┘                     │
│         │                                                     │
│  ┌──────▼──────────────────────────────────────┐             │
│  │             Engine 层                        │             │
│  │                                              │             │
│  │  ┌────────────────┐  ┌───────────────────┐  │             │
│  │  │ completion     │  │ correction        │  │             │
│  │  │ _engine        │  │ _engine           │  │             │
│  │  │                │  │                   │  │             │
│  │  │ 30+ 别名映射   │  │ typo 纠错         │  │             │
│  │  │ 项目感知补全   │  │ apt→dnf 映射      │  │             │
│  │  │ cd 目录候选    │  │ NL 规则匹配       │  │             │
│  │  │ 多候选返回     │  │ 选项修正          │  │             │
│  │  └────────────────┘  └───────────────────┘  │             │
│  │                                              │             │
│  │  ┌────────────────┐  ┌───────────────────┐  │             │
│  │  │ workflow       │  │ nl2cmd_engine     │  │             │
│  │  │ _engine        │  │                   │  │             │
│  │  │                │  │ 9 类工作流预测    │  │             │
│  │  │ 11 条内置映射  │  │ 9 种前后关联       │  │             │
│  │  │ Mock→LLM 级联  │  │ 历史序列匹配       │  │             │
│  │  └────────────────┘  └───────────────────┘  │             │
│  │                                              │             │
│  │  ┌────────────────┐  ┌───────────────────┐  │             │
│  │  │ risk_engine    │  │ ranker            │  │             │
│  │  │                │  │                   │  │             │
│  │  │ 15 高危+5 中危 │  │ confidence 排序    │  │             │
│  │  │ 正则模式匹配   │  │ 高风险降权=0       │  │             │
│  │  │ 中文风险说明   │  │ top 3 返回         │  │             │
│  │  └────────────────┘  └───────────────────┘  │             │
│  └──────────────────────────────────────────────┘             │
│                                                               │
│  ┌──────────────────────────────────────────────┐             │
│  │            Provider 层 (可插拔)               │             │
│  │                                              │             │
│  │  LLMProvider (ABC)                           │             │
│  │  ├── MockProvider       (11 条 NL, 始终可用) │             │
│  │  └── OpenAICompatProvider (HTTPS remote API) │             │
│  └──────────────────────────────────────────────┘             │
│                                                               │
│  ┌──────────────────────────────────────────────┐             │
│  │            渲染层                             │             │
│  │                                              │             │
│  │  RenderEngine (render_protocol.py)           │             │
│  │  ├── Level 1: zle -M 纯文本                  │             │
│  │  ├── Level 2: ANSI 颜色 + 诊断行 + 下划线    │             │
│  │  └── Level 3: undercurl (未来)               │             │
│  └──────────────────────────────────────────────┘             │
│                                                               │
│  ┌──────────────────────────────────────────────┐             │
│  │            数据层                             │             │
│  │                                              │             │
│  │  context.py   — 上下文收集 (OS/文件/Git/历史)│             │
│  │  config.py    — 配置管理 (嵌套路径读写)      │             │
│  │  stats.py     — 历史记录 (~/.shansh/)       │             │
│  │  models.py    — 数据模型 (dataclass)         │             │
│  │  rules/*.json — 5 个规则配置文件             │             │
│  │  prompts/*.txt — 4 个 LLM 提示词模板         │             │
│  └──────────────────────────────────────────────┘             │
└───────────────────────────────────────────────────────────────┘
```

## 核心数据流

```
┌──────────┐    Ctrl-G     ┌──────────────┐   suggest-shell   ┌──────────────┐
│  用户输入  │ ────────────→│ shansh.zsh   │ ────────────────→ │  Python CLI  │
│  (BUFFER) │              │ (ZLE Widget) │                   │  (cli.py)    │
└──────────┘              └──────────────┘                   └──────┬───────┘
                                                                     │
                              ┌──────────────────────────────────────┘
                              ↓
                     ┌─────────────────┐
                     │  context.py     │  收集 OS / 文件 / Git / 历史
                     └────────┬────────┘
                              ↓
                ┌─────────────────────────────┐
                │        路由到 Engine         │
                │                             │
                │  buffer 非空?                │
                │    ├── 是中文? → nl2cmd      │
                │    └── 否 → completion       │
                │            + correction       │
                │            + ranker           │
                │                             │
                │  buffer 为空?                │
                │    └── workflow_engine       │
                └─────────────┬───────────────┘
                              ↓
                ┌─────────────────────────────┐
                │       RiskEngine 一审        │
                │      检查所有候选命令         │
                │      high → confidence=0    │
                └─────────────┬───────────────┘
                              ↓
                ┌─────────────────────────────┐
                │    render_protocol.py        │
                │    生成 KEY=VALUE 输出        │
                │    构建诊断行 (^^^)           │
                └─────────────┬───────────────┘
                              ↓
┌──────────┐    zle -M      ┌──────────────┐
│  终端显示  │ ←──────────── │ shansh.zsh   │
│ (底栏+DIAG)│              │ 显示建议       │
└──────────┘              └──────────────┘
```

## 模块职责

### 1. Shell Frontend (Zsh ZLE)

| 组件 | 职责 |
|---|---|
| `shansh-suggest` | 读取 BUFFER，调用 suggest-shell，解析并显示建议 |
| `shansh-accept` | 替换 BUFFER 为建议命令 (高风险拒绝) |
| `shansh-clear` | 清除所有建议状态 |
| `shansh-accept-line` | Enter 前风险检查 (risk-shell)，记录历史 |
| `shansh-next-candidate` | 多候选循环切换 |

### 2. Context Engine

| 模块 | 职责 |
|---|---|
| `context.py` | 收集 OS 信息 (/etc/os-release)、文件列表、项目类型、Git 状态、历史命令 |
| `stats.py` | 持久化历史记录到 `~/.shansh/history.json`，提供 get_recent/get_frequency |

### 3. Completion Engine

- 30+ 命令别名映射 (git st→status, dnf ins→install, docker bu→build 等)
- 项目感知补全 (main.py/python, requirements.txt/pip, Dockerfile/docker, Makefile/make)
- 多候选返回 (git co→commit/checkout/clone, git p→push/pull)
- 上下文感知 cd 目录候选

### 4. Correction Engine

- 拼写纠错: typo 映射表 (gti→git, statsu→status, mkidr→mkdir)
- 发行版适配: apt→dnf 自动映射
- 包名智能补全: ng→nginx
- 命令行选项修正: -z→-l
- 自然语言短映射: "查看磁盘空间"→df -h, "解压 *.tar.gz"→tar -zxvf
- Diagnostic 输出: 标注错误字符范围 (start/end/severity/message)

### 5. Workflow Engine

9 类工作流预测:
- `git add .` → `git commit -m ""`
- `git commit -m "..."` → `git push`
- `python -m venv .venv` → `source .venv/bin/activate`
- `source .venv/bin/activate` → `pip install -r requirements.txt` (需 requirements.txt)
- `sudo dnf install <pkg>` → `sudo systemctl enable --now <pkg>`
- `systemctl enable --now <svc>` → `systemctl status <svc>`
- `docker build -t <name> .` → `docker run --rm <name>`
- `git clone <url>` → `cd <repo_name>`
- `tar -czvf <archive> <dir>` → `ls -lh <archive>`

### 6. LLM Provider

抽象接口:

```python
class LLMProvider(ABC):
    def suggest(self, context: dict) -> dict: ...
    def is_available(self) -> bool: ...
```

四种 Provider:
- **MockProvider**: 11 条 NL 规则，始终可用
- **OpenAICompatibleProvider**: POST /chat/completions，API Key 环境变量注入

### 7. Risk Engine

- 15 个高危正则: rm -rf /、dd、mkfs、chmod 777 /、chown -R root /、fork bomb 等
- 5 个中危正则: sudo rm、chmod 777、curl|sh、wget|sh
- 中文风险解释
- 三层审查: Engine层一审 → LLM二审 → Enter前三审

### 8. Render Engine

三级渲染:
- Level 1: zle -M 纯文本 (TERM=dumb, NO_COLOR=1)
- Level 2: ANSI 颜色 + 下划线 + 诊断行 (主流终端)
- Level 3: undercurl 扩展 (未来)

### 9. Learning / Stats

- 命令历史持久化 (~/.shansh/history.json)
- 命令频率统计
- 补全/纠错/拦截计数器
- 热门命令排行

## 安全设计

```
用户输入
    ↓
Engine 层 (规则审查: 规则本身不含危险命令)
    ↓
RiskEngine 一审 (正则匹配 14+5 风险模式)
    ↓
LLM 二审 (LLM 输出必须通过 RiskEngine 再次检查)
    ↓
ranker (high risk → confidence=0)
    ↓
shansh-accept (high risk → 拒绝接受)
    ↓
shansh-accept-line → risk-shell → 三审 (high → 拦截不执行)
    ↓
仅 low/medium risk 命令可以通过
```

## 渲染协议

Zsh 前端通过 `suggest-shell` 和 `risk-shell` 两个 KEY=VALUE 格式命令与 Python 后端通信。

详见 [render-design.md](render-design.md) 和 [llm-provider-design.md](llm-provider-design.md)。
