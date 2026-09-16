from __future__ import annotations

import json
import os
import re
import time
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass
from typing import Any, Callable

from .agent_vertical import ACTIONS_EXTENDED, AgentState


@dataclass(slots=True)
class LLMUsage:
    calls: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    latency_ms: float = 0.0
    estimated_cost_usd: float = 0.0
    invalid_actions: int = 0
    repaired_actions: int = 0
    request_failures: int = 0

    def copy(self) -> "LLMUsage":
        return LLMUsage(**asdict(self))

    def delta(self, before: "LLMUsage") -> "LLMUsage":
        return LLMUsage(
            calls=self.calls - before.calls,
            prompt_tokens=self.prompt_tokens - before.prompt_tokens,
            completion_tokens=self.completion_tokens - before.completion_tokens,
            total_tokens=self.total_tokens - before.total_tokens,
            latency_ms=self.latency_ms - before.latency_ms,
            estimated_cost_usd=self.estimated_cost_usd - before.estimated_cost_usd,
            invalid_actions=self.invalid_actions - before.invalid_actions,
            repaired_actions=self.repaired_actions - before.repaired_actions,
            request_failures=self.request_failures - before.request_failures,
        )


@dataclass(slots=True)
class LLMCallRecord:
    action: str
    raw_text: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    latency_ms: float
    estimated_cost_usd: float
    valid: bool
    repaired: bool


def valid_actions_for_state(state: AgentState) -> tuple[str, ...]:
    if state.tests_passed:
        return ("finish",)
    if state.phase == "start" or state.patched:
        return ("run_tests",)
    if state.phase == "failed":
        if state.failure_kind == "missing_module":
            return ("inspect_file", "search_symbol", "inspect_dependency")
        return ("inspect_file", "search_symbol")
    if state.phase == "searched":
        return ("inspect_file",)
    if state.phase == "inspected":
        return ("apply_fix",)
    if state.phase == "dep_inspected":
        return ("search_registry", "modify_dependency_file", "inspect_file")
    if state.phase == "registry_searched":
        return ("modify_dependency_file", "inspect_file")
    if state.phase == "dep_modified":
        return ("install_dependency", "run_tests")
    if state.phase == "installed":
        return ("run_tests",)
    return ("run_tests",)


def safe_recovery_action(state: AgentState) -> str:
    allowed = valid_actions_for_state(state)
    # Prefer a deterministic, non-destructive observation when multiple actions are legal.
    if "inspect_file" in allowed:
        return "inspect_file"
    return allowed[0]


