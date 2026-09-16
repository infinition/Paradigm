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

READ_ONLY_TOOLS = ("file_read", "file_list", "file_search", "lsp", "tool_search")
DEFAULT_SHELL_ALLOW = (
    r"^(python3? -m )?pytest(\s.*)?$",
    r"^cargo (test|check|build)(\s.*)?$",
    r"^npm (test|run test)(\s.*)?$",
    r"^go test(\s.*)?$",
)
FIN_SUCCESS = ("Accomplie",)
FIN_FAILURE = ("Erreur", "Plafond", "BoucleSterile", "Budget", "Escalade")


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

    def reflex_capable(self, nom: str, args: Any) -> bool:
        if nom not in self.reflex_tools or nom in self.high_risk_tools:
            return False
        if nom == "shell_exec":
            cmd = self.shell_command(args)
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

    def action_from_appel(self, appel: dict[str, Any]) -> tuple[str, bool]:
        """Label for an executed call and whether that call is reflex-capable at all."""
        nom, args = str(appel.get("nom")), appel.get("args", {})
        capable = self.reflex_capable(nom, args)
        key = self.register_template(nom, args) if capable else action_key(nom, args)
        return key, capable

    def outcome_from_result(self, result: dict[str, Any]) -> VerifiedOutcome:
        """ok -> SUCCESS, incertain -> UNKNOWN, otherwise FAILURE. This is tool-level verification only."""
        if result.get("incertain"):
            return VerifiedOutcome.unknown("laruche:ResultatOutil", incertain=True)
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

    def decide(self, session: str, messages: list[dict[str, Any]], schemas: list[dict[str, Any]]) -> dict[str, Any]:
        state = self.adapter.encode_state(session, messages, schemas)
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
        self._pending[session] = {"state": state, "source": decision.source}
        return payload

    def observe(self, session: str, appel: dict[str, Any], result: dict[str, Any], *, source: str | None = None, usage: dict[str, Any] | None = None) -> dict[str, Any]:
        pending = self._pending.pop(session, None)
        state = pending["state"] if pending else self.adapter.encode_state(session, [], [])
        src = source or (pending["source"] if pending else "deliberative")
        key, capable = self.adapter.action_from_appel(appel)
        outcome = self.adapter.outcome_from_result(result)
        metadata: dict[str, Any] = {}
        if usage:
            metadata["llm_tokens"] = int(usage.get("entree", 0)) + int(usage.get("sortie", 0))
            metadata["llm_latency_ms"] = float(usage.get("latency_ms", 0.0))
        # A deliberative call whose arguments a reflex may never replay is recorded as unverified
        # evidence so it never becomes a reflex label; it still counts toward telemetry.
        if not capable:
            outcome = VerifiedOutcome(Outcome.UNKNOWN, {"reason": "not_reflex_capable", **outcome.evidence}, outcome.verifier)
        rec = self.engine.observe(state, key, outcome, source=src, metadata=metadata)
        self.adapter.remember_result(session, key, result)
        rec.update({"action": key, "reflex_capable": capable})
        return rec

    def close(self, session: str, fin: str) -> dict[str, Any]:
        self._pending.pop(session, None)
        self.adapter.forget_session(session)
        return self.engine.close_episode(self.adapter.outcome_from_fin(fin))
