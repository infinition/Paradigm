"""Shadow sampling: route a pre-declared subset of reflex-eligible decisions to the teacher.

An active family stops producing teacher evidence once its reflex serves it. Shadow
sampling keeps a deterministic fraction of eligible decisions deliberative, with reason
``shadow_sample``, so verified fresh evidence keeps arriving. It changes evidence
collection only; no certification threshold is involved. The draw depends on the
seed, the episode index, the family and the step index, never on predictions or
outcomes, so a run is reproducible and the rate is declared in advance.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field


@dataclass(slots=True)
class ShadowSampler:
    seed: int = 20260917
    # (first_episode, last_episode, rate), inclusive bounds; episodes outside every band get 0.
    schedule: tuple[tuple[int, int, float], ...] = field(default_factory=tuple)

    @classmethod
    def parse(cls, spec: str, seed: int = 20260917) -> "ShadowSampler":
        """``"17-20:0.25,21-24:0.5,29-36:1.0"``."""
        bands = []
        for part in spec.split(","):
            part = part.strip()
            if not part:
                continue
            rng, rate = part.split(":")
            lo, hi = rng.split("-")
            bands.append((int(lo), int(hi), float(rate)))
        return cls(seed=int(seed), schedule=tuple(bands))

    def rate(self, episode_index: int) -> float:
        for lo, hi, p in self.schedule:
            if lo <= episode_index <= hi:
                return p
        return 0.0

    def draw(self, episode_index: int, family: str, step_index: int) -> float:
        key = f"{self.seed}|{episode_index}|{family}|{step_index}".encode("utf-8")
        digest = hashlib.sha256(key).digest()
        return int.from_bytes(digest[:8], "big") / float(1 << 64)

    def sample(self, episode_index: int, family: str, step_index: int) -> bool:
        p = self.rate(episode_index)
        return p > 0.0 and self.draw(episode_index, family, step_index) < p

    def to_dict(self) -> dict:
        return {"seed": self.seed, "schedule": [list(b) for b in self.schedule]}
