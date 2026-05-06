# ShanShell AI 渲染协议与终端渲染设计

## 概述

ShanShell 的终端渲染采用渐进增强的三级策略，保证在不同终端环境下都能稳定运行。当前版本实现 Level 1 + Level 2，Level 3 作为未来扩展。

## 三级渲染体系

### Level 1 — zle -M 纯文本 (始终可用)

- 使用 Zsh 的 `zle -M` 在终端底栏显示单行纯文本
- 格式: `[ShanShell] → git status | 查看 Git 仓库状态`
- 无任何 ANSI 转义序列
- 兼容所有终端，是基础保障

适用场景:
- `TERM=dumb` (Emacs shell, eshell 等)
- 非交互式终端 (管道、脚本)
- `NO_COLOR=1` 环境变量设置时
- `SHANSH_NO_COLOR=1` 强制禁用颜色时

### Level 2 — ANSI 颜色 + 下划线 + 诊断行 (主流终端)

在 Level 1 基础上增加:
- **ANSI 颜色映射**: 红(error)、黄(warning)、蓝(info)、灰(ghost text)
- **错误下划线**: 对诊断范围内的字符添加 ANSI 下划线高亮
- **风险颜色**: 高风险用红底白字(`\033[41;97m`)，中风险用黄色
- **诊断行**: 在底栏第二行用 `^` 和 `~` 标注错误位置

示例:

```
[ShanShell] → git status | 自动纠错: gti statsu → git status
 gti statsu
 ^^^ ^^^^^^
```

- `^` 表示 warning/error 级别错误
- `~` 表示 info 级别提示

ANSI 代码:

| 用途 | 代码 | 效果 |
|---|---|---|
| 灰色 (ghost text) | `\033[90m` | 预览中提示用 |
| 红色 (error) | `\033[31m` | 严重错误 |
| 黄色 (warning) | `\033[33m` | 警告 |
| 蓝色 (info) | `\033[34m` | 信息提示 |
| 下划线 | `\033[4m` | 错误位置标记 |
| 红底白字 (high risk) | `\033[41;97m` | 高风险命令 |
| 重置 | `\033[0m` | 恢复默认 |

适用场景:
- xterm、xterm-256color、screen、tmux
- VS Code 内置终端、GNOME Terminal、Konsole
- kitty、Alacritty、WezTerm
- 大部分现代终端仿真器

### Level 3 — undercurl 扩展 (未来)

在 Level 2 基础上增加:
- **波浪下划线**: `\033[4:3m` (kitty 协议) 或 `\033[58;5;COLOR;4:3m`
- **彩色波浪线**: 不同错误等级用不同颜色的波浪线
- **内联 ghost text 渲染**: 在输入行直接显示灰色建议

为什么当前不做:
1. `\033[4:3m` 只有 Kitty 和少数终端支持
2. 内联 ghost text 需要精细控制 zsh 行编辑区域，容易破坏输入体验
3. 答辩演示中使用 Level 1 + Level 2 已足够清晰展示功能
4. 高级渲染不稳定时自动降级到 Level 1 或 Level 2

## 渲染协议

### Zsh → Python 通信

Zsh 调用 Python 后端子进程，通过 stdin/stdout 传递消息:

**请求格式** (JSON):

```json
{
  "type": "complete",
  "input": "git st",
  "cwd": "/root/myproject",
  "history": ["ls", "cd src", "git st"]
}
```

**响应格式** (JSON):

```json
{
  "type": "complete",
  "suggestions": [
    {
      "text": "git status",
      "score": 0.95,
      "source": "rules",
      "description": ""
    }
  ],
  "error": null
}
```

### Shell 模式 KEY=VALUE 输出

Zsh 前端解析 `suggest-shell` 输出的 KEY=VALUE 格式:

```
MODE=completion
REPLACEMENT=git status
GHOST_TEXT=atus
EXPLANATION=补全 git st → git status
RISK=low
SOURCE=rules
CONFIDENCE=0.9
CANDIDATE_COUNT=1
CANDIDATE_0_CMD=git status
CANDIDATE_0_EXPLANATION=...
DIAGNOSTIC_COUNT=0
```

### 风险检测 KEY=VALUE 输出

```
RISK=high
EXPLANATION=删除根目录将导致系统不可恢复
ANSI_WARNING=<red_bg> HIGH RISK: ... </red_bg>
```

## 降级策略

```
检测终端能力
    ↓
TERM=dumb 或 !tty? → Level 1 (纯文本)
    ↓
NO_COLOR=1?        → Level 1
    ↓
SHANSH_NO_COLOR=1?→ Level 1
    ↓
默认               → Level 2 (ANSI)
    ↓
渲染失败?          → 自动回退 Level 1
```

## 前端渲染职责

Zsh 渲染模块 ([shell/shansh.zsh](file://shansh-ai/shell/shansh.zsh)) 当前职责:

1. **shansh-suggest**: 调用 `suggest-shell`，解析 diagnostics，构建诊断行，通过 `zle -M` 显示
2. **shansh-accept-line**: 调用 `risk-shell`，解析 ANSI_WARNING，高风险时用 `echo -e` 输出红色警告并拦截
3. **shansh-next-candidate**: 切换候选时重新显示底栏提示

当前策略:
- 不修改用户输入行 (BUFFER)
- 不尝试内联 ghost text
- 错误位置通过独立诊断行标注
- 高风险通过 `zle -M` + `echo` 双重提示

## 性能约束

- 单次请求响应时间 < 200ms (规则匹配)
- 单次请求响应时间 < 2000ms (LLM 调用，后续阶段)
- 不允许阻塞用户终端输入
- ANSI 渲染零额外延迟 (纯字符串拼接)

## 答辩演示要点

1. 演示 `gti statsu` → Ctrl-G，展示诊断行标注错误位置
2. 演示 `rm -rf /` → Enter，展示高风险红底拦截
3. 演示正常补全 `git st` → Tab 接受
4. 说明三级渲染策略：当前稳定 Level 1+2，未来可扩展 Level 3
