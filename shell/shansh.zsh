# ShanShell AI — Zsh 前端 (Phase 4 Copilot 终端渲染增强)
#
# 用法:
# cd shansh-ai
# zsh
# source shell/shansh.zsh

if [[ -z "$ZSH_VERSION" ]]; then
    echo "[ShanShell] 此脚本仅支持 Zsh，当前 shell 不支持" >&2
    return 1
fi

zmodload zsh/system 2>/dev/null

# ============================== 全局变量 ==============================
export SHANSH_ROOT="${SHANSH_ROOT:-/root/shansh-ai}"
SHANSH_LAST_REPLACEMENT=""
SHANSH_LAST_EXPLANATION=""
SHANSH_LAST_RISK="low"
SHANSH_LAST_GHOST=""
SHANSH_CANDIDATE_INDEX=0
SHANSH_LAST_DIAG_LINE=""
export SHANSH_AUTO_SUGGEST="${SHANSH_AUTO_SUGGEST:-1}"

_SHANSH_CANDIDATES=()
_SHANSH_CANDIDATE_COUNT=0
_SHANSH_CANDIDATE_EXPLANATIONS=()
_SHANSH_DIAGS=()
SHANSH_AUTO_LAST_TIME=0

SHANSH_WAITING_LLM=0
SHANSH_PENDING_BUFFER=""
SHANSH_PENDING_CWD=""
SHANSH_LAST_KEYSTROKE_TIME=0
SHANSH_LLM_BG_PID=""
SHANSH_LLM_FIFO="/tmp/shansh_llm_fifo_$$"
SHANSH_LLM_RESULT_FILE="/tmp/shansh_llm_result_$$"
SHANSH_LLM_FD=""

_shansh_llm_fifo_reopen() {
    [[ -n "$SHANSH_LLM_FD" ]] && { zle -F "$SHANSH_LLM_FD" '' 2>/dev/null; exec {SHANSH_LLM_FD}>&- 2>/dev/null; }
    [[ -p "$SHANSH_LLM_FIFO" ]] || mkfifo "$SHANSH_LLM_FIFO" 2>/dev/null
    exec {SHANSH_LLM_FD}<>"$SHANSH_LLM_FIFO"
    zle -F "$SHANSH_LLM_FD" _shansh_llm_on_result
}

_shansh_llm_cleanup() {
    _shansh_kill_llm_bg
    [[ -n "$SHANSH_LLM_FD" ]] && { zle -F "$SHANSH_LLM_FD" '' 2>/dev/null; exec {SHANSH_LLM_FD}>&- 2>/dev/null; }
    [[ -p "$SHANSH_LLM_FIFO" ]] && rm -f "$SHANSH_LLM_FIFO"
    [[ -f "$SHANSH_LLM_RESULT_FILE" ]] && rm -f "$SHANSH_LLM_RESULT_FILE"
}

_shansh_llm_on_result() {
    local fd=$1 signal
    sysread -i $fd signal 2>/dev/null

    if [[ "$SHANSH_WAITING_LLM" != "1" ]]; then
        return
    fi
    SHANSH_WAITING_LLM=0

    local output
    [[ -s "$SHANSH_LLM_RESULT_FILE" ]] || { _shansh_llm_fifo_reopen; return; }
    output=$(<"$SHANSH_LLM_RESULT_FILE" 2>/dev/null)
    [[ -z "$output" ]] && { _shansh_llm_fifo_reopen; return; }
    : > "$SHANSH_LLM_RESULT_FILE"

    local parsed mode replacement explanation risk source confidence
    parsed=$(_shansh_parse_kv <<< "$output")
    eval "$parsed"

    mode="${_shansh_parsed_MODE:-none}"
    replacement="${_shansh_parsed_REPLACEMENT:-}"
    explanation="${_shansh_parsed_EXPLANATION:-}"
    risk="${_shansh_parsed_RISK:-low}"
    source="${_shansh_parsed_SOURCE:-nl2cmd}"
    confidence="${_shansh_parsed_CONFIDENCE:-0.0}"

    if [[ "$mode" != "none" && -n "$replacement" ]]; then
        SHANSH_LAST_REPLACEMENT="$replacement"
        SHANSH_LAST_EXPLANATION="$explanation"
        SHANSH_LAST_RISK="$risk"
        SHANSH_CANDIDATE_INDEX=0
        _shansh_parse_candidates "$output"

        local suggest_line
        suggest_line=$(_shansh_build_suggest_line "$replacement" "$explanation" "$source" "$confidence" "$risk" "$_SHANSH_CANDIDATE_COUNT")
        zle -M "$suggest_line"
    fi

    _shansh_llm_fifo_reopen
}