class OpenAICompatibleCodingDeliberator:
    """Tool-choice controller for OpenAI-compatible chat-completions endpoints.

    The controller intentionally asks the model only for the next control action.
    Paradigm can then compile repeated control decisions without claiming to compile
    free-form code generation or reasoning.

    ``api_style="ollama"`` targets Ollama's native ``/api/chat`` instead, which is the
    only way to disable hidden reasoning on hybrid thinking models such as qwen3:8b.
    Token counts are taken from ``prompt_eval_count`` and ``eval_count``.
    """

    def __init__(
        self,
        *,
        base_url: str,
        model: str,
        api_key: str | None = None,
        timeout_s: float = 60.0,
        temperature: float = 0.0,
        max_tokens: int = 64,
        input_cost_per_million: float = 0.0,
        output_cost_per_million: float = 0.0,
        transport: Callable[[str, dict[str, Any], dict[str, str], float], dict[str, Any]] | None = None,
        api_style: str = "openai",
        think: bool = False,
    ) -> None:
        if api_style not in {"openai", "ollama"}:
            raise ValueError(f"unsupported api_style: {api_style!r}")
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.api_style = api_style
        self.think = bool(think)
        self.api_key = api_key
        self.timeout_s = float(timeout_s)
        self.temperature = float(temperature)
        self.max_tokens = int(max_tokens)
        self.input_cost_per_million = float(input_cost_per_million)
        self.output_cost_per_million = float(output_cost_per_million)
        self.transport = transport or self._http_transport
        self.usage = LLMUsage()
        self.records: list[LLMCallRecord] = []

    @classmethod
    def from_env(cls) -> "OpenAICompatibleCodingDeliberator":
        base_url = os.environ.get("PARADIGM_LLM_BASE_URL", "").strip()
        model = os.environ.get("PARADIGM_LLM_MODEL", "").strip()
        if not base_url or not model:
            raise RuntimeError(
                "Set PARADIGM_LLM_BASE_URL and PARADIGM_LLM_MODEL before running the live P2.2 benchmark."
            )
        return cls(
            base_url=base_url,
            model=model,
            api_key=os.environ.get("PARADIGM_LLM_API_KEY") or None,
            timeout_s=float(os.environ.get("PARADIGM_LLM_TIMEOUT", "60")),
            input_cost_per_million=float(os.environ.get("PARADIGM_LLM_INPUT_COST_PER_M", "0")),
            output_cost_per_million=float(os.environ.get("PARADIGM_LLM_OUTPUT_COST_PER_M", "0")),
            api_style=os.environ.get("PARADIGM_LLM_API", "openai").strip() or "openai",
            think=os.environ.get("PARADIGM_LLM_THINK", "0").strip() in {"1", "true", "yes"},
        )

    @staticmethod
    def _http_transport(url: str, payload: dict[str, Any], headers: dict[str, str], timeout: float) -> dict[str, Any]:
        request = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))

    @staticmethod
    def _extract_text(response: dict[str, Any]) -> str:
        if "message" in response and "choices" not in response:
            return str((response.get("message") or {}).get("content", ""))
        choices = response.get("choices") or []
        if not choices:
            return ""
        message = choices[0].get("message") or {}
        content = message.get("content", "")
        if isinstance(content, list):
            pieces: list[str] = []
            for item in content:
                if isinstance(item, dict) and item.get("type") in {"text", "output_text"}:
                    pieces.append(str(item.get("text", "")))
            return "".join(pieces)
        return str(content)

    @staticmethod
    def _parse_action(text: str) -> str | None:
        stripped = text.strip()
        try:
            obj = json.loads(stripped)
            action = str(obj.get("action", ""))
            if action in ACTIONS_EXTENDED:
                return action
        except (json.JSONDecodeError, AttributeError, TypeError):
            pass
        match = re.search(r"\b(" + "|".join(ACTIONS_EXTENDED) + r")\b", stripped)
        return match.group(1) if match else None

    @staticmethod
    def _state_payload(state: AgentState) -> dict[str, Any]:
        payload = {
            "task": state.task.prompt,
            "phase": state.phase,
            "failure_kind": state.failure_kind,
            "tests_passed": state.tests_passed,
            "inspected": state.inspected,
            "searched": state.searched,
            "patched": state.patched,
            "tool_calls": state.tool_calls,
            "last_tool_output": state.last_output[-2500:],
            "allowed_actions": list(valid_actions_for_state(state)),
        }
        if state.task.is_dependency_task:
            # Extra fields only for dependency tasks so earlier prompts stay byte-identical.
            payload.update(
                {
                    "dep_inspected": state.dep_inspected,
                    "registry_searched": state.registry_searched,
                    "dep_modified": state.dep_modified,
                    "installed": state.installed,
                }
            )
        return payload

    def _payload(self, state: AgentState) -> dict[str, Any]:
        system = (
            "You are the slow-path controller of a constrained coding agent. "
            "Choose exactly one next action from allowed_actions. Do not solve the task in prose. "
            "Return strict JSON only: {\"action\": \"...\", \"reason\": \"short reason\"}. "
            "Never choose an action outside allowed_actions."
        )
        user = json.dumps(self._state_payload(state), ensure_ascii=False)
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ]
        if self.api_style == "ollama":
            return {
                "model": self.model,
                "messages": messages,
                "stream": False,
                "think": self.think,
                "options": {"temperature": self.temperature, "num_predict": self.max_tokens},
            }
        return {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }

    def snapshot(self) -> LLMUsage:
        return self.usage.copy()

    def decide(self, state: AgentState) -> str:
        payload = self._payload(state)
        url = f"{self.base_url}/api/chat" if self.api_style == "ollama" else f"{self.base_url}/chat/completions"
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        start = time.perf_counter()
        try:
            response = self.transport(url, payload, headers, self.timeout_s)
        except (urllib.error.URLError, TimeoutError, OSError, ValueError) as exc:
            self.usage.request_failures += 1
            raise RuntimeError(f"LLM controller request failed: {exc}") from exc
        latency_ms = (time.perf_counter() - start) * 1e3

        text = self._extract_text(response)
        usage = response.get("usage") or {}
        if self.api_style == "ollama":
            usage = {
                "prompt_tokens": response.get("prompt_eval_count", 0),
                "completion_tokens": response.get("eval_count", 0),
            }
        prompt_tokens = int(usage.get("prompt_tokens") or usage.get("input_tokens") or 0)
        completion_tokens = int(usage.get("completion_tokens") or usage.get("output_tokens") or 0)
        total_tokens = int(usage.get("total_tokens") or (prompt_tokens + completion_tokens))
        cost = (
            prompt_tokens * self.input_cost_per_million / 1_000_000
            + completion_tokens * self.output_cost_per_million / 1_000_000
        )

        parsed = self._parse_action(text)
        allowed = set(valid_actions_for_state(state))
        valid = parsed in allowed if parsed is not None else False
        repaired = not valid
        if repaired:
            self.usage.invalid_actions += 1
            self.usage.repaired_actions += 1
            action = safe_recovery_action(state)
        else:
            action = str(parsed)

        self.usage.calls += 1
        self.usage.prompt_tokens += prompt_tokens
        self.usage.completion_tokens += completion_tokens
        self.usage.total_tokens += total_tokens
        self.usage.latency_ms += latency_ms
        self.usage.estimated_cost_usd += cost
        self.records.append(
            LLMCallRecord(
                action=action,
                raw_text=text,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
                latency_ms=latency_ms,
                estimated_cost_usd=cost,
                valid=valid,
                repaired=repaired,
            )
        )
        return action
