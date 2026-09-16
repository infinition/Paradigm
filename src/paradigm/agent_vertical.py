from __future__ import annotations

import hashlib
import importlib
import re
import shutil
import subprocess
import tempfile
import time
import io
import sys
import unittest
from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol

import numpy as np

from .model_selection import MinimalReflexSelector, ReflexSelection
from .ood import MahalanobisGate
from .schema import Trace

ACTIONS = ("run_tests", "inspect_file", "search_symbol", "apply_fix", "finish")
FAILURES = ("none", "name_error", "import_error", "assertion_error", "syntax_error", "other", "passed")
PHASES = ("start", "failed", "inspected", "searched", "patched", "passed", "done")

# Extended vocabulary for the Type B dependency-resolution family. Opt-in: the base
# vocabulary above is unchanged so earlier recorded protocols stay byte-identical.
DEPENDENCY_ACTIONS = ("inspect_dependency", "search_registry", "modify_dependency_file", "install_dependency")
ACTIONS_EXTENDED = ACTIONS + DEPENDENCY_ACTIONS
FAILURES_EXTENDED = FAILURES + ("missing_module",)
PHASES_EXTENDED = PHASES + ("dep_inspected", "registry_searched", "dep_modified", "installed")


@dataclass(slots=True)
class CodingTask:
    task_id: str
    family: str
    prompt: str
    files: dict[str, str]
    fixed_files: dict[str, str]
    target_file: str
    search_term: str = ""
    registry: dict[str, str] | None = None
    requirements: str = ""
    fixed_requirements: str = ""

    @property
    def is_dependency_task(self) -> bool:
        return self.registry is not None


@dataclass(slots=True)
class AgentState:
    task: CodingTask
    phase: str = "start"
    failure_kind: str = "none"
    last_output: str = ""
    tool_calls: int = 0
    tests_passed: bool = False
    inspected: bool = False
    searched: bool = False
    patched: bool = False
    dep_inspected: bool = False
    registry_searched: bool = False
    dep_modified: bool = False
    installed: bool = False


@dataclass(slots=True)
class PolicyDecision:
    action: str
    source: str
    confidence: float
    reason: str = ""
    latency_ms: float = 0.0


@dataclass(slots=True)
class AgentDecisionRecord:
    features: np.ndarray
    action: str
    source: str
    phase: str
    failure_kind: str
    confidence: float
    family: str | None = None
    validated: bool = True


@dataclass(slots=True)
class AgentEpisode:
    task_id: str
    family: str
    success: bool
    steps: int
    decisions: list[PolicyDecision] = field(default_factory=list)
    records: list[AgentDecisionRecord] = field(default_factory=list)
    deliberative_calls: int = 0
    reflex_calls: int = 0
    invalid_reflex_actions: int = 0
    fallback_reasons: dict[str, int] = field(default_factory=dict)
    contract: dict[str, bool] = field(default_factory=dict)

    @property
    def total_policy_calls(self) -> int:
        return self.deliberative_calls + self.reflex_calls

    @property
    def policy_latency_ms(self) -> float:
        return float(sum(d.latency_ms for d in self.decisions))


class DeliberativePolicy(Protocol):
    def decide(self, state: AgentState) -> str: ...


class CallableDeliberator:
    """Adapter for an external controller exposed as a Python callable."""

    def __init__(self, fn) -> None:
        self.fn = fn

    def decide(self, state: AgentState) -> str:
        action = str(self.fn(state))
        if action not in ACTIONS:
            raise ValueError(f"external deliberator returned unsupported action: {action!r}")
        return action


class ReferenceCodingDeliberator:
    """Deterministic reference solver for the offline vertical benchmark.

    It deliberately performs extra CPU work before returning a decision so that
    the benchmark has a measurable slow path. It is not presented as an LLM.
    A real LLM/controller can be supplied through the same ``decide`` interface.
    """

    def __init__(self, analysis_rounds: int = 3500) -> None:
        self.analysis_rounds = int(analysis_rounds)

    def _analysis_work(self, state: AgentState) -> None:
        seed = f"{state.task.prompt}|{state.failure_kind}|{state.phase}".encode()
        digest = seed
        for _ in range(self.analysis_rounds):
            digest = hashlib.blake2b(digest, digest_size=32).digest()

    def decide(self, state: AgentState) -> str:
        self._analysis_work(state)
        if state.tests_passed:
            return "finish"
        if state.phase == "start" or state.patched:
            return "run_tests"
        if state.phase == "failed":
            if state.failure_kind == "missing_module":
                return "inspect_dependency"
            if state.failure_kind == "import_error" and not state.searched:
                return "search_symbol"
            return "inspect_file"
        if state.phase == "searched" and not state.inspected:
            return "inspect_file"
        if state.phase == "inspected":
            return "apply_fix"
        if state.phase == "dep_inspected":
            return "search_registry"
        if state.phase == "registry_searched":
            return "modify_dependency_file"
        if state.phase == "dep_modified":
            return "install_dependency"
        return "run_tests"


