"""ShanShell AI 命令行入口。

用法:
    python3 -m shansh.cli suggest --buffer "git st" --cwd .
    python3 -m shansh.cli risk --cmd "rm -rf /"
    python3 -m shansh.cli context --buffer "" --cwd .
    python3 -m shansh.cli stats
    python3 -m shansh.cli server
    python3 -m shansh.cli suggest-shell --buffer "git st" --cwd .
    python3 -m shansh.cli risk-shell --cmd "rm -rf /"
    python3 -m shansh.cli render --buffer "gti statsu" --cwd .
    python3 -m shansh.cli config get llm.mode
    python3 -m shansh.cli config set llm.mode remote
    python3 -m shansh.cli doctor
"""

import sys
import json
import argparse
import os

from shansh.models import SuggestResponse, Candidate, Diagnostic
from shansh.context import collect_context
from shansh.completion_engine import CompletionEngine
from shansh.correction_engine import CorrectionEngine
from shansh.workflow_engine import WorkflowEngine
from shansh.risk_engine import RiskEngine
from shansh.ranker import Ranker
from shansh.nl2cmd_engine import NL2CmdEngine
from shansh.render_protocol import RenderEngine, _ansi, ANSI


def _is_chinese_text(text: str) -> bool:
    return any("\u4e00" <= ch <= "\u9fff" for ch in text)


def _build_suggest_result(buffer: str, cwd: str, use_llm: bool = True, lightweight: bool = False) -> dict:
    ctx = collect_context(buffer, cwd, lightweight=lightweight)
    trimmed = buffer.strip()

    if not trimmed:
        workflow_engine = WorkflowEngine()
        wf_candidates = workflow_engine.predict(ctx.get("last_commands", []), ctx)
        if wf_candidates:
            risk_check = RiskEngine().check(wf_candidates[0].cmd)
            return {
                "mode": "workflow",
                "completion_candidates": [],
                "correction_candidates": [],
                "correction_diagnostics": [],
                "correction_replacement": "",
                "workflow_candidates": wf_candidates,
                "top_candidates": [wf_candidates[0]],
                "risk": risk_check["risk"],
            }
        return {
            "mode": "none",
            "completion_candidates": [],
            "correction_candidates": [],
            "correction_diagnostics": [],
            "correction_replacement": "",
            "workflow_candidates": [],
            "top_candidates": [],
            "risk": "low",
        }

    is_nl = _is_chinese_text(trimmed) and not any(
        trimmed.startswith(p) for p in [
            "git ", "dnf ", "systemctl ", "docker ", "pip ", "npm ",
            "python ", "make ", "apt ", "ls ", "chmod ", "chown ",
            "sudo ", "rm ", "dd ", "mkfs", "tar ", "curl ", "wget ",
        ]
    )

    completion_engine = CompletionEngine()
    correction_engine = CorrectionEngine()
    nl_engine = NL2CmdEngine()

    completion_candidates = completion_engine.complete(trimmed, ctx)
    correction_result = correction_engine.correct(trimmed, ctx)
    correction_candidates = correction_result.get("candidates", [])
    correction_diagnostics = correction_result.get("diagnostics", [])
    correction_replacement = correction_result.get("replacement", "")

    if completion_candidates or correction_candidates:
        all_candidates = completion_candidates + correction_candidates
        ranker = Ranker()
        top_candidates = ranker.rank(all_candidates, max_results=3)
        check_target = trimmed
        if correction_replacement:
            check_target = correction_replacement
        risk = RiskEngine().check(check_target)["risk"]
        mode = "completion" if completion_candidates else "correction"
        return {
            "mode": mode,
            "completion_candidates": completion_candidates,
            "correction_candidates": correction_candidates,
            "correction_diagnostics": correction_diagnostics,
            "correction_replacement": correction_replacement,
            "workflow_candidates": [],
            "top_candidates": top_candidates,
            "risk": risk,
        }

    if not use_llm:
        return {
            "mode": "none",
            "completion_candidates": [],
            "correction_candidates": [],
            "correction_diagnostics": [],
            "correction_replacement": "",
            "workflow_candidates": [],
            "top_candidates": [],
            "risk": "low",
        }

    if len(trimmed) >= 2:
        llm_candidates = nl_engine.translate(trimmed, ctx)
        if llm_candidates:
            ranker = Ranker()
            top_candidates = ranker.rank(llm_candidates, max_results=3)
            return {
                "mode": "nl2cmd",
                "completion_candidates": [],
                "correction_candidates": [],
                "correction_diagnostics": [],
                "correction_replacement": "",
                "workflow_candidates": [],
                "top_candidates": top_candidates,
                "risk": "low",
            }

    return {
        "mode": "none",
        "completion_candidates": [],
        "correction_candidates": [],
        "correction_diagnostics": [],
        "correction_replacement": "",
        "workflow_candidates": [],
        "top_candidates": [],
        "risk": "low",
    }


