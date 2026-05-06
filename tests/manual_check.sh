#!/usr/bin/env bash
# ShanShell AI 一键验收脚本
# 用法: bash tests/manual_check.sh
# 所有测试为字符串分析，不执行任何危险命令。

set +e
cd "$(dirname "$0")/.."
PASS=0
FAIL=0

green()  { echo -e "\033[32m$1\033[0m"; }
red()    { echo -e "\033[31m$1\033[0m"; }
yellow() { echo -e "\033[33m$1\033[0m"; }
bold()   { echo -e "\033[1m$1\033[0m"; }

check_pipe() {
    local name="$1" expect="$2"; shift 2
    local actual
    actual=$("$@" 2>&1)
    if echo "$actual" | python3 -c "$expect" 2>/dev/null; then
        ((PASS++))
        green "  [PASS] $name"
    else
        ((FAIL++))
        red "  [FAIL] $name"
        yellow "    预期包含: $expect"
        echo "    实际输出: $actual"
    fi
}

check_ok() {
    local name="$1"; shift
    if "$@" &>/dev/null; then
        ((PASS++))
        green "  [PASS] $name"
    else
        ((FAIL++))
        red "  [FAIL] $name"
    fi
}

bold "================================================="
bold "  ShanShell AI 一键验收脚本"
bold "================================================="
echo ""

# 1. 单元测试
bold "1. 单元测试 (python3 -m unittest discover -s tests)"
python3 -m unittest discover -s tests 2>&1
echo ""

# 2. Doctor
bold "2. 健康检查 (shansh doctor)"
python3 -m shansh.cli doctor 2>&1
echo ""

# 3. CLI 功能测试
bold "3. CLI 功能测试"

check_pipe "git st → git status" \
    "import sys,json; r=json.loads(sys.stdin.read()); assert r['replacement']=='git status'" \
    python3 -m shansh.cli suggest --buffer "git st" --cwd .

check_pipe "git co → 3 候选 (commit/checkout/clone)" \
    "import sys,json; r=json.loads(sys.stdin.read()); assert r['mode']=='completion'; cmds=[c['cmd'] for c in r['candidates']]; assert 'git commit' in cmds and 'git checkout' in cmds and 'git clone' in cmds" \
    python3 -m shansh.cli suggest --buffer "git co" --cwd .

check_pipe "gti statsu → git status (纠错)" \
    "import sys,json; r=json.loads(sys.stdin.read()); assert r['replacement']=='git status'" \
    python3 -m shansh.cli suggest --buffer "gti statsu" --cwd .

check_pipe "查看磁盘空间 → df -h (NL2CMD)" \
    "import sys,json; r=json.loads(sys.stdin.read()); assert r['replacement']=='df -h'" \
    python3 -m shansh.cli suggest --buffer "查看磁盘空间" --cwd .

check_pipe "apt install nginx → sudo dnf install nginx (发行版适配)" \
    "import sys,json; r=json.loads(sys.stdin.read()); assert 'sudo dnf install' in r['replacement']" \
    python3 -m shansh.cli suggest --buffer "apt install nginx" --cwd .

echo ""

# 4. 风险检测测试
bold "4. 风险检测测试 (字符串分析，不执行)"

check_pipe "rm -rf / → RISK=high" \
    "import sys,json; r=json.loads(sys.stdin.read()); assert r['risk']=='high'" \
    python3 -m shansh.cli risk --cmd "rm -rf /"

check_pipe "dd if=/dev/zero of=/dev/sda → RISK=high" \
    "import sys,json; r=json.loads(sys.stdin.read()); assert r['risk']=='high'" \
    python3 -m shansh.cli risk --cmd "dd if=/dev/zero of=/dev/sda"

check_pipe ":(){ :|:& };: (fork bomb) → RISK=high" \
    "import sys,json; r=json.loads(sys.stdin.read()); assert r['risk']=='high'" \
    python3 -m shansh.cli risk --cmd ":(){ :|:& };:"

check_pipe "ls -la → RISK=low" \
    "import sys,json; r=json.loads(sys.stdin.read()); assert r['risk']=='low'" \
    python3 -m shansh.cli risk --cmd "ls -la"

check_pipe "chmod 777 test.sh → RISK=medium" \
    "import sys,json; r=json.loads(sys.stdin.read()); assert r['risk']=='medium'" \
    python3 -m shansh.cli risk --cmd "chmod 777 test.sh"

echo ""

# 5. 配置管理测试
bold "5. 配置管理测试"

check_ok "config get llm.mode" \
    python3 -m shansh.cli config get llm.mode

check_ok "config set llm.mode rules_only" \
    python3 -m shansh.cli config set llm.mode rules_only

echo ""

# 6. Render 测试
bold "6. Render 测试"

check_ok "render gti statsu" \
    python3 -m shansh.cli render --buffer "gti statsu" --cwd .

check_ok "render apt install nginx" \
    python3 -m shansh.cli render --buffer "apt install nginx" --cwd .

echo ""

# 7. Shell 模式测试
bold "7. Shell 模式测试"

check_ok "suggest-shell — KEY=VALUE 输出包含 MODE=" \
    bash -c 'python3 -m shansh.cli suggest-shell --buffer "git st" --cwd . 2>&1 | grep -q "^MODE="'

check_ok "risk-shell — 输出包含 RISK=high" \
    bash -c 'python3 -m shansh.cli risk-shell --cmd "rm -rf /" 2>&1 | grep -q "^RISK=high"'

echo ""

# 总结
bold "================================================="
TOTAL=$((PASS + FAIL))
bold "  测试结果: ${PASS}/${TOTAL} 通过"
if [[ $FAIL -gt 0 ]]; then
    red "  失败: ${FAIL}"
    exit 1
else
    green "  全部通过！"
fi
bold "================================================="
