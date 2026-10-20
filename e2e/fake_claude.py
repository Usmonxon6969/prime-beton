"""Tiny fake of the Anthropic Messages API for browser tests (port 9099)."""
import json
from http.server import BaseHTTPRequestHandler, HTTPServer


class H(BaseHTTPRequestHandler):
    def log_message(self, *a): pass

    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers["content-length"])))
        msgs = body["messages"]
        last = msgs[-1]
        if body.get("tool_choice"):
            out = {"content": [{"type": "tool_use", "id": "t1", "name": "propose_document", "input": {
                "kind": "receipt", "party": "Cement Trade", "rows": [{"item": "Sement", "qty": 100, "price": 1200}, {"item": "mystery", "qty": 2}]}}], "stop_reason": "tool_use"}
        elif isinstance(last["content"], list) and last["content"][0].get("type") == "tool_result":
            out = {"content": [{"type": "text", "text": "**Sement** bo‘yicha qoldiq topildi:\n- Jami: 3 700 kg\n- Minimal: 30 000 kg"}], "stop_reason": "end_turn"}
        elif "Bugungi" in json.dumps(last) or "briefing" in json.dumps(last):
            out = {"content": [{"type": "text", "text": "- Bugun sement qoldig‘i kam.\n- Mijoz qarzi bor."}], "stop_reason": "end_turn"}
        else:
            out = {"content": [{"type": "tool_use", "id": "t0", "name": "get_stock", "input": {"query": "cement"}}], "stop_reason": "tool_use"}
        data = json.dumps({"model": "fake", "usage": {"input_tokens": 1, "output_tokens": 1}, **out}).encode()
        self.send_response(200); self.send_header("content-type", "application/json"); self.send_header("content-length", str(len(data))); self.end_headers(); self.wfile.write(data)


HTTPServer(("127.0.0.1", 9099), H).serve_forever()