def _cmd_suggest(buffer: str, cwd: str):
    result = _build_suggest_result(buffer, cwd)
    top = result["top_candidates"]
    risk = result["risk"]

    if not top:
        resp = SuggestResponse(
            mode=result["mode"], replacement="", ghost_text="",
            explanation="", confidence=0.0, risk=risk, source="",
            candidates=[], diagnostics=[]
        )
        print(json.dumps(resp.to_dict(), ensure_ascii=False, indent=2))
        return

    best = top[0]
    diags = []
    for d in result.get("correction_diagnostics", []):
        diags.append(d.to_dict() if hasattr(d, "to_dict") else d)

    resp = SuggestResponse(
        mode=result["mode"] if result["mode"] != "none" else "completion",
        replacement=best.cmd,
        ghost_text=best.ghost_text if hasattr(best, "ghost_text") else "",
        explanation=best.explanation if hasattr(best, "explanation") else "",
        confidence=best.confidence if hasattr(best, "confidence") else 0.0,
        risk=risk,
        source=best.source if hasattr(best, "source") else "",
        candidates=[c.to_dict() for c in top],
        diagnostics=diags,
    )
    print(json.dumps(resp.to_dict(), ensure_ascii=False, indent=2))


def _cmd_suggest_shell(buffer: str, cwd: str):
    result = _build_suggest_result(buffer, cwd, use_llm=True)
    top = result["top_candidates"]
    mode = result["mode"]

    if not top:
        print("MODE=none")
        return

    best = top[0]

    print(f"MODE={mode}")
    print(f"REPLACEMENT={best.cmd}")
    print(f"GHOST_TEXT={best.ghost_text if hasattr(best, 'ghost_text') else ''}")
    print(f"EXPLANATION={best.explanation if hasattr(best, 'explanation') else ''}")
    print(f"RISK={result['risk']}")
    print(f"SOURCE={best.source if hasattr(best, 'source') else ''}")
    print(f"CONFIDENCE={best.confidence if hasattr(best, 'confidence') else 0.0}")

    print(f"CANDIDATE_COUNT={len(top)}")
    for i, c in enumerate(top):
        print(f"CANDIDATE_{i}_CMD={c.cmd}")
        print(f"CANDIDATE_{i}_GHOST={c.ghost_text if hasattr(c, 'ghost_text') else ''}")
        print(f"CANDIDATE_{i}_EXPLANATION={c.explanation if hasattr(c, 'explanation') else ''}")
        print(f"CANDIDATE_{i}_CONFIDENCE={c.confidence if hasattr(c, 'confidence') else 0.0}")

    diags = result.get("correction_diagnostics", [])
    print(f"DIAGNOSTIC_COUNT={len(diags)}")
    for i, d in enumerate(diags):
        print(f"DIAGNOSTIC_{i}_START={d.start if hasattr(d, 'start') else 0}")
        print(f"DIAGNOSTIC_{i}_END={d.end if hasattr(d, 'end') else 0}")
        print(f"DIAGNOSTIC_{i}_SEVERITY={d.severity if hasattr(d, 'severity') else 'info'}")
        print(f"DIAGNOSTIC_{i}_MESSAGE={d.message if hasattr(d, 'message') else ''}")


