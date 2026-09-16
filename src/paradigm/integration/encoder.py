from __future__ import annotations

import hashlib
import re

import numpy as np

from .contract import ParadigmState


class GenericStateEncoder:
    """Fixed-width, teacher-independent encoding of a ParadigmState by feature hashing.

    Categorical facts (phase, last action, last outcome, available and recent actions,
    domain, risk, string features) become signed hashed indicators; numeric and boolean
    features are hashed into a separate block; goal tokens are hashed like the coding
    vertical's prompt hash. The same state always maps to the same vector.
    """

    def __init__(self, categorical_dims: int = 96, numeric_dims: int = 16, text_dims: int = 24) -> None:
        self.categorical_dims = int(categorical_dims)
        self.numeric_dims = int(numeric_dims)
        self.text_dims = int(text_dims)
        self.vocabulary = "generic"

    @property
    def dims(self) -> int:
        return self.categorical_dims + self.numeric_dims + self.text_dims + 1

    @staticmethod
    def _slot(token: str, dims: int) -> tuple[int, float]:
        h = hashlib.blake2b(token.encode("utf-8"), digest_size=8).digest()
        return int.from_bytes(h[:4], "little") % dims, (1.0 if h[4] % 2 == 0 else -1.0)

    def encode(self, state: ParadigmState) -> np.ndarray:
        cat = np.zeros(self.categorical_dims, dtype=np.float64)
        tokens = [
            f"domain={state.domain}",
            f"phase={state.phase}",
            f"last_action={state.last_action}",
            f"last_outcome={state.last_outcome}",
            f"risk={state.risk}",
        ]
        tokens += [f"available={a}" for a in state.available_actions]
        tokens += [f"recent{i}={a}" for i, a in enumerate(state.recent_actions[-3:])]
        for key, value in sorted(state.features.items()):
            if isinstance(value, str):
                tokens.append(f"{key}={value}")
        for token in tokens:
            idx, sign = self._slot(token, self.categorical_dims)
            cat[idx] += sign
        num = np.zeros(self.numeric_dims, dtype=np.float64)
        for key, value in sorted(state.features.items()):
            if isinstance(value, bool):
                idx, sign = self._slot(f"flag:{key}", self.numeric_dims)
                num[idx] += sign * float(value)
            elif isinstance(value, (int, float)):
                idx, sign = self._slot(f"num:{key}", self.numeric_dims)
                num[idx] += sign * float(np.clip(float(value), -1e3, 1e3))
        text = np.zeros(self.text_dims, dtype=np.float64)
        for word in re.findall(r"[a-zA-Z_]+", state.goal.lower()):
            idx, sign = self._slot(f"goal:{word}", self.text_dims)
            text[idx] += sign
        norm = np.linalg.norm(text)
        if norm > 0:
            text /= norm
        step = np.asarray([min(state.step / 16.0, 1.0)], dtype=np.float64)
        return np.concatenate([cat, num, text, step])