# ============================== 历史记录 ==============================
_shansh_record_history() {
    local cmd="$1"
    local exit_code="${2:-0}"
    (cd "${SHANSH_ROOT}" && python3 -c "
from shansh.stats import record_command
record_command('${cmd//\'/\'\\\'\'}', exit_code=${exit_code}, cwd='${PWD//\'/\'\\\'\'}')
" 2>/dev/null)
}

# ============================== 解析 shell 输出 ==============================
_shansh_parse_kv() {
    while IFS='=' read -r key value; do
        [[ -z "$key" ]] && continue
        printf "_shansh_parsed_%s=%q\n" "$key" "$value"
    done
}

_shansh_parse_candidates() {
    local output="$1"
    _SHANSH_CANDIDATES=()
    _SHANSH_CANDIDATE_EXPLANATIONS=()

    local count
    count=$(echo "$output" | grep "^CANDIDATE_COUNT=" | cut -d= -f2)
    [[ -z "$count" || "$count" -le 0 ]] && { _SHANSH_CANDIDATE_COUNT=0; return 0; }

    local i cmd expl
    for ((i=0; i<count; i++)); do
        cmd=$(echo "$output" | grep "^CANDIDATE_${i}_CMD=" | cut -d= -f2-)
        expl=$(echo "$output" | grep "^CANDIDATE_${i}_EXPLANATION=" | cut -d= -f2-)
        _SHANSH_CANDIDATES+=("${cmd:-}")
        _SHANSH_CANDIDATE_EXPLANATIONS+=("${expl:-}")
    done
    _SHANSH_CANDIDATE_COUNT=$count
}

_shansh_parse_diagnostics() {
    local output="$1" count
    _SHANSH_DIAGS=()
    count=$(echo "$output" | grep "^DIAGNOSTIC_COUNT=" | cut -d= -f2)
    [[ -z "$count" || "$count" -le 0 ]] && return 0
    local i=0 start end severity message
    for ((i=0; i<count; i++)); do
        start=$(echo "$output" | grep "^DIAGNOSTIC_${i}_START=" | cut -d= -f2-)
        end=$(echo "$output" | grep "^DIAGNOSTIC_${i}_END=" | cut -d= -f2-)
        severity=$(echo "$output" | grep "^DIAGNOSTIC_${i}_SEVERITY=" | cut -d= -f2-)
        message=$(echo "$output" | grep "^DIAGNOSTIC_${i}_MESSAGE=" | cut -d= -f2-)
        _SHANSH_DIAGS+=("${start:-0}:${end:-0}:${severity:-info}:${message:-}")
    done
}

_shansh_build_diag_line() {
    local buffer="$1"
    local max_end=0
    local diag line
    for diag in "${_SHANSH_DIAGS[@]}"; do
        local end="${diag#*:}"
        end="${end%%:*}"
        [[ $end -gt $max_end ]] && max_end=$end
    done
    [[ $max_end -lt ${#buffer} ]] && max_end=${#buffer}

    local markers=""
    local i
    for ((i=0; i<max_end; i++)); do
        markers+=" "
    done

    for diag in "${_SHANSH_DIAGS[@]}"; do
        local s="${diag%%:*}"
        local rest="${diag#*:}"
        local e="${rest%%:*}"
        rest="${rest#*:}"
        local sev="${rest%%:*}"
        local ch="^"
        [[ "$sev" == "info" ]] && ch="~"
        local j
        for ((j=s; j<e && j<${#buffer}; j++)); do
            markers="${markers:0:$j}${ch}${markers:$((j+1))}"
        done
    done
    echo " ${markers}"
}

# ============================== ANSI 颜色 ==============================
_shansh_ansi_red=$'\e[31m'
_shansh_ansi_yellow=$'\e[33m'
_shansh_ansi_blue=$'\e[34m'
_shansh_ansi_gray=$'\e[90m'
_shansh_ansi_underline=$'\e[4m'
_shansh_ansi_red_bg=$'\e[41;97m'
_shansh_ansi_reset=$'\e[0m'
_shansh_color_supported=1

_shansh_check_color() {
    [[ "$NO_COLOR" == "1" ]] && { _shansh_color_supported=0; return; }
    [[ "$TERM" == "dumb" ]] && { _shansh_color_supported=0; return; }
    [[ "$SHANSH_NO_COLOR" == "1" ]] && { _shansh_color_supported=0; return; }
    _shansh_color_supported=1
}

_shansh_color() {
    [[ $_shansh_color_supported -eq 0 ]] && { echo -n "$1"; return; }
    echo -n "$2$1${_shansh_ansi_reset}"
}

# ============================== UI 辅助函数 ==============================
_shansh_source_label() {
    case "$1" in
        nl2cmd)    echo "AI" ;;
        rules)     echo "规则" ;;
        distro)    echo "适配" ;;
        mock)      echo "内置" ;;
        workflow)  echo "预测" ;;
        completion) echo "补全" ;;
        correction) echo "纠错" ;;
        *)         echo "" ;;
    esac
}

