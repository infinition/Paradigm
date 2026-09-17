"""Deterministic temporality and actionability features for French requests (C4).

Implemented from the rules of ``results/intent_bench/PREREG_C4.md``, which were written
from French grammar before the extractor was applied to the dataset. Categories:
PAST_REFERENCE, CONDITIONAL, FUTURE, NOW, UNSPECIFIED, in that priority order; plus
``negated`` and ``actionable_now``.
"""

from __future__ import annotations

import re
import unicodedata

import numpy as np

CATEGORIES = ("NOW", "FUTURE", "PAST_REFERENCE", "CONDITIONAL", "UNSPECIFIED")


def _norm(text: str) -> str:
    t = unicodedata.normalize("NFD", text.lower())
    t = "".join(c for c in t if unicodedata.category(c) != "Mn")
    t = t.replace("’", "'")
    return " " + re.sub(r"\s+", " ", t).strip() + " "


PARTICIPLE = r"\w+(?:e|i|u|is|it|es|ee|ees|us|its)"
PAST = [
    rf"\b(?:tu as|t'as|ta|tu m'as|tu l'as) {PARTICIPLE}\b",
    r"\b(?:tu avais|t'avais|j'avais|tu m'avais|tu l'avais|tu nous avais)\b",
    r"\b(?:marchait|etait|fonctionnait|yavait|y avait|repondait|existait)\b",
    r"\bhier\b",
    r"\bdeja\b",
    r"\bavant\s*(?:\?|$)",
]
CONDITIONAL = [r"\bsi (?:tu|je|on|la|le|ca|c'est)\b", r"\bau cas ou\b", r"\bquand tu pourras\b"]
FUTURE = [
    r"\btu (?:me |te |le |la |les |nous |lui |m'|l')?\w+(?:ras|eras|iras|dras|ra|era|ira|dra)\b",
    r"\bje (?:te |le |la |les |lui |t'|l')?\w+rai\b",
    r"\bdemain\b",
    r"\bce soir\b",
    r"\bplus tard\b",
    r"\bapres\s*(?:\?|\.|,|$)",
    r"\bensuite\b",
    r"\bpas maintenant\b",
    r"\bdans (?:\d+|un|une|deux|trois|quatre|cinq|dix|quinze|vingt|trente|quelques) ?(?:min|minutes?|h|heures?|secondes?|jours?|semaines?)\b",
    r"\bquand (?:je|tu|il|elle|on|ca|c') ?\w* ?(?:\w+rai|\w+ras|\w+ra|aurai|auras|aura|serai|seras|sera)\b",
]
NOW = [r"\bmaintenant\b", r"\btout de suite\b", r"\bla maintenant\b", r"\bvite fait\b", r"\bimmediatement\b", r"\bdirect\b", r"\bla\s*(?:\?|\.|$)"]
TOUT_A_L_HEURE = r"\btout a l'heure\b"
NEGATION = [
    r"\bne? \w+ pas\b", r"\bn'\w+ pas\b", r"\bpas d[e']\b", r"\bsurtout pas\b", r"\bjamais\b", r"\baucune?\b",
    r"\b(?:prends?|fais|fait|cherche|touche|regarde|montre|ouvre|teste?|capture|utilise|va|vas|change|fais-en|lance|affiche|enregistre|verifie|check) (?:me |moi |le |la |les |y )?pas\b",
]


def _any(patterns: list[str], t: str) -> bool:
    return any(re.search(p, t) for p in patterns)


def temporal_category(text: str) -> str:
    t = _norm(text)
    past = _any(PAST, t)
    if past:
        return "PAST_REFERENCE"
    if _any(CONDITIONAL, t):
        return "CONDITIONAL"
    if _any(FUTURE, t) or re.search(TOUT_A_L_HEURE, t):
        return "FUTURE"
    if _any(NOW, t):
        return "NOW"
    return "UNSPECIFIED"


def negated(text: str) -> bool:
    return _any(NEGATION, _norm(text))


def features(text: str) -> dict[str, object]:
    cat = temporal_category(text)
    neg = negated(text)
    return {"temporal": cat, "negated": neg, "actionable_now": cat in ("NOW", "UNSPECIFIED") and not neg}


def vector(text: str, scale: float = 1.0) -> np.ndarray:
    f = features(text)
    v = np.zeros(7, dtype=np.float64)
    v[CATEGORIES.index(str(f["temporal"]))] = 1.0
    v[5] = float(bool(f["negated"]))
    v[6] = float(bool(f["actionable_now"]))
    return v * scale
