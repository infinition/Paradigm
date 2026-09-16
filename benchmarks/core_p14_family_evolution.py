from __future__ import annotations

import json
from pathlib import Path

from paradigm.p14 import run_p14_benchmark


ROOT = Path(__file__).resolve().parents[1]
RESULT_DIR = ROOT / "results" / "core_p14"


def main() -> None:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    payload = run_p14_benchmark(RESULT_DIR / "family_store")
    (RESULT_DIR / "core_p14_family_evolution.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(payload["observed"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