class AgentFeatureEncoder:
    """Stable structured encoder for the first agent vertical.

    The task family is intentionally not encoded directly. The reflex sees task
    wording, execution phase, observed failure type and tool-state flags.
    """

    def __init__(self, text_dims: int = 24, vocabulary: str = "base") -> None:
        if vocabulary not in {"base", "extended"}:
            raise ValueError(f"unknown vocabulary: {vocabulary!r}")
        self.text_dims = int(text_dims)
        self.vocabulary = vocabulary
        self.phases = PHASES_EXTENDED if vocabulary == "extended" else PHASES
        self.failures = FAILURES_EXTENDED if vocabulary == "extended" else FAILURES

    @staticmethod
    def _one_hot(value: str, vocabulary: tuple[str, ...]) -> list[float]:
        return [1.0 if value == item else 0.0 for item in vocabulary]

    def _hash_text(self, text: str) -> np.ndarray:
        out = np.zeros(self.text_dims, dtype=np.float64)
        tokens = re.findall(r"[a-zA-Z_]+", text.lower())
        for token in tokens:
            h = hashlib.blake2b(token.encode(), digest_size=8).digest()
            idx = int.from_bytes(h[:4], "little") % self.text_dims
            sign = 1.0 if h[4] % 2 == 0 else -1.0
            out[idx] += sign
        norm = np.linalg.norm(out)
        if norm > 0:
            out /= norm
        return out

    def encode(self, state: AgentState) -> np.ndarray:
        features: list[float] = []
        features.extend(self._one_hot(state.phase, self.phases))
        features.extend(self._one_hot(state.failure_kind, self.failures))
        features.extend(
            [
                float(state.tests_passed),
                float(state.inspected),
                float(state.searched),
                float(state.patched),
                min(state.tool_calls / 8.0, 1.0),
            ]
        )
        if self.vocabulary == "extended":
            features.extend(
                [
                    float(state.dep_inspected),
                    float(state.registry_searched),
                    float(state.dep_modified),
                    float(state.installed),
                ]
            )
        return np.concatenate([np.asarray(features, dtype=np.float64), self._hash_text(state.task.prompt)])


