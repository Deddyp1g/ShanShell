"""ShanShell AI HTTP 服务。

监听 127.0.0.1:8765
- GET  /health  → {"status": "ok"}
- POST /suggest → SuggestResponse JSON
- POST /risk    → 风险检测 JSON
"""

import json
import os
from http.server import HTTPServer, BaseHTTPRequestHandler

from shansh.models import SuggestResponse
from shansh.context import collect_context
from shansh.completion_engine import CompletionEngine
from shansh.correction_engine import CorrectionEngine
from shansh.workflow_engine import WorkflowEngine
from shansh.risk_engine import RiskEngine
from shansh.ranker import Ranker
from shansh.nl2cmd_engine import NL2CmdEngine


class SmartShHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def _send_json(self, data, status=200):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/health":
            self._send_json({"status": "ok"})
        else:
            self._send_json({"error": "not found"}, 404)

    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length) if content_length > 0 else b"{}"
        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            self._send_json({"error": "invalid JSON"}, 400)
            return

        if self.path == "/suggest":
            self._handle_suggest(data)
        elif self.path == "/risk":
            self._handle_risk(data)
        else:
            self._send_json({"error": "not found"}, 404)

    def _handle_suggest(self, data: dict):
        buffer = data.get("buffer", "")
        cwd = data.get("cwd", os.getcwd())

        ctx = collect_context(buffer, cwd)
        trimmed = buffer.strip()

        is_nl = any("\u4e00" <= ch <= "\u9fff" for ch in trimmed) and not any(
            trimmed.startswith(p) for p in ["git ", "dnf ", "systemctl ", "docker ", "pip ", "npm ", "python ", "make ", "apt ", "ls ", "chmod ", "chown ", "sudo ", "rm ", "dd ", "mkfs", "tar ", "curl ", "wget "]
        )

        if is_nl and len(trimmed) > 2:
            nl_engine = NL2CmdEngine()
            nl_candidates = nl_engine.translate(trimmed, ctx)
            if nl_candidates:
                resp = SuggestResponse(
                    mode="nl2cmd",
                    replacement=nl_candidates[0].cmd,
                    ghost_text="",
                    explanation=nl_candidates[0].explanation,
                    confidence=nl_candidates[0].confidence,
                    risk="low",
                    source="nl2cmd",
                    candidates=[c.to_dict() for c in nl_candidates],
                    diagnostics=[]
                )
                self._send_json(resp.to_dict())
                return

        completion_engine = CompletionEngine()
        correction_engine = CorrectionEngine()
        workflow_engine = WorkflowEngine()

        completion_candidates = completion_engine.complete(trimmed, ctx)
        correction_result = correction_engine.correct(trimmed, ctx)
        correction_candidates = correction_result.get("candidates", [])
        correction_diagnostics = correction_result.get("diagnostics", [])
        correction_replacement = correction_result.get("replacement", "")

        workflow_candidates = workflow_engine.predict(ctx.get("last_commands", []), ctx)

        all_candidates = completion_candidates + correction_candidates + workflow_candidates
        ranker = Ranker()
        top_candidates = ranker.rank(all_candidates, max_results=3)

        risk_check = RiskEngine().check(trimmed if not correction_replacement else correction_replacement)

        if not top_candidates:
            resp = SuggestResponse(
                mode="completion",
                replacement="",
                ghost_text="",
                explanation="",
                confidence=0.0,
                risk=risk_check["risk"],
                source="",
                candidates=[],
                diagnostics=[]
            )
            self._send_json(resp.to_dict())
            return

        best = top_candidates[0]
        resp = SuggestResponse(
            mode="completion" if completion_candidates else ("correction" if correction_candidates else "workflow"),
            replacement=best.cmd,
            ghost_text=best.ghost_text if hasattr(best, "ghost_text") else "",
            explanation=best.explanation if hasattr(best, "explanation") else "",
            confidence=best.confidence if hasattr(best, "confidence") else 0.0,
            risk=risk_check["risk"],
            source=best.source if hasattr(best, "source") else "",
            candidates=[c.to_dict() for c in top_candidates],
            diagnostics=[d.to_dict() for d in correction_diagnostics] if correction_diagnostics else []
        )
        self._send_json(resp.to_dict())

    def _handle_risk(self, data: dict):
        cmd = data.get("cmd", "")
        result = RiskEngine().check(cmd)
        self._send_json(result)


def serve_http(host="127.0.0.1", port=8765):
    server = HTTPServer((host, port), SmartShHandler)
    print(f"[shansh] HTTP 服务启动: http://{host}:{port}")
    print(f"[shansh] GET  /health  → 健康检查")
    print(f"[shansh] POST /suggest → 智能建议")
    print(f"[shansh] POST /risk    → 风险检测")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[shansh] 服务已关闭")
        server.shutdown()


if __name__ == "__main__":
    serve_http()
