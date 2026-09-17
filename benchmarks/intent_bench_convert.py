"""Convert a pipe-separated part of the intent benchmark into its JSONL file, verbatim.

Line format: ``group | role | transformation | intent | text`` (``-`` for no transformation).
Usage: python benchmarks/intent_bench_convert.py <source> <input.txt> <output.jsonl>
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

CLASSES = {"CAPTURE_PERSON", "CHECK_CAMERA", "OPEN_CAMERA_NO_CAPTURE", "FIND_EXISTING_PHOTOS", "SCREENSHOT", "OTHER"}
ROLES = {"base", "variant", "hard_negative"}
TRANSFORMATIONS = {"negation", "temporal", "past_question", "object_change", "inspection_only"}


def main(source: str, src: Path, dst: Path) -> None:
    rows = []
    for n, line in enumerate(src.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        parts = [p.strip() for p in line.split("|")]
        if len(parts) != 5:
            raise SystemExit(f"line {n}: expected 5 fields, got {len(parts)}")
        group, role, transformation, intent, text = parts
        if role not in ROLES or intent not in CLASSES:
            raise SystemExit(f"line {n}: bad role or intent: {role} {intent}")
        transformation = None if transformation in ("-", "") else transformation
        if (role == "hard_negative") != (transformation is not None) or (transformation and transformation not in TRANSFORMATIONS):
            raise SystemExit(f"line {n}: transformation {transformation!r} inconsistent with role {role}")
        rows.append({"id": f"{source}-{len(rows) + 1:03d}", "group": group, "source": source, "role": role, "transformation": transformation, "intent": intent, "text": text})
    with dst.open("w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"{len(rows)} sentences, {len({r['group'] for r in rows})} groups -> {dst}")


if __name__ == "__main__":
    main(sys.argv[1], Path(sys.argv[2]), Path(sys.argv[3]))