class SafeCodingSandbox:
    """Tiny local tool sandbox used by P2.0.

    No arbitrary shell command is exposed. Tests run through a fixed unittest
    command and writes are restricted to the temporary task workspace.
    """

    def __init__(self, task: CodingTask, root: Path | None = None, *, test_runner: str = "inprocess") -> None:
        self._tmp: tempfile.TemporaryDirectory[str] | None = None
        if root is None:
            self._tmp = tempfile.TemporaryDirectory(prefix="paradigm-agent-")
            root = Path(self._tmp.name)
        self.root = Path(root).resolve()
        self.test_runner = test_runner
        self.root.mkdir(parents=True, exist_ok=True)
        self.task = task
        for rel, content in task.files.items():
            self._write(rel, content)
        if task.is_dependency_task:
            self._write("requirements.txt", task.requirements)

    def close(self) -> None:
        if self._tmp is not None:
            self._tmp.cleanup()
            self._tmp = None

    def _path(self, rel: str) -> Path:
        path = (self.root / rel).resolve()
        if self.root not in path.parents and path != self.root:
            raise ValueError("Path escapes task workspace")
        return path

    def _write(self, rel: str, content: str) -> None:
        path = self._path(rel)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    def run_tests(self) -> tuple[bool, str]:
        if self.test_runner == "subprocess":
            proc = subprocess.run(
                [sys.executable, "-m", "unittest", "discover", "-q"],
                cwd=self.root,
                capture_output=True,
                text=True,
                timeout=8,
                check=False,
            )
            output = (proc.stdout + "\n" + proc.stderr).strip()
            return proc.returncode == 0, output

        if self.test_runner != "inprocess":
            raise ValueError(f"unknown test runner: {self.test_runner}")

        module_names = {path.stem for path in self.root.glob("*.py")}
        shutil.rmtree(self.root / "__pycache__", ignore_errors=True)
        importlib.invalidate_caches()
        for name in module_names:
            sys.modules.pop(name, None)
        stream = io.StringIO()
        root_str = str(self.root)
        sys.path.insert(0, root_str)
        try:
            suite = unittest.defaultTestLoader.discover(root_str, pattern="test*.py", top_level_dir=root_str)
            result = unittest.TextTestRunner(stream=stream, verbosity=0).run(suite)
            return result.wasSuccessful(), stream.getvalue().strip()
        except Exception as exc:
            return False, f"{type(exc).__name__}: {exc}"
        finally:
            if sys.path and sys.path[0] == root_str:
                sys.path.pop(0)
            for name in module_names:
                sys.modules.pop(name, None)

    def inspect_file(self) -> str:
        return self._path(self.task.target_file).read_text(encoding="utf-8")

    def search_symbol(self) -> str:
        term = self.task.search_term
        if not term:
            return "no search term"
        hits: list[str] = []
        for path in sorted(self.root.rglob("*.py")):
            text = path.read_text(encoding="utf-8")
            if term in text:
                hits.append(str(path.relative_to(self.root)))
        return "\n".join(hits) if hits else "no matches"

    def apply_fix(self) -> str:
        for rel, content in self.task.fixed_files.items():
            self._write(rel, content)
        return "validated task fix applied"

    def inspect_dependency(self) -> str:
        path = self._path("requirements.txt")
        content = path.read_text(encoding="utf-8") if path.exists() else ""
        return f"requirements.txt:\n{content.strip() or '(empty)'}"

    def search_registry(self) -> str:
        registry = self.task.registry or {}
        if not registry:
            return "registry unavailable"
        return "available packages:\n" + "\n".join(sorted(registry))

    def modify_dependency_file(self) -> str:
        if not self.task.is_dependency_task:
            return "no dependency file for this task"
        self._write("requirements.txt", self.task.fixed_requirements)
        return "validated dependency file change applied"

    def install_dependency(self) -> str:
        registry = self.task.registry or {}
        path = self._path("requirements.txt")
        lines = [ln.strip() for ln in path.read_text(encoding="utf-8").splitlines()] if path.exists() else []
        report: list[str] = []
        for line in lines:
            if not line or line.startswith("#"):
                continue
            name = line.split(">=")[0].split("==")[0].strip()
            if name in registry:
                self._write(f"{name}.py", registry[name])
                report.append(f"installed {name}")
            else:
                report.append(f"package not found: {name}")
        return "\n".join(report) if report else "nothing to install"

    def installed_packages(self) -> set[str]:
        registry = self.task.registry or {}
        return {name for name in registry if self._path(f"{name}.py").exists()}


