from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

from .contract import Outcome, ParadigmState, VerifiedOutcome
from .engine import Paradigm
from .laruche import LaRucheAdapter, LaRucheBridge


def _outcome_from_payload(data: dict[str, Any]) -> VerifiedOutcome:
    raw = data.get("outcome", data)
    if isinstance(raw, str):
        return VerifiedOutcome(Outcome(raw.lower()))
    return VerifiedOutcome(Outcome(str(raw.get("outcome", "unknown")).lower()), dict(raw.get("evidence") or {}), str(raw.get("verifier", "")))


class ParadigmService:
    """JSON over HTTP on localhost. One engine, one LaRuche bridge, one lock."""

    def __init__(self, engine: Paradigm, *, state_file: Path | None = None, adapter: LaRucheAdapter | None = None) -> None:
        self.engine = engine
        self.bridge = LaRucheBridge(engine, adapter)
        self.state_file = Path(state_file) if state_file else None
        self._lock = threading.RLock()

    def _persist(self) -> None:
        if self.state_file is not None:
            self.engine.save(self.state_file)

    def handle(self, method: str, path: str, query: dict[str, list[str]], body: dict[str, Any]) -> tuple[int, dict[str, Any]]:
        with self._lock:
            if method == "GET" and path == "/v1/health":
                return 200, {"ok": True, "active_reflex_version": self.engine.compiler.state.version}
            if method == "GET" and path == "/v1/telemetry":
                return 200, self.engine.telemetry()
            if method == "GET" and path == "/v1/manifest":
                return 200, {"trust_manifest": self.engine.trust_manifest()}
            if method == "GET" and path == "/v1/log":
                last = int(query.get("last", ["50"])[0])
                return 200, {"decisions": self.engine.decision_log(last=last)}
            if method == "POST" and path == "/v1/explain":
                return 200, self.engine.explain(ParadigmState.from_dict(body["state"]))
            if method == "POST" and path == "/v1/decide":
                state = ParadigmState.from_dict(body["state"])
                actions = tuple(body["actions"]) if body.get("actions") else None
                decision = self.engine.decide(state, actions)
                return 200, {"decision": decision.to_dict()}
            if method == "POST" and path == "/v1/observe":
                state = ParadigmState.from_dict(body["state"])
                rec = self.engine.observe(state, str(body["action"]), _outcome_from_payload(body), source=str(body.get("source", "deliberative")), metadata=body.get("metadata"))
                return 200, rec
            if method == "POST" and path == "/v1/episode/close":
                rec = self.engine.close_episode(_outcome_from_payload(body), family=body.get("family"))
                self._persist()
                return 200, rec
            if method == "POST" and path == "/v1/laruche/decide":
                return 200, self.bridge.decide(str(body.get("session", "default")), list(body.get("messages") or []), list(body.get("schemas") or []), workspace=body.get("workspace"))
            if method == "POST" and path == "/v1/laruche/observe":
                return 200, self.bridge.observe(str(body.get("session", "default")), dict(body["appel"]), dict(body["result"]), source=body.get("source"), usage=body.get("usage"))
            if method == "POST" and path == "/v1/laruche/close":
                rec = self.bridge.close(str(body.get("session", "default")), str(body.get("fin", "Autre")))
                self._persist()
                return 200, rec
            return 404, {"error": f"unknown route {method} {path}"}


def make_handler(service: ParadigmService):
    class Handler(BaseHTTPRequestHandler):
        def _send(self, status: int, payload: dict[str, Any]) -> None:
            data = json.dumps(payload, default=float).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def _dispatch(self, method: str) -> None:
            parsed = urlparse(self.path)
            length = int(self.headers.get("Content-Length") or 0)
            raw = self.rfile.read(length) if length else b""
            try:
                body = json.loads(raw.decode("utf-8")) if raw else {}
                status, payload = service.handle(method, parsed.path, parse_qs(parsed.query), body)
            except (KeyError, ValueError, TypeError) as exc:
                status, payload = 400, {"error": f"{type(exc).__name__}: {exc}"}
            self._send(status, payload)

        def do_GET(self) -> None:  # noqa: N802
            self._dispatch("GET")

        def do_POST(self) -> None:  # noqa: N802
            self._dispatch("POST")

        def log_message(self, format: str, *args: Any) -> None:  # silence default logging
            return

    return Handler


def serve(service: ParadigmService, host: str = "127.0.0.1", port: int = 8765) -> ThreadingHTTPServer:
    server = ThreadingHTTPServer((host, port), make_handler(service))
    return server
