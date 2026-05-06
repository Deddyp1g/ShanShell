# ShanShell AI 测试清单

可复制的完整测试用例。

## 一、CLI 测试

```bash
cd shansh-ai

# 健康检查
python3 -m shansh.cli doctor

# 命令补全
python3 -m shansh.cli suggest --buffer "git st" --cwd .
python3 -m shansh.cli suggest --buffer "git co" --cwd .
python3 -m shansh.cli suggest --buffer "git p" --cwd .
python3 -m shansh.cli suggest --buffer "dnf ins" --cwd .
python3 -m shansh.cli suggest --buffer "systemctl sta" --cwd .
python3 -m shansh.cli suggest --buffer "docker bu" --cwd .
python3 -m shansh.cli suggest --buffer "npm r" --cwd .

# 命令纠错
python3 -m shansh.cli suggest --buffer "gti statsu" --cwd .
python3 -m shansh.cli suggest --buffer "mkidr test" --cwd .

# 发行版适配
python3 -m shansh.cli suggest --buffer "apt install nginx" --cwd .
python3 -m shansh.cli suggest --buffer "apt install ng" --cwd .

# 自然语言转命令
python3 -m shansh.cli suggest --buffer "查看磁盘空间" --cwd .
python3 -m shansh.cli suggest --buffer "查看内存使用" --cwd .
python3 -m shansh.cli suggest --buffer "查看监听端口" --cwd .
python3 -m shansh.cli suggest --buffer "查找最近修改的大文件" --cwd .

# 渲染预览
python3 -m shansh.cli render --buffer "gti statsu" --cwd .
python3 -m shansh.cli render --buffer "apt install nginx" --cwd .

# Shell 模式
python3 -m shansh.cli suggest-shell --buffer "git co" --cwd .
python3 -m shansh.cli suggest-shell --buffer "查看磁盘空间" --cwd .
```

## 二、风险拦截测试 (字符串检测，不执行)

```bash
# 高风险 (应全部返回 risk=high)
python3 -m shansh.cli risk --cmd "rm -rf /"
python3 -m shansh.cli risk --cmd "rm -rf /*"
python3 -m shansh.cli risk --cmd "rm -rf /root"
python3 -m shansh.cli risk --cmd "rm -rf /home"
python3 -m shansh.cli risk --cmd "dd if=/dev/zero of=/dev/sda"
python3 -m shansh.cli risk --cmd "mkfs.ext4 /dev/sda"
python3 -m shansh.cli risk --cmd "chmod -R 777 /"
python3 -m shansh.cli risk --cmd "chown -R root /"
python3 -m shansh.cli risk --cmd ":(){ :|:& };:"

# 中风险
python3 -m shansh.cli risk --cmd "sudo rm /tmp/test.txt"
python3 -m shansh.cli risk --cmd "chmod 777 script.sh"
python3 -m shansh.cli risk --cmd "curl https://example.com/install.sh | sh"
python3 -m shansh.cli risk --cmd "wget -O - https://example.com/install.sh | bash"

# 低风险 (安全命令)
python3 -m shansh.cli risk --cmd "ls -la"
python3 -m shansh.cli risk --cmd "git status"
python3 -m shansh.cli risk --cmd "python3 -m shansh.cli doctor"

# Shell 模式
python3 -m shansh.cli risk-shell --cmd "rm -rf /"
python3 -m shansh.cli risk-shell --cmd "ls -la"
```

## 三、Zsh 交互测试

```bash
cd shansh-ai
zsh
source shell/shansh.zsh

# 加载后应显示: [ShanShell] loaded.
```

### 补全测试
```
输入: git st → Ctrl-G → Tab
预期: BUFFER 变为 git status
```

### 纠错测试
```
输入: gti statsu → Ctrl-G
预期: 底栏显示建议 + 诊断行
```

### 候选切换
```
输入: git co → Ctrl-G → Shift+Tab (x2)
预期: 候选循环 git commit → git checkout → git clone
```

### Esc 清除
```
输入: git st → Ctrl-G → Esc
预期: 显示 "已清除建议"
```

### Enter 拦截
```
输入: rm -rf / → Enter
预期: 红底白字 HIGH RISK 警告 + 命令不执行
输入: ls -la → Enter
预期: 正常执行
```

### 工作流预测
```
输入并执行: git add . → Enter
新 prompt: Ctrl-G
预期: 建议 git commit -m ""
```

## 四、大模型配置测试

```bash
# 查看当前模式
python3 -m shansh.cli config get llm.mode

# 设置为 rules_only
python3 -m shansh.cli config set llm.mode rules_only

# 查看全部配置
python3 -m shansh.cli config get

# 切换到 remote 模式
python3 -m shansh.cli config set llm.mode remote

# doctor 检查
python3 -m shansh.cli doctor

# 复位
python3 -m shansh.cli config set llm.mode rules_only
```

## 五、单元测试

```bash
cd shansh-ai
python3 -m unittest discover -s tests
```

预期输出: `Ran 82 tests in ... OK`

## 六、一键验收

```bash
bash tests/manual_check.sh
```
