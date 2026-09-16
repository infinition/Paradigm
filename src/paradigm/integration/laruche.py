from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from typing import Any

from .contract import DeliberateDecision, Outcome, ParadigmState, ReflexDecision, VerifiedOutcome
from .engine import Paradigm, ReflexPolicy

# LaRuche engine wire shapes (laruche-butinage): Message {role, contenu, outil?}, Appel {id, nom, args},
# ResultatOutil {ok, sortie, images, incertain}, Bilan.fin (FinDeVol variant name).

READ_ONLY_TOOLS = ("file_read", "read_extract", "file_list", "file_search", "lsp", "tool_search")
DEFAULT_SHELL_ALLOW = (
    r"^(python3? -m )?pytest(\s.*)?$",
    r"^cargo (test|check|build)(\s.*)?$",
    r"^npm (test|run test)(\s.*)?$",
    r"^go test(\s.*)?$",
)
FIN_SUCCESS = ("Accomplie",)
FIN_FAILURE = ("Erreur", "Plafond", "BoucleSterile", "Budget", "Escalade")


def canonical_shell(command: str, workspace: str | None = None) -> str:
    """Reduce equivalent shell phrasings of one command to a canonical form.

    A leading ``cd <workspace> &&`` is dropped (tools already run in the workspace),
    and output decorations that do not change the command's effect are removed:
    ``2>&1``, ``| tail -N``, ``| head -N``, ``; echo ...``. The reflex replays the
    canonical form, never the model's decorated one.
    """
    cmd = command.strip()
    if workspace:
        for prefix in (f"cd {workspace} && ", f"cd '{workspace}' && ", f'cd "{workspace}" && '):
            if cmd.startswith(prefix):
                cmd = cmd[len(prefix):]
                break
    cmd = re.split(r"\s*;\s*echo\b", cmd)[0]
    cmd = re.split(r"\s*\|\s*(tail|head)\b", cmd)[0]
    cmd = cmd.replace("2>&1", "").strip()
    return re.sub(r"\s+", " ", cmd)