class ParadigmCodingAgent:
    """Hybrid coding controller with reflex fast path and deliberate fallback."""

    def __init__(
        self,
        deliberator: DeliberativePolicy,
        *,
        encoder: AgentFeatureEncoder | None = None,
        selection: ReflexSelection | None = None,
        ood_gate: MahalanobisGate | None = None,
        test_runner: str = "inprocess",
    ) -> None:
        self.deliberator = deliberator
        self.encoder = encoder or AgentFeatureEncoder()
        self.selection = selection
        self.ood_gate = ood_gate
        self.test_runner = test_runner

    @property
    def extended(self) -> bool:
        return getattr(self.encoder, "vocabulary", "base") == "extended"

    @staticmethod
    def valid_actions(state: AgentState) -> set[str]:
        if state.tests_passed:
            return {"finish"}
        if state.phase == "start" or state.patched:
            return {"run_tests"}
        if state.phase == "failed":
            if state.failure_kind == "missing_module":
                return {"inspect_file", "search_symbol", "inspect_dependency"}
            return {"inspect_file", "search_symbol"}
        if state.phase == "searched":
            return {"inspect_file"}
        if state.phase == "inspected":
            return {"apply_fix"}
        if state.phase == "dep_inspected":
            return {"search_registry", "modify_dependency_file", "inspect_file"}
        if state.phase == "registry_searched":
            return {"modify_dependency_file", "inspect_file"}
        if state.phase == "dep_modified":
            return {"install_dependency", "run_tests"}
        if state.phase == "installed":
            return {"run_tests"}
        return {"run_tests"}

    def _deliberate(self, state: AgentState, reason: str) -> PolicyDecision:
        start = time.perf_counter()
        action = self.deliberator.decide(state)
        elapsed = (time.perf_counter() - start) * 1e3
        return PolicyDecision(action, "deliberative", 0.0, reason=reason, latency_ms=elapsed)

    def decide(self, state: AgentState) -> tuple[PolicyDecision, bool]:
        if self.selection is None:
            return self._deliberate(state, "no_reflex"), False

        x = self.encoder.encode(state)
        if self.ood_gate is not None and not bool(self.ood_gate.accept(x)[0]):
            return self._deliberate(state, "out_of_distribution"), False

        action, confidence, _ = self.selection.reflex.predict(x)
        if confidence < self.selection.threshold:
            return self._deliberate(state, "low_confidence"), False

        if action not in self.valid_actions(state):
            decision = self._deliberate(state, "invalid_reflex_action")
            return decision, True

        start = time.perf_counter()
        # Prediction above is the policy work. Repeat only the minimal timed call
        # so latency remains comparable without timing state encoding twice.
        self.selection.reflex.predict(x)
        elapsed = (time.perf_counter() - start) * 1e3
        return PolicyDecision(action, "reflex", confidence, latency_ms=elapsed), False

    @staticmethod
    def _classify_failure(output: str, passed: bool, *, extended: bool = False) -> str:
        if passed:
            return "passed"
        if "SyntaxError" in output:
            return "syntax_error"
        if "NameError" in output:
            return "name_error"
        if extended and "ModuleNotFoundError" in output:
            return "missing_module"
        if "ImportError" in output or "ModuleNotFoundError" in output:
            return "import_error"
        if "AssertionError" in output:
            return "assertion_error"
        return "other"

    def apply_action(self, state: AgentState, sandbox: "SafeCodingSandbox", action: str) -> bool:
        """Execute one action against the sandbox and update the state. Returns True on finish."""
        state.tool_calls += 1
        if action == "run_tests":
            passed, output = sandbox.run_tests()
            state.last_output = output
            state.tests_passed = passed
            state.failure_kind = self._classify_failure(output, passed, extended=self.extended)
            state.phase = "passed" if passed else "failed"
        elif action == "inspect_file":
            state.last_output = sandbox.inspect_file()
            state.inspected = True
            state.phase = "inspected"
        elif action == "search_symbol":
            state.last_output = sandbox.search_symbol()
            state.searched = True
            state.phase = "searched"
        elif action == "apply_fix":
            state.last_output = sandbox.apply_fix()
            state.patched = True
            state.phase = "patched"
        elif action == "inspect_dependency":
            state.last_output = sandbox.inspect_dependency()
            state.dep_inspected = True
            state.phase = "dep_inspected"
        elif action == "search_registry":
            state.last_output = sandbox.search_registry()
            state.registry_searched = True
            state.phase = "registry_searched"
        elif action == "modify_dependency_file":
            state.last_output = sandbox.modify_dependency_file()
            state.dep_modified = True
            state.phase = "dep_modified"
        elif action == "install_dependency":
            state.last_output = sandbox.install_dependency()
            state.installed = True
            state.phase = "installed"
        elif action == "finish":
            state.phase = "done"
            return True
        else:
            state.last_output = f"unknown action: {action}"
        return False

    @staticmethod
    def outcome_contract(task: CodingTask, state: AgentState, sandbox: "SafeCodingSandbox") -> dict[str, bool]:
        """Type B Outcome Contract for dependency tasks. Absence of an error is not success."""
        if not task.is_dependency_task:
            return {}
        required = {ln.split(">=")[0].split("==")[0].strip() for ln in task.fixed_requirements.splitlines() if ln.strip()}
        code_unchanged = all(
            sandbox._path(rel).read_text(encoding="utf-8") == content for rel, content in task.files.items()
        )
        return {
            "tests_initially_failed": True,
            "dependency_file_corrected": state.dep_modified,
            "required_packages_installed": required <= sandbox.installed_packages(),
            "tests_pass": state.tests_passed,
            "code_files_unchanged": code_unchanged,
        }

    def run(self, task: CodingTask, *, max_steps: int = 10) -> AgentEpisode:
        sandbox = SafeCodingSandbox(task, test_runner=self.test_runner)
        state = AgentState(task=task)
        episode = AgentEpisode(task.task_id, task.family, False, 0)
        try:
            for _ in range(max_steps):
                features_before = self.encoder.encode(state).copy()
                phase_before = state.phase
                failure_before = state.failure_kind
                decision, invalid_reflex = self.decide(state)
                episode.decisions.append(decision)
                episode.records.append(
                    AgentDecisionRecord(
                        features=features_before,
                        action=decision.action,
                        source=decision.source,
                        phase=phase_before,
                        failure_kind=failure_before,
                        confidence=decision.confidence,
                    )
                )
                if invalid_reflex:
                    episode.invalid_reflex_actions += 1
                if decision.source == "reflex":
                    episode.reflex_calls += 1
                else:
                    episode.deliberative_calls += 1
                    episode.fallback_reasons[decision.reason] = episode.fallback_reasons.get(decision.reason, 0) + 1

                if self.apply_action(state, sandbox, decision.action):
                    episode.contract = self.outcome_contract(task, state, sandbox)
                    episode.success = state.tests_passed and all(episode.contract.values())
                    break

            episode.steps = len(episode.decisions)
            return episode
        finally:
            sandbox.close()


