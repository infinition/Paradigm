"""C6 scorers, frozen: NLI entailment and instruction-aware reranking between a request and
the five action contracts of ``PREREG_C6.md``. Both models frozen, CPU.
"""

from __future__ import annotations

import time

import numpy as np
import torch

CONTRACTS = {
    "camera.capture": "L'utilisateur demande qu'une photo de lui soit prise maintenant.",
    "camera.list": "L'utilisateur demande de vérifier la présence, la disponibilité ou le fonctionnement d'une caméra, sans prendre de photo.",
    "camera.preview": "L'utilisateur demande de montrer l'image d'une caméra maintenant, sans enregistrer de photo.",
    "photos.find": "L'utilisateur demande de retrouver des photos déjà existantes.",
    "screen.capture": "L'utilisateur demande une capture de l'écran ou d'une fenêtre maintenant.",
}
NLI_MODEL = "MoritzLaurer/mDeBERTa-v3-base-mnli-xnli"
RERANK_MODEL = "Qwen/Qwen3-Reranker-0.6B"
INSTRUCTION = (
    "Indique si l'action candidate doit être exécutée maintenant d'après la demande de l'utilisateur. "
    "Une demande au futur, une question sur le passé, une négation ou une simple demande d'observation n'autorisent pas l'exécution."
)


class NLIScorer:
    """P(entailment) and P(contradiction) for each contract: 10 dimensions."""

    def __init__(self) -> None:
        from transformers import AutoModelForSequenceClassification, AutoTokenizer

        self.tok = AutoTokenizer.from_pretrained(NLI_MODEL)
        self.model = AutoModelForSequenceClassification.from_pretrained(NLI_MODEL).eval()
        labels = {v.lower(): k for k, v in self.model.config.id2label.items()}
        self.i_ent, self.i_con = labels["entailment"], labels["contradiction"]

    @torch.no_grad()
    def score(self, text: str) -> tuple[np.ndarray, dict[str, dict[str, float]], float]:
        t0 = time.perf_counter()
        out = np.zeros(2 * len(CONTRACTS))
        detail = {}
        for k, (name, hyp) in enumerate(CONTRACTS.items()):
            enc = self.tok(text, hyp, return_tensors="pt", truncation=True)
            p = torch.softmax(self.model(**enc).logits[0], dim=-1).numpy()
            out[2 * k], out[2 * k + 1] = float(p[self.i_ent]), float(p[self.i_con])
            detail[name] = {"entailment": float(p[self.i_ent]), "contradiction": float(p[self.i_con])}
        return out, detail, (time.perf_counter() - t0) * 1000


class RerankScorer:
    """One score per contract: P(yes) against P(no) at the last position, as in the model card."""

    def __init__(self) -> None:
        from transformers import AutoModelForCausalLM, AutoTokenizer

        self.tok = AutoTokenizer.from_pretrained(RERANK_MODEL, padding_side="left")
        self.model = AutoModelForCausalLM.from_pretrained(RERANK_MODEL, dtype=torch.float32).eval()
        self.yes = self.tok.convert_tokens_to_ids("yes")
        self.no = self.tok.convert_tokens_to_ids("no")
        self.prefix = "<|im_start|>system\nJudge whether the Document meets the requirements based on the Query and the Instruct provided. Note that the answer can only be \"yes\" or \"no\".<|im_end|>\n<|im_start|>user\n"
        self.suffix = "<|im_end|>\n<|im_start|>assistant\n<think>\n\n</think>\n\n"

    @torch.no_grad()
    def score(self, text: str) -> tuple[np.ndarray, dict[str, float], float]:
        t0 = time.perf_counter()
        prompts = [f"{self.prefix}<Instruct>: {INSTRUCTION}\n<Query>: {text}\n<Document>: {hyp}{self.suffix}" for hyp in CONTRACTS.values()]
        enc = self.tok(prompts, return_tensors="pt", padding=True)
        logits = self.model(**enc).logits[:, -1, :]
        pair = torch.stack([logits[:, self.no], logits[:, self.yes]], dim=1)
        p_yes = torch.softmax(pair, dim=1)[:, 1].numpy()
        detail = {name: float(p_yes[k]) for k, name in enumerate(CONTRACTS)}
        return p_yes.astype(np.float64), detail, (time.perf_counter() - t0) * 1000