def _cmd_suggest_rules_shell(buffer: str, cwd: str):
    result = _build_suggest_result(buffer, cwd, use_llm=False, lightweight=True)
    top = result["top_candidates"]
    mode = result["mode"]

    if not top:
        print("MODE=none")
        return

    best = top[0]

    print(f"MODE={mode}")
    print(f"REPLACEMENT={best.cmd}")
    print(f"GHOST_TEXT={best.ghost_text if hasattr(best, 'ghost_text') else ''}")
    print(f"EXPLANATION={best.explanation if hasattr(best, 'explanation') else ''}")
    print(f"RISK={result['risk']}")
    print(f"SOURCE={best.source if hasattr(best, 'source') else ''}")
    print(f"CONFIDENCE={best.confidence if hasattr(best, 'confidence') else 0.0}")

    print(f"CANDIDATE_COUNT={len(top)}")
    for i, c in enumerate(top):
        print(f"CANDIDATE_{i}_CMD={c.cmd}")
        print(f"CANDIDATE_{i}_GHOST={c.ghost_text if hasattr(c, 'ghost_text') else ''}")
        print(f"CANDIDATE_{i}_EXPLANATION={c.explanation if hasattr(c, 'explanation') else ''}")
        print(f"CANDIDATE_{i}_CONFIDENCE={c.confidence if hasattr(c, 'confidence') else 0.0}")

    diags = result.get("correction_diagnostics", [])
    print(f"DIAGNOSTIC_COUNT={len(diags)}")
    for i, d in enumerate(diags):
        print(f"DIAGNOSTIC_{i}_START={d.start if hasattr(d, 'start') else 0}")
        print(f"DIAGNOSTIC_{i}_END={d.end if hasattr(d, 'end') else 0}")
        print(f"DIAGNOSTIC_{i}_SEVERITY={d.severity if hasattr(d, 'severity') else 'info'}")
        print(f"DIAGNOSTIC_{i}_MESSAGE={d.message if hasattr(d, 'message') else ''}")


def _cmd_risk_shell(cmd: str):
    engine = RiskEngine()
    result = engine.check(cmd)
    explanation = result["explanation"]
    print(f"RISK={result['risk']}")
    print(f"EXPLANATION={explanation}")
    if result['risk'] == 'high':
        warning = _ansi(f" HIGH RISK: {explanation} ", ANSI["red_bg_white"])
        print(f"ANSI_WARNING={warning}")
    elif result['risk'] == 'medium':
        warning = _ansi(f" MEDIUM RISK: {explanation} ", ANSI["yellow"])
        print(f"ANSI_WARNING={warning}")


def _cmd_risk(cmd: str):
    engine = RiskEngine()
    result = engine.check(cmd)
    print(json.dumps(result, ensure_ascii=False, indent=2))


def _cmd_context(buffer: str, cwd: str):
    ctx = collect_context(buffer, cwd)
    print(json.dumps(ctx, ensure_ascii=False, indent=2))


def _cmd_stats():
    try:
        from shansh.stats import get_recent_commands
        recent = get_recent_commands(10)
        cmd_list = [r.get("cmd", "") for r in recent]
    except Exception:
        cmd_list = []

    stats = {
        "completions": 0,
        "corrections": 0,
        "workflow_hits": 0,
        "risk_blocks": 0,
        "top_commands": cmd_list,
        "uptime": "Phase 3 - Copilot 体验强化"
    }
    print(json.dumps(stats, ensure_ascii=False, indent=2))


def _cmd_render(buffer: str, cwd: str):
    result = _build_suggest_result(buffer, cwd)
    top = result["top_candidates"]
    risk = result["risk"]

    diags = result.get("correction_diagnostics", [])
    diag_dicts = []
    for d in diags:
        if hasattr(d, "to_dict"):
            diag_dicts.append(d.to_dict())
        else:
            diag_dicts.append({
                "start": getattr(d, "start", 0), "end": getattr(d, "end", 0),
                "severity": getattr(d, "severity", "info"),
                "message": getattr(d, "message", ""),
            })

    if not top:
        resp = SuggestResponse(mode="none", risk=risk, diagnostics=diag_dicts)
    else:
        best = top[0]
        resp = SuggestResponse(
            mode=result["mode"] if result["mode"] != "none" else "completion",
            replacement=best.cmd,
            ghost_text=best.ghost_text if hasattr(best, "ghost_text") else "",
            explanation=best.explanation if hasattr(best, "explanation") else "",
            confidence=best.confidence if hasattr(best, "confidence") else 0.0,
            risk=risk,
            source=best.source if hasattr(best, "source") else "",
            candidates=[c.to_dict() for c in top],
            diagnostics=diag_dicts,
        )

    engine = RenderEngine(level=2)
    rendered = engine.render(buffer, resp)

    print(f"INPUT: {buffer}")
    print(f"RENDER_LEVEL: {rendered['render_level']}")
    if resp.replacement:
        print(f"SUGGEST: → {resp.replacement} | {resp.explanation}")
    else:
        print("SUGGEST: (无建议)")
    diag_line = rendered.get("diagnostic_line", "")
    if diag_line:
        print("DIAG:")
        print(buffer)
        print(diag_line)
    if resp.replacement:
        print(f"RISK: {risk}")
    print(f"ANSI_PREVIEW: {rendered['ansi_preview']}")


