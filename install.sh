#!/usr/bin/env bash
# ShanShell AI 安装脚本
#
# 用法: bash install.sh
# 安装后: exec zsh 或 source ~/.zshrc

set -e

SHANSH_ROOT="$(cd "$(dirname "$0")" && pwd)"
ZSHRC="${HOME}/.zshrc"
CONFIG_DIR="${HOME}/.config/shansh"
CONFIG_FILE="${CONFIG_DIR}/config.json"
DEFAULT_CONFIG='{
  "llm": {
    "mode": "rules_only"
  },
  "remote": {
    "provider": "openai_compatible",
    "base_url": "https://api.deepseek.com/v1",
    "model": "deepseek-chat",
    "api_key_env": "SHANSH_API_KEY",
    "timeout": 5
  },
  "privacy": {
    "send_cwd": true,
    "send_os_info": true,
    "send_history": false
  }
}'

SHANSH_BLOCK_START="# >>> ShanShell AI >>>"
SHANSH_BLOCK_END="# <<< ShanShell AI <<<"

echo "========================================="
echo "  ShanShell AI 安装脚本"
echo "========================================="
echo ""

if [[ ! -f "${SHANSH_ROOT}/shell/shansh.zsh" ]]; then
    echo "[ERROR] 请在 ShanShell AI 项目根目录下运行此脚本" >&2
    exit 1
fi

if ! command -v python3 &>/dev/null; then
    echo "[ERROR] 未找到 python3，请先安装 Python 3.6+" >&2
    exit 1
fi
echo "[OK] python3 found: $(python3 --version)"

if ! command -v zsh &>/dev/null; then
    echo "[WARN] 未找到 zsh。ShanShell AI 需要 Zsh 才能运行。"
    echo "      请使用包管理器安装 zsh:"
    echo "      sudo dnf install zsh    (openEuler/Fedora)"
    echo "      sudo apt install zsh     (Ubuntu/Debian)"
    echo "      安装完成后重新运行: bash install.sh"
    exit 0
fi
echo "[OK] zsh found: $(zsh --version 2>&1 | head -1)"

echo ""
echo "[*] 创建配置目录: ${CONFIG_DIR}"
mkdir -p "${CONFIG_DIR}"

if [[ ! -f "${CONFIG_FILE}" ]]; then
    echo "${DEFAULT_CONFIG}" > "${CONFIG_FILE}"
    echo "[OK] 写入默认配置: ${CONFIG_FILE}"
else
    echo "[OK] 配置文件已存在，保留: ${CONFIG_FILE}"
fi

SHANSH_BLOCK="${SHANSH_BLOCK_START}
export SHANSH_ROOT=\"${SHANSH_ROOT}\"
export PYTHONPATH=\"${SHANSH_ROOT}\${PYTHONPATH:+:\${PYTHONPATH}}\"
source \"${SHANSH_ROOT}/shell/shansh.zsh\"
${SHANSH_BLOCK_END}"

echo ""
if [[ ! -f "${ZSHRC}" ]]; then
    echo "[*] 创建 ${ZSHRC} 并写入 ShanShell 加载块"
    echo "${SHANSH_BLOCK}" > "${ZSHRC}"
    echo "[OK] 写入完成"
else
    BACKUP="${ZSHRC}.shansh.bak.$(date +%Y%m%d%H%M%S)"
    cp "${ZSHRC}" "${BACKUP}"
    echo "[OK] 已备份 ~/.zshrc -> ${BACKUP}"

    if grep -q "${SHANSH_BLOCK_START}" "${ZSHRC}"; then
        echo "[*] 检测到已有 ShanShell 配置块，正在替换..."
        TMPFILE=$(mktemp)
        awk "/^${SHANSH_BLOCK_START//\//\\/}/{flag=1; next} /^${SHANSH_BLOCK_END//\//\\/}/{flag=0; next} !flag" "${ZSHRC}" | sed '/^$/N;/^\n$/d' > "${TMPFILE}"
        echo "" >> "${TMPFILE}"
        echo "${SHANSH_BLOCK}" >> "${TMPFILE}"
        mv "${TMPFILE}" "${ZSHRC}"
        echo "[OK] 配置块已更新"
    else
        echo "[*] 追加 ShanShell 配置块到 ~/.zshrc..."
        echo "" >> "${ZSHRC}"
        echo "${SHANSH_BLOCK}" >> "${ZSHRC}"
        echo "[OK] 配置块已追加"
    fi
fi

echo ""
echo "========================================="
echo "  ShanShell AI 安装完成！"
echo "========================================="
echo ""
echo "  下一步 — 加载 ShanShell:"
echo "    exec zsh"
echo "    或"
echo "    source ~/.zshrc"
echo ""
echo "  使用方式:"
echo "    Ctrl-T       开关自动建议（推荐开启，打字时自动弹出）"
echo "    Ctrl-G       手动触发建议"
echo "    Tab          接受建议"
echo "    Shift+Tab    切换候选"
echo "    Esc          清除建议"
echo "    Enter        执行命令（含风险检查）"
echo ""
echo "  配置大模型 (可选):"
echo "    export SHANSH_API_KEY=\"sk-your-key-here\""
echo "    shansh config set llm.mode remote"
echo ""
echo "  验证安装:"
echo "    python3 -m shansh.cli doctor"
echo ""
echo "  卸载:"
echo "    bash ${SHANSH_ROOT}/uninstall.sh"
echo ""
