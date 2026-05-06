# ShanShell AI 演示脚本

后续阶段录制演示视频时使用的脚本。

## 环境准备

```bash
cd ShanShell
bash install.sh
```

## 演示流程

### 1. 命令补全

```bash
$ git st<Tab>
  → git status (rules, 0.95)

$ git br<Tab>
  → git branch (rules, 0.95)
```

### 2. 命令纠错

```bash
$ gti statsu<Enter>
  [?] 是否要执行 git status ？[Y/n]
  → 自动纠错并执行

$ dcoker<Enter>
  → 提示: docker ? [Y/n]
```

### 3. 跨发行版适配

```bash
$ apt install nginx<Tab>
  → sudo dnf install nginx (distro, 0.90)
  → 自动识别 openEuler，映射 apt -> dnf
```

### 4. 工作流预测

```bash
$ git add .
  → ↓ git commit -m "" (Ctrl+F 接受)

$ python -m venv .venv
  → ↓ source .venv/bin/activate (Ctrl+F 接受)
```

### 5. 自然语言转命令

```bash
$ #nl 查看磁盘空间
  → df -h

$ #nl 查找日志文件
  → find /var/log -name "*.log" -type f
```

### 6. 高风险拦截

```bash
$ rm -rf /<Enter>
  ⚠ 高风险命令检测: rm -rf /
    原因: 删除根目录将导致系统不可恢复
    Level: CRITICAL — 已拦截

$ chmod -R 777 /<Enter>
  ⚠ 高风险: 递归修改根目录权限
    Level: HIGH — 输入 yes 继续 / no 取消
```

## 关闭演示

```bash
$ exit  # 或 Ctrl+D
```

## 录制建议

- 使用 `script` 命令录制终端会话
- 终端字体: monospace, 18pt
- 终端配色: 深色主题
- 每个场景间隔 3 秒
