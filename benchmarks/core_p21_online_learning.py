from pathlib import Path

from paradigm.p21 import run_p21_benchmark, write_p21_results


if __name__ == "__main__":
    result = run_p21_benchmark()
    root = Path(__file__).resolve().parents[1] / "results" / "core_p21"
    write_p21_results(root, result)
    print(root / "REPORT.md")