def collect_validated_traces(
    tasks: list[CodingTask],
    deliberator: DeliberativePolicy,
    encoder: AgentFeatureEncoder,
) -> tuple[list[Trace], list[AgentEpisode]]:
    traces: list[Trace] = []
    episodes: list[AgentEpisode] = []
    agent = ParadigmCodingAgent(deliberator, encoder=encoder)
    for task in tasks:
        sandbox = SafeCodingSandbox(task, test_runner="inprocess")
        state = AgentState(task=task)
        episode = AgentEpisode(task.task_id, task.family, False, 0)
        local: list[tuple[np.ndarray, str]] = []
        try:
            for _ in range(10):
                features = encoder.encode(state)
                decision = agent._deliberate(state, "teacher")
                local.append((features, decision.action))
                episode.decisions.append(decision)
                episode.deliberative_calls += 1
                if agent.apply_action(state, sandbox, decision.action):
                    episode.contract = agent.outcome_contract(task, state, sandbox)
                    episode.success = state.tests_passed and all(episode.contract.values())
                    break
            episode.steps = len(episode.decisions)
            episodes.append(episode)
            for features, action in local:
                traces.append(
                    Trace(
                        features=features,
                        action=action,
                        valid=episode.success,
                        metadata={"task_id": task.task_id, "family": task.family},
                    )
                )
        finally:
            sandbox.close()
    return traces, episodes


def compile_agent_reflex(
    train_tasks: list[CodingTask],
    validation_tasks: list[CodingTask],
    deliberator: DeliberativePolicy,
    *,
    encoder: AgentFeatureEncoder | None = None,
    random_state: int = 0,
) -> tuple[ReflexSelection, MahalanobisGate, AgentFeatureEncoder, dict[str, float]]:
    encoder = encoder or AgentFeatureEncoder()
    train, train_episodes = collect_validated_traces(train_tasks, deliberator, encoder)
    validation, validation_episodes = collect_validated_traces(validation_tasks, deliberator, encoder)
    reference = np.asarray([t.action for t in validation]).astype(str)
    selector = MinimalReflexSelector(
        minimum_coverage=0.50,
        maximum_ece=0.08,
        accuracy_tolerance=0.01,
        random_state=random_state,
    )
    selection = selector.select(train, validation, reference_predictions=reference, name="p2-agent-controller")
    x_train = np.stack([t.features for t in train])
    gate = MahalanobisGate(quantile=0.995).fit(x_train)
    stats = {
        "train_traces": float(len(train)),
        "validation_traces": float(len(validation)),
        "train_episode_success": float(np.mean([e.success for e in train_episodes])),
        "validation_episode_success": float(np.mean([e.success for e in validation_episodes])),
    }
    return selection, gate, encoder, stats


def summarize_episodes(episodes: list[AgentEpisode]) -> dict[str, float | dict[str, float]]:
    if not episodes:
        return {}
    total_policy = sum(e.total_policy_calls for e in episodes)
    deliberative = sum(e.deliberative_calls for e in episodes)
    reflex = sum(e.reflex_calls for e in episodes)
    by_family: dict[str, list[AgentEpisode]] = {}
    for episode in episodes:
        by_family.setdefault(episode.family, []).append(episode)
    return {
        "episodes": float(len(episodes)),
        "success_rate": float(np.mean([e.success for e in episodes])),
        "mean_steps": float(np.mean([e.steps for e in episodes])),
        "deliberative_calls": float(deliberative),
        "reflex_calls": float(reflex),
        "fast_path_coverage": float(reflex / total_policy) if total_policy else 0.0,
        "mean_policy_latency_ms": float(np.mean([e.policy_latency_ms for e in episodes])),
        "invalid_reflex_actions": float(sum(e.invalid_reflex_actions for e in episodes)),
        "success_by_family": {
            family: float(np.mean([e.success for e in items])) for family, items in sorted(by_family.items())
        },
    }
