"""Extractor version 2 (C4b): version 1 plus temporal subordinate clauses and the indirect
question exception for ``si``. Implemented from ``PREREG_C4B.md``; version 1 is untouched.
"""

from __future__ import annotations

import re

import numpy as np

from intent_temporal_fr import CATEGORIES, CONDITIONAL, FUTURE, NOW, PAST, TOUT_A_L_HEURE, _any, _norm, negated

# A temporal subordinate that defers the main clause, whatever the tense inside it.
SUBORDINATE = [
    r"\b(?:quand|lorsque|des que|une fois que|apres que|aussitot que|sitot que|au moment ou|le jour ou) (?:je|j'|tu|t'|il|elle|on|nous|vous|ils|elles|ce|c'|ca|la|le|les|mon|ma|mes|ton|ta|tes)\b",
    r"\battends? (?:que|de|d'|avant de|avant d')\b",
    r"\bavant de (?:me |te |le |la |les |lui )?\w+(?:er|ir|re|dre|oir)\b",
    r"\bapres (?:avoir|etre) \w+\b",
]
# "quand" as an interrogative about time is not a deferral.
QUAND_QUESTION = [r"\bquand est-ce que\b", r"\bc'est quand\b", r"\bquand\s*\?"]
# "si" right after a verb of perception, verification or saying is an indirect question.
INDIRECT_SI = r"\b(?:regarde|regardez|verifie|verifiez|dis-moi|dis moi|dites-moi|indique-moi|indique moi|check|checke|sais|savoir|voir|test|teste|vois|confirme|confirme-moi|confirme moi) (?:un peu |juste |vite fait |seulement |simplement |bien |donc )?si\b"


SUBORDINATE_CLAUSE = r"\b(?:quand|lorsque|des que|une fois que|apres que|aussitot que|sitot que|au moment ou|le jour ou|attends? (?:que|de|d'|avant de|avant d')|avant de|apres (?:avoir|etre))\b[^,?.!]*"


def _main_clause(t: str) -> str:
    """The sentence without its temporal subordinate clause: the tense that decides between a
    deferral and a past reference is the main clause's, whatever the subordinate's."""
    return re.sub(SUBORDINATE_CLAUSE, " ", t)


def temporal_category_v2(text: str) -> str:
    t = _norm(text)
    deferral = _any(SUBORDINATE, t) and not _any(QUAND_QUESTION, t)
    if _any(PAST, _main_clause(t) if deferral else t):
        return "PAST_REFERENCE"
    conditional = _any(CONDITIONAL, t) or bool(re.search(r"\bsi jamais\b", t))
    if conditional and re.search(INDIRECT_SI, t) and not re.search(r"(?:^|,) ?si (?:tu|je|on|la|le|ca|c'est|jamais)\b", t):
        conditional = False
    if conditional:
        return "CONDITIONAL"
    if deferral or _any(FUTURE, t) or re.search(TOUT_A_L_HEURE, t):
        return "FUTURE"
    if _any(NOW, t):
        return "NOW"
    return "UNSPECIFIED"


def features_v2(text: str) -> dict[str, object]:
    cat = temporal_category_v2(text)
    neg = negated(text)
    return {"temporal": cat, "negated": neg, "actionable_now": cat in ("NOW", "UNSPECIFIED") and not neg}


def vector_v2(text: str, scale: float = 1.0) -> np.ndarray:
    f = features_v2(text)
    v = np.zeros(7, dtype=np.float64)
    v[CATEGORIES.index(str(f["temporal"]))] = 1.0
    v[5] = float(bool(f["negated"]))
    v[6] = float(bool(f["actionable_now"]))
    return v * scale
