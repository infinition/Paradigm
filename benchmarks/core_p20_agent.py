from pathlib import Path

from paradigm.p20 import run_p20_benchmark, write_p20_results


if __name__ == "__main__":
    result = run_p20_benchmark()
    root = Path("results/core_p20")
    write_p20_results(root, result)
    print(root / "REPORT.md")