_shansh_render_colored_buffer() {
    local buffer="$1"
    local result=""
    local i diag s e sev
    local -a colors
    for ((i=0; i<${#buffer}; i++)); do
        colors[$i]=""
    done

    for diag in "${_SHANSH_DIAGS[@]}"; do
        s="${diag%%:*}"
        local rest="${diag#*:}"
        e="${rest%%:*}"
        rest="${rest#*:}"
        sev="${rest%%:*}"
        local ansi="${_shansh_ansi_red}"
        [[ "$sev" == "warning" ]] && ansi="${_shansh_ansi_yellow}"
        [[ "$sev" == "info" ]] && ansi="${_shansh_ansi_blue}"
        for ((j=s; j<e && j<${#buffer}; j++)); do
            colors[$j]="$ansi${_shansh_ansi_underline}"
        done
    done

    if [[ $_shansh_color_supported -eq 0 ]]; then
        echo -n "$buffer"
        return
    fi

    for ((i=0; i<${#buffer}; i++)); do
        local ch="${buffer:$i:1}"
        if [[ -n "${colors[$i]}" ]]; then
            echo -n "${colors[$i]}$ch"
        else
            echo -n "$ch"
        fi
    done
    echo -n "${_shansh_ansi_reset}"
}

_shansh_build_suggest_line() {
    local replacement="$1" explanation="$2" source="$3" confidence="$4" risk="$5" count="$6"
    local src_label conf_str risk_label suggest_line

    src_label=$(_shansh_source_label "$source")
    if [[ -n "$confidence" && "$confidence" != "0.0" ]]; then
        conf_str="$(printf '%.0f' "$(echo "$confidence * 100" | bc -l 2>/dev/null || echo 0)")%"
    else
        conf_str=""
    fi

    case "$risk" in
        high)   risk_label=" HIGH RISK" ;;
        medium) risk_label=" MED RISK" ;;
    esac

    if [[ -n "$src_label" ]]; then
        suggest_line="[ShanShell] [${src_label}]"
    else
        suggest_line="[ShanShell]"
    fi
    [[ -n "$conf_str" ]] && suggest_line+=" ${conf_str}"
    suggest_line+=" → ${replacement}"
    [[ -n "$explanation" ]] && suggest_line+=" | ${explanation}"
    if [[ ${count:-0} -gt 1 ]]; then
        if [[ -n "$src_label" ]]; then
            suggest_line="[ShanShell] [1/${count}] [${src_label}]"
        else
            suggest_line="[ShanShell] [1/${count}]"
        fi
        [[ -n "$conf_str" ]] && suggest_line+=" ${conf_str}"
        suggest_line+=" → ${replacement}"
        [[ -n "$explanation" ]] && suggest_line+=" | ${explanation}"
    fi
    [[ -n "$risk_label" ]] && suggest_line+="${risk_label}"

    echo "$suggest_line"
}
_shansh_emit_diagnostics() {
    local buffer="$1"
    if [[ ${#_SHANSH_DIAGS[@]} -eq 0 ]]; then
        return
    fi
    if [[ $_shansh_color_supported -eq 1 ]]; then
        echo ""
        _shansh_render_colored_buffer "$buffer"
        echo ""
    fi
    echo "$(_shansh_build_diag_line "$buffer")"
}

shansh-suggest() {
    local buffer="$BUFFER"
    local cwd="$PWD"
    local output mode replacement ghost explanation risk source confidence

    output=$(cd "${SHANSH_ROOT}" && python3 -m shansh.cli suggest-shell --buffer "$buffer" --cwd "$cwd" 2>/dev/null)
    local rc=$?

    if [[ $rc -ne 0 ]] || [[ -z "$output" ]]; then
        zle -M "[ShanShell] 后端调用失败"
        return 1
    fi

    local parsed
    parsed=$(_shansh_parse_kv <<< "$output")
    eval "$parsed"

    mode="${_shansh_parsed_MODE:-none}"
    replacement="${_shansh_parsed_REPLACEMENT:-}"
    ghost="${_shansh_parsed_GHOST_TEXT:-}"
    explanation="${_shansh_parsed_EXPLANATION:-}"
    risk="${_shansh_parsed_RISK:-low}"
    source="${_shansh_parsed_SOURCE:-}"
    confidence="${_shansh_parsed_CONFIDENCE:-0.0}"

    if [[ "$mode" == "none" ]]; then
        SHANSH_LAST_REPLACEMENT=""
        SHANSH_LAST_EXPLANATION=""
        SHANSH_LAST_RISK="low"
        SHANSH_LAST_GHOST=""
        SHANSH_LAST_DIAG_LINE=""
        return 1
    fi

    SHANSH_LAST_REPLACEMENT="$replacement"
    SHANSH_LAST_EXPLANATION="$explanation"
    SHANSH_LAST_RISK="$risk"
    SHANSH_LAST_GHOST="$ghost"
    SHANSH_CANDIDATE_INDEX=0

    _shansh_parse_candidates "$output"
    _shansh_parse_diagnostics "$output"

    SHANSH_LAST_DIAG_LINE="$(_shansh_build_diag_line "$buffer")"

    local suggest_line
    suggest_line=$(_shansh_build_suggest_line "$replacement" "$explanation" "$source" "$confidence" "$risk" "$_SHANSH_CANDIDATE_COUNT")

    _shansh_emit_diagnostics "$buffer"
    zle -M "$suggest_line"
}

# ============================== 接受建议 ==============================
shansh-accept() {
    if [[ -z "$SHANSH_LAST_REPLACEMENT" ]]; then
        zle expand-or-complete
        return
    fi

    if [[ "$SHANSH_LAST_RISK" == "high" ]]; then
        zle -M "[ShanShell] ⚠ 高风险建议禁止自动接受"
        return 1
    fi

    BUFFER="$SHANSH_LAST_REPLACEMENT"
    CURSOR=${#BUFFER}

    SHANSH_LAST_REPLACEMENT=""
    SHANSH_LAST_EXPLANATION=""
    SHANSH_LAST_RISK="low"
    SHANSH_LAST_GHOST=""
    SHANSH_LAST_DIAG_LINE=""
    _SHANSH_CANDIDATES=()
    _SHANSH_CANDIDATE_EXPLANATIONS=()
    _SHANSH_CANDIDATE_COUNT=0
    _SHANSH_DIAGS=()
}

# ============================== 清除建议 ==============================
shansh-clear() {
    SHANSH_LAST_REPLACEMENT=""
    SHANSH_LAST_EXPLANATION=""
    SHANSH_LAST_RISK="low"
    SHANSH_LAST_GHOST=""
    SHANSH_CANDIDATE_INDEX=0
    SHANSH_LAST_DIAG_LINE=""
    _SHANSH_CANDIDATES=()
    _SHANSH_CANDIDATE_EXPLANATIONS=()
    _SHANSH_CANDIDATE_COUNT=0
    _SHANSH_DIAGS=()
    _shansh_kill_llm_bg
    SHANSH_WAITING_LLM=0
}

# ============================== Enter 拦截 (含历史记录) ==============================
shansh-accept-line() {
    local buffer="$BUFFER"
    local output risk explanation ansi_warning

    _shansh_kill_llm_bg
    SHANSH_WAITING_LLM=0

    if [[ -z "${buffer// /}" ]]; then
        zle accept-line
        return
    fi

    output=$(cd "${SHANSH_ROOT}" && python3 -m shansh.cli risk-shell --cmd "$buffer" 2>/dev/null)
    local rc=$?

    if [[ $rc -ne 0 ]] || [[ -z "$output" ]]; then
        _shansh_record_history "$buffer" 0
        zle accept-line
        return
    fi

    local parsed
    parsed=$(_shansh_parse_kv <<< "$output")
    eval "$parsed"

    risk="${_shansh_parsed_RISK:-low}"
    explanation="${_shansh_parsed_EXPLANATION:-}"
    ansi_warning="${_shansh_parsed_ANSI_WARNING:-}"

    if [[ "$risk" == "high" ]]; then
        echo ""
        if [[ $_shansh_color_supported -eq 1 ]]; then
            echo -e "${_shansh_ansi_red_bg} HIGH RISK: ${explanation} ${_shansh_ansi_reset}"
        else
            echo "HIGH RISK: ${explanation}"
        fi
        zle -M "[ShanShell] 高风险命令已拦截: ${explanation}"
        zle send-break
        return 1
    fi

    if [[ "$risk" == "medium" ]]; then
        if [[ $_shansh_color_supported -eq 1 ]]; then
            echo -e "  ${_shansh_ansi_yellow}MEDIUM RISK: ${explanation}${_shansh_ansi_reset}"
        else
            echo "  MEDIUM RISK: ${explanation}"
        fi
        zle -M "[ShanShell] 中风险提示: ${explanation} (已放行)"
    fi

    _shansh_record_history "$buffer" 0
    zle accept-line
}

# ============================== 候选切换 ==============================
shansh-next-candidate() {
    if [[ $_SHANSH_CANDIDATE_COUNT -le 1 ]]; then
        return
    fi

    SHANSH_CANDIDATE_INDEX=$(( (SHANSH_CANDIDATE_INDEX + 1) % _SHANSH_CANDIDATE_COUNT ))
    local idx=$SHANSH_CANDIDATE_INDEX
    local cmd="${_SHANSH_CANDIDATES[$idx]}"
    local expl="${_SHANSH_CANDIDATE_EXPLANATIONS[$idx]:-}"

    SHANSH_LAST_REPLACEMENT="$cmd"
    SHANSH_LAST_EXPLANATION="$expl"

    local disp_idx=$((idx + 1))
    zle -M "[ShanShell] [${disp_idx}/${_SHANSH_CANDIDATE_COUNT}] → ${cmd} | ${expl}"
}

# ============================== 自动建议 ==============================

shansh-auto-toggle() {
    if [[ "$SHANSH_AUTO_SUGGEST" == "1" ]]; then
        SHANSH_AUTO_SUGGEST=0
        shansh-clear
        zle -M "[ShanShell] 自动建议已关闭 (手动模式: Ctrl-G 触发)"
    else
        SHANSH_AUTO_SUGGEST=1
        zle -M "[ShanShell] 自动建议已开启 (打字时自动弹出)"
        if [[ -n "$BUFFER" ]]; then
            zle shansh-suggest
        fi
    fi
}

_shansh_kill_llm_bg() {
    if [[ -n "$SHANSH_LLM_BG_PID" ]]; then
        kill "$SHANSH_LLM_BG_PID" 2>/dev/null
        SHANSH_LLM_BG_PID=""
    fi
}

_shansh_start_llm_bg() {
    local buffer="$1" cwd="$2"
    _shansh_kill_llm_bg
    : > "$SHANSH_LLM_RESULT_FILE"
    (
        sleep 1
        cd "${SHANSH_ROOT}" && python3 -m shansh.cli suggest-shell --buffer "$buffer" --cwd "$cwd" 2>/dev/null > "$SHANSH_LLM_RESULT_FILE"
        echo "x" > "$SHANSH_LLM_FIFO"
    ) &!
    SHANSH_LLM_BG_PID=$!
}

_shansh_auto_suggest_on_insert() {
    zle .self-insert

    if [[ "$SHANSH_AUTO_SUGGEST" != "1" ]] || [[ -z "${BUFFER// /}" ]]; then
        return
    fi

    SHANSH_LAST_KEYSTROKE_TIME=$EPOCHREALTIME

    local output
    output=$(cd "${SHANSH_ROOT}" && python3 -m shansh.cli suggest-rules-shell --buffer "$BUFFER" --cwd "$PWD" 2>/dev/null) || return

    local parsed mode replacement explanation source confidence
    parsed=$(_shansh_parse_kv <<< "$output")
    eval "$parsed"

    mode="${_shansh_parsed_MODE:-none}"
    replacement="${_shansh_parsed_REPLACEMENT:-}"
    explanation="${_shansh_parsed_EXPLANATION:-}"
    source="${_shansh_parsed_SOURCE:-rules}"
    confidence="${_shansh_parsed_CONFIDENCE:-0.0}"

    if [[ "$mode" != "none" && -n "$replacement" ]]; then
        _shansh_kill_llm_bg
        SHANSH_WAITING_LLM=0
        SHANSH_LAST_REPLACEMENT="$replacement"
        SHANSH_LAST_EXPLANATION="$explanation"
        SHANSH_CANDIDATE_INDEX=0
        _shansh_parse_candidates "$output"
        local risk="${_shansh_parsed_RISK:-low}"
        local suggest_line
        suggest_line=$(_shansh_build_suggest_line "$replacement" "$explanation" "$source" "$confidence" "$risk" "$_SHANSH_CANDIDATE_COUNT")
        zle -M "$suggest_line"
        return
    fi

    SHANSH_WAITING_LLM=1
    SHANSH_PENDING_BUFFER="$BUFFER"
    SHANSH_PENDING_CWD="$PWD"
    _shansh_start_llm_bg "$BUFFER" "$PWD"
}

_shansh_auto_suggest_on_delete() {
    zle .backward-delete-char

    if [[ "$SHANSH_AUTO_SUGGEST" != "1" ]]; then
        return
    fi
    if [[ -z "${BUFFER// /}" ]]; then
        _shansh_kill_llm_bg
        SHANSH_WAITING_LLM=0
        shansh-clear
        return
    fi

    SHANSH_LAST_KEYSTROKE_TIME=$EPOCHREALTIME

    local output
    output=$(cd "${SHANSH_ROOT}" && python3 -m shansh.cli suggest-rules-shell --buffer "$BUFFER" --cwd "$PWD" 2>/dev/null) || return

    local parsed mode replacement explanation source confidence
    parsed=$(_shansh_parse_kv <<< "$output")
    eval "$parsed"

    mode="${_shansh_parsed_MODE:-none}"
    replacement="${_shansh_parsed_REPLACEMENT:-}"
    explanation="${_shansh_parsed_EXPLANATION:-}"
    source="${_shansh_parsed_SOURCE:-rules}"
    confidence="${_shansh_parsed_CONFIDENCE:-0.0}"

    if [[ "$mode" != "none" && -n "$replacement" ]]; then
        _shansh_kill_llm_bg
        SHANSH_WAITING_LLM=0
        SHANSH_LAST_REPLACEMENT="$replacement"
        SHANSH_LAST_EXPLANATION="$explanation"
        SHANSH_CANDIDATE_INDEX=0
        _shansh_parse_candidates "$output"
        local risk="${_shansh_parsed_RISK:-low}"
        local suggest_line
        suggest_line=$(_shansh_build_suggest_line "$replacement" "$explanation" "$source" "$confidence" "$risk" "$_SHANSH_CANDIDATE_COUNT")
        zle -M "$suggest_line"
        return
    fi

    SHANSH_WAITING_LLM=1
    SHANSH_PENDING_BUFFER="$BUFFER"
    SHANSH_PENDING_CWD="$PWD"
    _shansh_start_llm_bg "$BUFFER" "$PWD"
}

# ============================== 注册 Widget ==============================
zle -N shansh-suggest
zle -N shansh-accept
zle -N shansh-clear
zle -N shansh-accept-line
zle -N shansh-next-candidate
zle -N shansh-auto-toggle
zle -N self-insert _shansh_auto_suggest_on_insert
zle -N backward-delete-char _shansh_auto_suggest_on_delete

# ============================== 按键绑定 ==============================
bindkey '^G' shansh-suggest
bindkey '^I' shansh-accept
bindkey '^M' shansh-accept-line
bindkey '^T' shansh-auto-toggle

if [[ -n "$terminfo[kcbt]" ]]; then
    bindkey "$terminfo[kcbt]" shansh-next-candidate
else
    bindkey '^[[Z' shansh-next-candidate
fi

bindkey '^[' shansh-clear

# ============================== 加载提示 ==============================
_shansh_llm_fifo_reopen
_shansh_check_color
echo "[ShanShell] loaded. Ctrl-G suggest, Ctrl-T auto, Tab accept, Shift+Tab next, Esc clear, Enter risk-check."