def canonical_args(args: Any) -> str:
    return json.dumps(args, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def action_key(nom: str, args: Any) -> str:
    """Stable label for a tool call: name plus a short hash of its canonical arguments."""
    digest = hashlib.blake2b(canonical_args(args).encode("utf-8"), digest_size=6).hexdigest()
    return f"{nom}#{digest}"


@dataclass(slots=True)
class LaRucheAdapter:
    """Translate LaRuche's engine shapes into the generic contract and back.

    Level 2 integration: a reflex may replay a whitelisted tool with the exact argument
    template it was validated with. Argument synthesis stays with the model. Tools outside
    the whitelist, shell commands outside the allowlist, and any call whose template is
    unknown deliberate by default.
    """

    reflex_tools: tuple[str, ...] = READ_ONLY_TOOLS + ("shell_exec", "task_complete", "mission_accomplie")
    shell_allow: tuple[str, ...] = DEFAULT_SHELL_ALLOW
    high_risk_tools: tuple[str, ...] = ("file_write", "file_edit", "git_push", "delegate", "computer", "browser")
    goal_chars: int = 200
    templates: dict[str, dict[str, Any]] = field(default_factory=dict)
    last_results: dict[str, dict[str, Any]] = field(default_factory=dict)

    # ----------------------------------------------------------- policy helpers

    def shell_command(self, args: Any) -> str | None:
        if isinstance(args, dict):
            for key in ("command", "cmd", "commande"):
                if isinstance(args.get(key), str):
                    return args[key].strip()
        return None

    def canonical_call(self, nom: str, args: Any, workspace: str | None = None) -> Any:
        """Arguments as the reflex would replay them."""
        if nom == "shell_exec" and isinstance(args, dict):
            cmd = self.shell_command(args)
            if cmd is not None:
                key = next(k for k in ("command", "cmd", "commande") if isinstance(args.get(k), str))
                return {**args, key: canonical_shell(cmd, workspace)}
        return args

    def reflex_capable(self, nom: str, args: Any, workspace: str | None = None) -> bool:
        if nom not in self.reflex_tools or nom in self.high_risk_tools:
            return False
        if nom == "shell_exec":
            cmd = self.shell_command(self.canonical_call(nom, args, workspace))
            return bool(cmd) and any(re.fullmatch(p, cmd) for p in self.shell_allow)
        return True

    def register_template(self, nom: str, args: Any) -> str:
        key = action_key(nom, args)
        self.templates[key] = {"nom": nom, "args": args}
        return key

    def policy(self) -> ReflexPolicy:
        return ReflexPolicy(allowed_actions=tuple(re.escape(t) + r"#[0-9a-f]{12}" for t in self.reflex_tools), max_risk="low")

    # ----------------------------------------------------------- state encoding

    def encode_state(self, session: str, messages: list[dict[str, Any]], schemas: list[dict[str, Any]]) -> ParadigmState:
        goal = next((m.get("contenu", "") for m in messages if str(m.get("role", "")).lower() == "utilisateur"), "")[: self.goal_chars]
        observations = [m for m in messages if str(m.get("role", "")).lower() == "observation"]
        recent = tuple(str(m.get("outil") or "?") for m in observations[-3:])
        last = self.last_results.get(session)
        last_action = last["key"] if last else (recent[-1] if recent else None)
        if last is None:
            last_outcome = "none"
        elif last["incertain"]:
            last_outcome = "uncertain"
        else:
            last_outcome = "success" if last["ok"] else "failure"
        available = tuple(
            str(s.get("name") or (s.get("function") or {}).get("name") or "") for s in schemas
        )
        available = tuple(a for a in available if a)
        risk = "low"
        features: dict[str, Any] = {
            "consecutive_failures": int(last.get("consecutive_failures", 0)) if last else 0,
            "last_output_kind": self._output_kind(last["sortie"]) if last else "none",
        }
        return ParadigmState(
            domain="laruche",
            phase="start" if not observations else "after_tool",
            available_actions=available,
            goal=goal,
            last_action=last_action.split("#")[0] if last_action else None,
            last_outcome=last_outcome,
            recent_actions=recent,
            step=len(observations),
            features=features,
            risk=risk,
            family_hint=self.family_for(goal, last_action, last_outcome, features["last_output_kind"]),
            context_refs={"session": session},
        )

    @staticmethod
    def _output_kind(sortie: str) -> str:
        head = sortie[:800]
        for kind, pattern in (
            ("tests_passed", r"\b(passed|ok)\b(?!.*(failed|error))"),
            ("tests_failed", r"\b(FAILED|failed|AssertionError)\b"),
            ("missing_module", r"ModuleNotFoundError|No module named"),
            ("syntax_error", r"SyntaxError"),
            ("name_error", r"NameError"),
            ("import_error", r"ImportError"),
            ("not_found", r"No such file|not found|ENOENT"),
        ):
            if re.search(pattern, head):
                return kind
        return "other"

    @staticmethod
    def family_for(goal: str, last_action: str | None, last_outcome: str, output_kind: str) -> str:
        """Behavior family: what just happened and how it went, not the goal text."""
        tool = (last_action or "start").split("#")[0]
        return f"laruche:{tool}:{last_outcome}:{output_kind}"

    # ------------------------------------------------------------ action side

    def to_appel(self, decision: ReflexDecision) -> dict[str, Any] | None:
        template = self.templates.get(decision.action)
        if template is None:
            return None
        return {"nom": template["nom"], "args": template["args"]}

    def action_from_appel(self, appel: dict[str, Any], workspace: str | None = None) -> tuple[str, bool]:
        """Label for an executed call and whether that call is reflex-capable at all."""
        nom, args = str(appel.get("nom")), appel.get("args", {})
        capable = self.reflex_capable(nom, args, workspace)
        canon = self.canonical_call(nom, args, workspace) if capable else args
        key = self.register_template(nom, canon) if capable else action_key(nom, canon)
        return key, capable

    TEST_REPORT = re.compile(r"\b\d+ (passed|failed|error|errors)\b|\bno tests ran\b|FAILED|PASSED")

    def outcome_from_result(self, result: dict[str, Any], appel: dict[str, Any] | None = None, workspace: str | None = None) -> VerifiedOutcome:
        """Step-level verification from the tool result.

        ``incertain`` is UNKNOWN. For an allowlisted diagnostic test command the verdict is
        the report, not the exit code: a test run that reports failures executed correctly
        and is a verified observation; a test command that produced no report (interpreter
        missing, syntax error in the command) is UNKNOWN. For every other call ``ok`` is
        SUCCESS and anything else FAILURE.
        """
        if result.get("incertain"):
            return VerifiedOutcome.unknown("laruche:ResultatOutil", incertain=True)
        if appel is not None and str(appel.get("nom")) == "shell_exec":
            cmd = self.shell_command(self.canonical_call("shell_exec", appel.get("args", {}), workspace))
            if cmd and any(re.fullmatch(p, cmd) for p in self.shell_allow):
                if self.TEST_REPORT.search(str(result.get("sortie", ""))[:4000]):
                    return VerifiedOutcome.success("laruche:test_report", exit_ok=bool(result.get("ok")))
                return VerifiedOutcome.unknown("laruche:test_report", reason="no test report in output")
        if result.get("ok"):
            return VerifiedOutcome.success("laruche:ResultatOutil")
        return VerifiedOutcome.failure("laruche:ResultatOutil")

    def outcome_from_fin(self, fin: str) -> VerifiedOutcome:
        """Episode verdict from the mission end: only a verified Accomplie is SUCCESS."""
        if fin in FIN_SUCCESS:
            return VerifiedOutcome.success("laruche:ControleMission", fin=fin)
        if fin in FIN_FAILURE:
            return VerifiedOutcome.failure("laruche:FinDeVol", fin=fin)
        return VerifiedOutcome.unknown("laruche:FinDeVol", fin=fin)

    def remember_result(self, session: str, key: str, result: dict[str, Any]) -> None:
        prev = self.last_results.get(session)
        failures = 0 if result.get("ok") else (int(prev.get("consecutive_failures", 0)) + 1 if prev else 1)
        self.last_results[session] = {
            "key": key,
            "ok": bool(result.get("ok")),
            "incertain": bool(result.get("incertain")),
            "sortie": str(result.get("sortie", ""))[:800],
            "consecutive_failures": failures,
        }

    def forget_session(self, session: str) -> None:
        self.last_results.pop(session, None)


class LaRucheBridge:
    """Session-aware glue between the wire protocol and one Paradigm engine."""

    def __init__(self, engine: Paradigm, adapter: LaRucheAdapter | None = None) -> None:
        self.adapter = adapter or LaRucheAdapter()
        self.engine = engine
        self._pending: dict[str, dict[str, Any]] = {}

    def decide(self, session: str, messages: list[dict[str, Any]], schemas: list[dict[str, Any]], workspace: str | None = None) -> dict[str, Any]:
        state = self.adapter.encode_state(session, messages, schemas)
        if workspace:
            state.context_refs["workspace"] = workspace
        decision = self.engine.decide(state)
        payload: dict[str, Any] = {"decision": decision.to_dict(), "state": state.to_dict()}
        if isinstance(decision, ReflexDecision):
            appel = self.adapter.to_appel(decision)
            if appel is None:
                # Trusted label without a template cannot be executed: deliberate instead.
                decision = DeliberateDecision(reason="no_argument_template", family=decision.family, trust_status="active", proposed_action=decision.action)
                payload["decision"] = decision.to_dict()
            else:
                payload["appel"] = appel
        self._pending[session] = {"state": state, "source": decision.source, "observed": 0}
        return payload

    def observe(self, session: str, appel: dict[str, Any], result: dict[str, Any], *, source: str | None = None, usage: dict[str, Any] | None = None) -> dict[str, Any]:
        pending = self._pending.get(session)
        if pending is None:
            # No decision was asked for this call (should not happen through the bridge):
            # record it for telemetry only, never as evidence.
            state = self.adapter.encode_state(session, [], [])
            pending = {"state": state, "source": "deliberative", "observed": 1}
        state = pending["state"]
        src = source or pending["source"]
        first_of_batch = pending.get("observed", 0) == 0
        pending["observed"] = pending.get("observed", 0) + 1
        workspace = state.context_refs.get("workspace")
        key, capable = self.adapter.action_from_appel(appel, workspace)
        outcome = self.adapter.outcome_from_result(result, appel, workspace)
        metadata: dict[str, Any] = {}
        if usage and first_of_batch:
            metadata["llm_tokens"] = int(usage.get("entree", 0)) + int(usage.get("sortie", 0))
            metadata["llm_latency_ms"] = float(usage.get("latency_ms", 0.0))
        # One decision per state. A model response carrying several tool calls yields one
        # teacher decision (the first call); the others are telemetry only. A call whose
        # arguments a reflex may never replay is likewise never a reflex label.
        if not capable or not first_of_batch:
            reason = "not_reflex_capable" if not capable else "batched_call"
            outcome = VerifiedOutcome(Outcome.UNKNOWN, {"reason": reason, **outcome.evidence}, outcome.verifier)
        rec = self.engine.observe(state, key, outcome, source=src, metadata=metadata)
        self.adapter.remember_result(session, key, result)
        rec.update({"action": key, "reflex_capable": capable, "first_of_batch": first_of_batch})
        return rec

    def close(self, session: str, fin: str) -> dict[str, Any]:
        self._pending.pop(session, None)
        self.adapter.forget_session(session)
        return self.engine.close_episode(self.adapter.outcome_from_fin(fin))
