"""Assemble the 80 D1-language missions from the two frozen formulation batches.

Deterministic: the crossing plan, the bug rotation and the ordering are fixed in
PREREG.md and nothing here chooses anything. Run it twice and it produces the same
file and the same hash.
"""

from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).parent
SUFFIX = ("\n\nTu travailles dans le dossier {d}. N'installe rien, ne touche à rien en dehors "
          "de ce dossier, et ne modifie jamais le fichier de tests.")

# j mod 4 -> the two state families the formulation is crossed with
ROTATION = {0: ("S1", "S3"), 1: ("S2", "S4"), 2: ("S1", "S4"), 3: ("S2", "S3")}
KINDS = ("wrong_constant", "off_by_one", "missing_import")
BUG_TEXT = {
    "wrong_constant": "une constante fausse",
    "off_by_one": "une borne décalée d'un cran",
    "missing_import": "un import manquant",
}
PAIRS = (("wrong_constant", "off_by_one"), ("off_by_one", "missing_import"), ("wrong_constant", "missing_import"))

BUGGY = {
    "wrong_constant": "TAX_RATE = 0.17\n\ndef total(amount):\n    return round(amount * (1 + TAX_RATE), 2)\n",
    "off_by_one": "def sum_to(n):\n    return sum(range(n))\n",
    "missing_import": "def root(x):\n    return sqrt(x)\n",
}
CORRECT = {
    "wrong_constant": "TAX_RATE = 0.2\n\ndef total(amount):\n    return round(amount * (1 + TAX_RATE), 2)\n",
    "off_by_one": "def sum_to(n):\n    return sum(range(n + 1))\n",
    "missing_import": "from math import sqrt\n\n\ndef root(x):\n    return sqrt(x)\n",
}
TEST = {
    "wrong_constant": "import unittest\nfrom calc import total\n\nclass T(unittest.TestCase):\n    def test_total(self):\n        self.assertEqual(total(100), 120.0)\n",
    "off_by_one": "import unittest\nfrom calc import sum_to\n\nclass T(unittest.TestCase):\n    def test_sum(self):\n        self.assertEqual(sum_to(10), 55)\n",
    "missing_import": "import unittest\nfrom calc import root\n\nclass T(unittest.TestCase):\n    def test_root(self):\n        self.assertEqual(root(81), 9.0)\n",
}
# S4: the defect sits in a second module the mission has to find first.
UTIL_BUGGY = {
    "wrong_constant": "def rate():\n    return 0.17\n",
    "off_by_one": "def upto(n):\n    return range(n)\n",
    "missing_import": "def root(x):\n    return sqrt(x)\n",
}
UTIL_CALC = {
    "wrong_constant": "from util import rate\n\n\ndef total(amount):\n    return round(amount * (1 + rate()), 2)\n",
    "off_by_one": "from util import upto\n\n\ndef sum_to(n):\n    return sum(upto(n))\n",
    "missing_import": "from util import root\n\n\ndef compute_root(x):\n    return root(x)\n",
}
UTIL_TEST = {
    "wrong_constant": TEST["wrong_constant"],
    "off_by_one": TEST["off_by_one"],
    "missing_import": "import unittest\nfrom calc import compute_root\n\nclass T(unittest.TestCase):\n    def test_root(self):\n        self.assertEqual(compute_root(81), 9.0)\n",
}


def workspace(state: str, kind: str, pair: tuple[str, str]) -> dict[str, str]:
    if state == "S1":
        return {"calc.py": BUGGY[kind], "test_calc.py": TEST[kind]}
    if state == "S2":
        return {"calc.py": CORRECT[kind], "test_calc.py": TEST[kind]}
    if state == "S3":
        a, b = pair
        return {
            "calc.py": BUGGY[a] + "\n" + BUGGY[b],
            "test_calc.py": TEST[a] + "\n" + TEST[b].replace("class T(", "class T2("),
        }
    return {"calc.py": UTIL_CALC[kind], "util.py": UTIL_BUGGY[kind], "test_calc.py": UTIL_TEST[kind]}


def main() -> int:
    forms = []
    for src in ("gen_a", "gen_b"):
        forms += json.loads((HERE / f"formulations_{src}.json").read_text(encoding="utf-8"))["formulations"]
    forms.sort(key=lambda f: (f["intention"], f["j"]))

    missions, n = [], 0
    for f in forms:
        for state in ROTATION[f["j"] % 4]:
            kind = KINDS[n % 3]
            pair = PAIRS[n % 3]
            bug_kind = pair[0] if state == "S3" else kind
            text = f["text"].replace("{bug}", BUG_TEXT[bug_kind])
            missions.append({
                "n": n + 1,
                "formulation_id": f["id"],
                "source": f["id"].split("-")[0],
                "intention": f["intention"],
                "state_family": state,
                "bug_kind": None if state == "S2" else (list(pair) if state == "S3" else kind),
                "slot_filled_with": BUG_TEXT[bug_kind] if "{bug}" in f["text"] else None,
                "prompt": text + SUFFIX,
                "files": workspace(state, kind, pair),
            })
            n += 1

    out = {
        "collection": "d1_language",
        "prereg": "results/d1_language/PREREG.md",
        "total_missions": len(missions),
        "constant_suffix": SUFFIX,
        "rotation": {str(k): list(v) for k, v in ROTATION.items()},
        "missions": missions,
    }
    (HERE / "missions.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"wrote {len(missions)} missions")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
