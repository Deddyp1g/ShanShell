#!/usr/bin/env bash
# ShanShell AI 卸载脚本
#
# 用法: bash uninstall.sh
# 仅删除 .zshrc 中的 ShanShell 标记块，不删除项目代码和历史文件。

set -e

SHANSH_ROOT="$(cd "$(dirname "$0")" && pwd)"
ZSHRC="${HOME}/.zshrc"
SHANSH_BLOCK_START="# >>> ShanShell AI >>>"
SHANSH_BLOCK_END="# <<< ShanShell AI <<<"

echo "========================================="
echo "  ShanShell AI 卸载脚本"
echo "========================================="
echo ""

if [[ ! -f "${ZSHRC}" ]]; then
    echo "[OK] 未找到 ~/.zshrc，无需清理。"
    echo ""
    echo "========================================="
    echo "  卸载完成"
    echo "========================================="
    echo ""
    echo "  注意: 项目代码和历史文件未被删除:"
    echo "    - 项目代码: ${SHANSH_ROOT}"
    echo "    - 配置文件: ~/.config/shansh/config.json"
    echo "    如需彻底删除请手动执行:"
    echo "      rm -rf ${SHANSH_ROOT}"
    echo "      rm -rf ~/.config/shansh"
    exit 0
fi

BACKUP="${ZSHRC}.shansh.uninstall.bak.$(date +%Y%m%d%H%M%S)"
cp "${ZSHRC}" "${BACKUP}"
echo "[OK] 已备份 ~/.zshrc -> ${BACKUP}"

if grep -q "${SHANSH_BLOCK_START}" "${ZSHRC}"; then
    TMPFILE=$(mktemp)
    awk "/^${SHANSH_BLOCK_START//\//\\/}/{flag=1; next} /^${SHANSH_BLOCK_END//\//\\/}/{flag=0; next} !flag" "${ZSHRC}" | sed '/^$/N;/^\n$/d' > "${TMPFILE}"
    mv "${TMPFILE}" "${ZSHRC}"
    echo "[OK] 已删除 ShanShell 配置块"
else
    echo "[OK] ~/.zshrc 中未找到 ShanShell 配置块，跳过"
fi

echo ""
echo "========================================="
echo "  卸载完成"
echo "========================================="
echo ""
echo "  已从 ~/.zshrc 移除 ShanShell 加载块。"
echo "  以下内容未被删除:"
echo "    - 项目代码: ${SHANSH_ROOT}"
echo "    - 配置文件: ~/.config/shansh/config.json"
echo ""
echo "  如需彻底删除项目:"
echo "    rm -rf ${SHANSH_ROOT}"
echo "    rm -rf ~/.config/shansh"
echo ""
echo "  如需重新加载 shell 生效:"
echo "    exec zsh"
echo ""