def _cmd_config(action: str, key: str = "", value: str = ""):
    from shansh.config import config_get, config_set, load_config, CONFIG_PATH
    if action == "get":
        if not key:
            config = load_config()
            print(json.dumps(config, ensure_ascii=False, indent=2))
            return
        result = config_get(key)
        if result is None:
            print(f"(not set)")
        else:
            print(json.dumps(result, ensure_ascii=False) if not isinstance(result, str) else result)
    elif action == "set":
        if not key:
            print("用法: shansh config set <key> <value>", file=sys.stderr)
            sys.exit(1)
        parsed_value = value
        if value.lower() in ("true", "false"):
            parsed_value = value.lower() == "true"
        elif value.isdigit():
            parsed_value = int(value)
        config_set(key, parsed_value)
        print(f"ok: {key} = {json.dumps(parsed_value, ensure_ascii=False)}")
    elif action == "path":
        print(CONFIG_PATH)
    else:
        print("用法: shansh config get [key]  |  shansh config set <key> <value>", file=sys.stderr)


def _cmd_doctor():
    import platform

    print("=== ShanShell AI 健康检查 (doctor) ===")
    print(f"Python version:    {platform.python_version()}")
    print(f"Project root:      {os.path.dirname(os.path.dirname(os.path.abspath(__file__)))}")
    print(f"PWD:               {os.getcwd()}")

    from shansh.config import CONFIG_PATH, load_config
    config = load_config()
    print(f"Config path:       {CONFIG_PATH}")
    print(f"Config exists:     {'yes' if os.path.exists(CONFIG_PATH) else 'no'}")
    mode = config.get("llm", {}).get("mode", "rules_only")
    print(f"LLM mode:          {mode}")

    remote_key_found = "no"
    try:
        key_env = config.get("remote", {}).get("api_key_env", "SHANSH_API_KEY")
        if os.environ.get(key_env):
            remote_key_found = "yes (key not displayed)"
    except Exception:
        pass
    print(f"Remote API key:    {remote_key_found}")

    zsh_found = "no"
    try:
        import subprocess
        result = subprocess.run(["zsh", "--version"], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            zsh_found = f"yes ({result.stdout.strip().split()[1] if result.stdout else '?'})"
    except Exception:
        pass
    print(f"Zsh found:         {zsh_found}")
    print(f"Risk engine:       enabled (yes)")
    print(f"Rules mode:        always available (yes)")
    print("=========================================")


def _cmd_server():
    from shansh.server import serve_http
    serve_http()


def main():
    parser = argparse.ArgumentParser(prog="shansh")
    parser.add_argument("command", nargs="?", default="suggest",
                        choices=["suggest", "suggest-shell", "suggest-rules-shell", "risk", "risk-shell", "context", "stats", "server", "render", "config", "doctor"])
    parser.add_argument("--buffer", default="")
    parser.add_argument("--cwd", default=os.getcwd())
    parser.add_argument("--cmd", default="")
    parser.add_argument("config_action", nargs="?", default="")
    parser.add_argument("config_key", nargs="?", default="")
    parser.add_argument("config_value", nargs="?", default="")

    args = parser.parse_args()

    if args.command == "suggest":
        _cmd_suggest(args.buffer, args.cwd)
    elif args.command == "suggest-shell":
        _cmd_suggest_shell(args.buffer, args.cwd)
    elif args.command == "suggest-rules-shell":
        _cmd_suggest_rules_shell(args.buffer, args.cwd)
    elif args.command == "risk":
        _cmd_risk(args.cmd)
    elif args.command == "risk-shell":
        _cmd_risk_shell(args.cmd)
    elif args.command == "context":
        _cmd_context(args.buffer, args.cwd)
    elif args.command == "stats":
        _cmd_stats()
    elif args.command == "server":
        _cmd_server()
    elif args.command == "render":
        _cmd_render(args.buffer, args.cwd)
    elif args.command == "config":
        _cmd_config(args.config_action, args.config_key, args.config_value)
    elif args.command == "doctor":
        _cmd_doctor()


if __name__ == "__main__":
    main()
