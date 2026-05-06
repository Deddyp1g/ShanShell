# ShanShell AI 使用指南

> 快速上手指南 —— 从安装到日常使用，10 分钟玩转 AI 终端助手

---

## 目录

- [1. 这是什么？](#1-这是什么)
- [2. 安装（2 步搞定）](#2-安装2-步搞定)
- [3. 按键速查表](#3-按键速查表)
- [4. 功能详解](#4-功能详解)
  - [4.1 命令补全](#41-命令补全)
  - [4.2 命令纠错](#42-命令纠错)
  - [4.3 下一步预测](#43-下一步预测)
  - [4.4 自然语言转命令](#44-自然语言转命令)
  - [4.5 发行版适配](#45-发行版适配)
  - [4.6 高风险拦截](#46-高风险拦截)
- [5. 配置大模型](#5-配置大模型)
- [6. 命令行工具](#6-命令行工具)
- [7. 常见问题](#7-常见问题)

---

## 1. 这是什么？

ShanShell AI 是你的**终端智能助手**，嵌入在你每天都在用的 Zsh 命令行里。

```
┌─────────────────────────────────────────────────────┐
│                                                     │
│   你输入:  git st                      按 Ctrl-G    │
│                                                     │
│   终端底栏弹出:                                     │
│   ┌─────────────────────────────────────────────┐   │
│   │ [ShanShell] → git status                   │   │
│   └─────────────────────────────────────────────┘   │
│                                                     │
│   按 Tab → 自动补全为 git status                    │
│                                                     │
└─────────────────────────────────────────────────────┘
```

**它能做什么？**

| 你遇到的问题 | ShanShell 怎么帮你 |
|---|---|
| 命令太长不想打全 | 打缩写 → 自动补全 |
| 手滑打错字了 | 自动纠错 + 标注哪里错了 |
| 不知道下一步该敲什么 | 根据上下文预测下一步 |
| 想用中文描述操作 | 自然语言 → 翻译成命令 |
| 从 Ubuntu 切到 openEuler | 自动把 apt 转成 dnf |
| 怕误执行危险命令 | 高风险命令直接拦截 |

---

## 2. 安装（2 步搞定）

### 前置条件

- 系统：openEuler / Linux
- Python 3.6+
- Zsh 5.0+（安装脚本会帮你检查）

### 第 1 步：进入项目目录

```bash
cd ShanShell
```

### 第 2 步：运行安装脚本

```bash
bash install.sh
```

安装脚本会自动完成：

```
=========================================
  ShanShell AI 安装脚本
=========================================

[OK] python3 found: Python 3.11.6      ← 检查 Python
[OK] zsh found: zsh 5.9                ← 检查 Zsh
[OK] 写入默认配置                       ← 创建配置文件
[OK] 已备份 ~/.zshrc → xxx.bak         ← 备份你的原有配置
[OK] 配置块已追加                       ← 注入加载代码
=========================================
  ShanShell AI 安装完成！
=========================================

  下一步：
    exec zsh              ← 重启终端即可生效
```

### 使配置生效

```bash
exec zsh
# 或者
source ~/.zshrc
```

看到 `[ShanShell] loaded.` 就说明成功了！

---

## 3. 按键速查表

每次使用只需要记住 **6 个按键**：

```
┌──────────────┬──────────────────────────────────┐
│    按键      │           功能                   │
├──────────────┼──────────────────────────────────┤
│   Ctrl-G     │  手动唤醒 AI，获取建议             │
│   Ctrl-T     │  开关自动建议模式                 │
│   Tab        │  采纳当前建议                     │
│   Shift+Tab  │  切换到下一条建议（多候选时）      │
│   Esc        │  清除所有建议                     │
│   Enter      │  执行命令（自动安全检查）          │
└──────────────┴──────────────────────────────────┘
```

### 两种使用模式

```
┌─────────────────────────────────────────────────────────┐
│                                                         │
│  模式 1：手动模式（默认）                                 │
│    你打字 → 停下来按 Ctrl-G → AI 弹出建议 → Tab 接受     │
│                                                         │
│  模式 2：自动建议（按 Ctrl-T 开启）                       │
│    你打字 → AI 自动在底栏弹出建议 → Tab 接受             │
│    不用按任何键！像 Copilot 一样流畅                      │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

**自动模式怎么工作？**

```
你敲下键盘                            终端自动反应
───────────────────────────────────────────────────
输入: g                               
  (0.5s 后自动)                      ─────────────────────────
                                     [ShanShell] → git
输入: git st                         
  (0.5s 后自动)                      ─────────────────────────
                                     [ShanShell] → git status
按 Tab                               $ git status    ← 一步到位！
```

- 每 0.5 秒最多触发一次，不会卡顿
- 删除字符时也会自动更新建议
- 空输入时自动清除建议
- 随时按 **Ctrl-T** 关闭/开启

> 推荐用法：安装后先按一次 **Ctrl-T** 开启自动模式，后续就几乎不需要再按 Ctrl-G 了。

## 4. 功能详解

### 4.1 命令补全

> 打缩写，帮你补全

**场景：** 你想查看 git 状态，但不想打完整单词。

```
操作步骤                           终端显示
───────────────────────────────────────────────────
1. 输入: git st                     $ git st

2. 按 Ctrl-G                        $ git st
                                    ─────────────────────────
                                    [ShanShell] → git status

3. 按 Tab                           
                                    $ git status           ← 自动补全！
```

**支持的缩写举例：**

```
你打的           →    建议
────────────────────────────────
git st          →    git status
git co          →    git commit / checkout / clone
git p           →    git push / pull
dnf ins         →    dnf install
systemctl sta   →    systemctl status
docker bu       →    docker build
npm r           →    npm run
```

> ShanShell 内置了 **30+** 条常用命令缩写，覆盖 Git / DNF / Docker / Systemd / NPM 等工具。

---

### 4.2 命令纠错

> 手滑打错？自动纠正，还告诉你哪里错了

**场景：** 打快了，把 `git status` 打成了 `gti statsu`。

```
操作步骤                           终端显示
───────────────────────────────────────────────────
1. 输入: gti statsu                 $ gti statsu

2. 按 Ctrl-G                        $ gti statsu
                                      ^^^ ^^^^^^    ← 标注错误位置！
                                    ─────────────────────────
                                    [ShanShell] → git status

3. 按 Tab                           $ git status           ← 纠正完成
```

**诊断行说明：**

```
 gti statsu
 ^^^ ^^^^^^
 │││ ││││││
 │││ └┴┴┴┴┤ 'statsu' 应为 'status'（严重: error）
 │└┴┤ 'gti' 应为 'git'（严重: warning）
 │   │
 │   用 ^ 的数量标记错误范围
 │
 不同严重程度用不同颜色显示
```

---

### 4.3 下一步预测

> 执行完一条命令后，AI 猜你接下来想干什么

**场景：** 你刚执行完 `git add .`，接下来通常是要 `git commit`。

```
操作步骤                           终端显示
───────────────────────────────────────────────────
1. 执行: git add .                  $ git add .
                                    [执行成功]

2. 来到新的空白提示符               
                                    $ █

3. 按 Ctrl-G（空输入时！）          
                                    ─────────────────────────
                                    [ShanShell] → git commit -m ""

4. 按 Tab                           $ git commit -m ""      ← 预测成功！
```

**支持的工作流预测（共 9 类）：**

```
上一条命令                        →    预测下一步
─────────────────────────────────────────────────
git add .                        →    git commit -m ""
git commit -m "..."              →    git push
python -m venv .venv             →    source .venv/bin/activate
source .venv/bin/activate        →    pip install -r requirements.txt
dnf install nginx                →    systemctl enable --now nginx
systemctl enable --now nginx     →    systemctl status nginx
docker build -t myapp .          →    docker run --rm myapp
git clone <url>                  →    cd <repo_name>
tar -czvf backup.tar.gz dir/     →    ls -lh backup.tar.gz
```

---

### 4.4 自然语言转命令

> 用中文描述你想做的事

**场景：** 想查磁盘空间，但忘了命令是啥。

```
操作步骤                           终端显示
───────────────────────────────────────────────────
1. 输入: 查看磁盘空间               $ 查看磁盘空间

2. 按 Ctrl-G                        ─────────────────────────
                                    [ShanShell] → df -h

3. 按 Tab                           $ df -h                ← 自动翻译！
```

**内置的中文映射（11 条）：**

```
中文描述                  →    命令
────────────────────────────────────────
查看磁盘空间              →    df -h
查看内存使用              →    free -h
查看监听端口              →    ss -tlnp
查看当前进程              →    ps aux
查找大文件                →    find . -type f -size +100M
解压 tar.gz               →    tar -zxvf
复制整个目录              →    cp -r
查看系统版本              →    cat /etc/os-release
查看 IP 地址              →    ip addr
查看当前用户              →    whoami
重启网络服务              →    systemctl restart network
```

---

### 4.5 发行版适配

> 你用 apt 习惯？在 openEuler 上自动转成 dnf

**场景：** 你刚从 Ubuntu 转过来，习惯打 `apt install`。

```
操作步骤                           终端显示
───────────────────────────────────────────────────
1. 输入: apt install nginx          $ apt install nginx

2. 按 Ctrl-G                        $ apt install nginx
                                      ^^^^^^^^^^^       ← 标注不适配部分
                                    ─────────────────────────
                                    [ShanShell] → sudo dnf install nginx

3. 按 Tab                           $ sudo dnf install nginx  ← 自动转换！
```

> ShanShell 读取 `/etc/os-release`，自动识别当前是 openEuler 并使用 dnf。

---

### 4.6 高风险拦截

> 危险命令自动拦下来，防止手滑酿成大祸

**场景：** 不小心输入了 `rm -rf /`。

```
操作步骤                           终端显示
───────────────────────────────────────────────────
1. 输入: rm -rf /                   $ rm -rf /

2. 按 Enter（尝试执行）             
                                    ╔══════════════════════════════╗
                                    ║  HIGH RISK: 删除根目录       ║
                                    ║  "rm -rf /" 将导致系统       ║
                                    ║  不可恢复                    ║
                                    ╚══════════════════════════════╝
                                    
                                    ⚠ 高风险命令已拦截，未执行！

3. 命令没有执行，系统安全！         
```

**被拦截的高危命令举例（15 条）：**

```
高风险命令              风险说明
────────────────────────────────────────────────
rm -rf /                删除根目录，系统不可恢复
rm -rf /*               删除所有文件
dd if=... of=/dev/sda   覆盖整个硬盘
mkfs.ext4 /dev/sda      格式化硬盘
chmod -R 777 /          开放全部权限
chown -R root /         更改全部所有权
:(){ :|:& };:           Fork 炸弹，系统死机
> /dev/sda              清空硬盘
```

**中风险命令（会警告但可放行，5 条）：**

```
中风险命令              风险说明
────────────────────────────────────────────────
sudo rm /tmp/test.txt   需要 root 权限的删除
chmod 777 script.sh     脚本赋权所有人可执行
curl ... | sh           直接执行远程脚本
wget ... | bash         直接执行远程脚本
```

---

## 5. 配置大模型

### 5.1 两种模式

```
模式          需要什么              适合场景
────────────────────────────────────────────────
rules_only    无（默认）            随时随地用，零依赖
remote        API Key              更强推理能力
```

### 5.2 切换模式

```bash
# 查看当前模式
python3 -m shansh.cli config get llm.mode
# 输出: rules_only

# 切换到远程 API（先设置 Key）
export SHANSH_API_KEY="sk-your-key-here"
python3 -m shansh.cli config set llm.mode remote
python3 -m shansh.cli config set remote.base_url "https://api.deepseek.com/v1"
python3 -m shansh.cli config set remote.model "deepseek-chat"
```

### 5.3 安全提醒

- **API Key 不存文件**：通过环境变量 `SHANSH_API_KEY` 注入，不会写入配置文件
- **LLM 不自动执行**：大模型生成的命令只是建议，必须你手动确认
- **LLM 输出有审查**：大模型返回的命令会经过 RiskEngine 再次检查才显示

---

## 6. 命令行工具

不进入 Zsh 交互模式，也能在普通终端测试所有功能：

```bash
# 1. 测试建议
python3 -m shansh.cli suggest --buffer "git st" --cwd .

# 2. 测试渲染效果（带 ANSI 颜色）
python3 -m shansh.cli render --buffer "gti statsu" --cwd .

# 3. 检查命令风险（只分析，不执行！）
python3 -m shansh.cli risk --cmd "rm -rf /"
python3 -m shansh.cli risk --cmd "ls -la"

# 4. 查看/修改配置
python3 -m shansh.cli config get              # 查看全部配置
python3 -m shansh.cli config get llm.mode     # 查看单项
python3 -m shansh.cli config set llm.mode remote

# 5. 健康检查
python3 -m shansh.cli doctor

# 6. 一键验收所有功能
bash tests/manual_check.sh
```

---

## 7. 常见问题

### Q1：Ctrl-G 没反应？

按顺序检查：

```bash
# ① zsh 加载了吗？
echo $ZSH_VERSION          # 应该有输出如 5.9

# ② ShanShell 加载了吗？
type shansh-suggest       # 应该显示它是一个函数

# ③ 如果没加载
source ShanShell/shell/shansh.zsh
```

### Q2：想卸载 ShanShell？

```bash
bash ShanShell/uninstall.sh
```

只会删除 `~/.zshrc` 里的 ShanShell 配置块，不会动你的代码。

### Q3：配置文件在哪里？

```
~/.config/shansh/config.json
```

用 `python3 -m shansh.cli config get` 查看当前配置。

### Q4：历史记录存在哪？

```
~/.shansh/history.json
```

### Q5：怎么确认一切正常？

```bash
bash ShanShell/tests/manual_check.sh
```

输出 16/16 全部通过就说明一切正常。

---

## 一页纸速记卡

```
┌─────────────────────────────────────────────────────────┐
│                                                         │
│               ShanShell AI 速记卡                       │
│                                                         │
│   ┌──────────┬───────────────────────────────────┐     │
│   │ Ctrl-G   │  有输入 → 补全/纠错                │     │
│   │          │  无输入 → 预测下一步               │     │
│   │          │  中文输入 → 翻译成命令              │     │
│   ├──────────┼───────────────────────────────────┤     │
│   │ Tab      │  采纳建议                          │     │
│   ├──────────┼───────────────────────────────────┤     │
│   │ Shift+Tab│  换下一个候选                       │     │
│   ├──────────┼───────────────────────────────────┤     │
│   │ Esc      │  清除建议                          │     │
│   ├──────────┼───────────────────────────────────┤     │
│   │ Enter    │  自动风险检查后执行                 │     │
│   └──────────┴───────────────────────────────────┘     │
│                                                         │
│   验证安装: python3 -m shansh.cli doctor               │
│   一键测试: bash tests/manual_check.sh                   │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

> 有问题？查看完整文档：[README.md](../README.md) | [架构设计](architecture.md) | [演示脚本](demo-script.md)
