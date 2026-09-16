from __future__ import annotations

from .agent_vertical import CodingTask

PROMPTS = {
    "missing_import": [
        "The square root helper fails at runtime. Run the tests and repair the implementation.",
        "Fix the math helper so its unit test passes.",
        "A numeric utility raises a runtime name error. Diagnose it and make the tests green.",
        "Repair the root calculation in this small Python project.",
    ],
    "wrong_constant": [
        "The pricing total is wrong. Run the tests and correct the implementation.",
        "Fix the tax calculation so the expected total is returned.",
        "A configuration constant produces an incorrect price. Repair it.",
        "The billing unit test is failing because the computed total is incorrect.",
    ],
    "renamed_symbol": [
        "The application cannot import a renamed helper. Find the current symbol and repair the call site.",
        "Fix the broken helper import after a rename.",
        "A public function was renamed and the application still uses the previous name.",
        "Repair the import failure caused by a renamed normalization function.",
    ],
    "off_by_one": [
        "The sequence helper misses the final value. Run the tests and fix the boundary.",
        "Repair an off by one error in the integer summation helper.",
        "The range boundary is wrong and the test result is too small.",
        "Fix the inclusive sum implementation.",
    ],
    "syntax_error": [
        "The module no longer imports because of malformed Python syntax. Diagnose and repair it.",
        "Fix the parser error in the increment helper and make the tests pass.",
        "A recent edit left the Python file syntactically invalid. Repair it.",
        "Run the tests, locate the syntax problem and restore a valid module.",
    ],
    "dependency_error": [
        "The service cannot start because a third-party package is unavailable. Resolve the dependency and make the tests pass.",
        "Tests fail with a missing module. Fix the project dependencies so the suite runs.",
        "A required library is not installed in this workspace. Repair the dependency declaration and install it.",
        "The import of an external package fails. Correct the dependency setup and get the tests green.",
    ],
}


def make_task(family: str, index: int) -> CodingTask:
    prompt = PROMPTS[family][index % len(PROMPTS[family])]
    suffix = index % 7
    if family == "missing_import":
        files = {
            "calc.py": f"def root_{suffix}(x):\n    return sqrt(x)\n",
            "test_calc.py": f"import unittest\nfrom calc import root_{suffix}\n\nclass T(unittest.TestCase):\n    def test_root(self):\n        self.assertEqual(root_{suffix}(81), 9)\n",
        }
        fixed = dict(files)
        fixed["calc.py"] = f"from math import sqrt\n\ndef root_{suffix}(x):\n    return sqrt(x)\n"
        return CodingTask(f"missing-{index}", family, prompt, files, fixed, "calc.py", "sqrt")

    if family == "wrong_constant":
        expected = 0.20 + (suffix * 0.01)
        wrong = expected - 0.03
        files = {
            "pricing.py": f"TAX_RATE = {wrong:.2f}\n\ndef total(x):\n    return round(x * (1 + TAX_RATE), 2)\n",
            "test_pricing.py": f"import unittest\nfrom pricing import total\n\nclass T(unittest.TestCase):\n    def test_total(self):\n        self.assertEqual(total(100), {100 * (1 + expected):.2f})\n",
        }
        fixed = dict(files)
        fixed["pricing.py"] = f"TAX_RATE = {expected:.2f}\n\ndef total(x):\n    return round(x * (1 + TAX_RATE), 2)\n"
        return CodingTask(f"constant-{index}", family, prompt, files, fixed, "pricing.py", "TAX_RATE")

    if family == "renamed_symbol":
        new = f"normalize_name_{suffix}"
        old = f"normalise_name_{suffix}"
        files = {
            "library.py": f"def {new}(value):\n    return value.strip().lower()\n",
            "app.py": f"from library import {old}\n\ndef clean(value):\n    return {old}(value)\n",
            "test_app.py": "import unittest\nfrom app import clean\n\nclass T(unittest.TestCase):\n    def test_clean(self):\n        self.assertEqual(clean('  Ada  '), 'ada')\n",
        }
        fixed = dict(files)
        fixed["app.py"] = f"from library import {new}\n\ndef clean(value):\n    return {new}(value)\n"
        return CodingTask(f"rename-{index}", family, prompt, files, fixed, "app.py", new)

    if family == "off_by_one":
        files = {
            "sequence.py": f"def sum_to_{suffix}(n):\n    return sum(range(n))\n",
            "test_sequence.py": f"import unittest\nfrom sequence import sum_to_{suffix}\n\nclass T(unittest.TestCase):\n    def test_sum(self):\n        self.assertEqual(sum_to_{suffix}(10), 55)\n",
        }
        fixed = dict(files)
        fixed["sequence.py"] = f"def sum_to_{suffix}(n):\n    return sum(range(n + 1))\n"
        return CodingTask(f"offbyone-{index}", family, prompt, files, fixed, "sequence.py", "range")

    if family == "syntax_error":
        files = {
            "broken.py": f"def increment_{suffix}(x):\n    return (x + 1\n",
            "test_broken.py": f"import unittest\nfrom broken import increment_{suffix}\n\nclass T(unittest.TestCase):\n    def test_increment(self):\n        self.assertEqual(increment_{suffix}(4), 5)\n",
        }
        fixed = dict(files)
        fixed["broken.py"] = f"def increment_{suffix}(x):\n    return x + 1\n"
        return CodingTask(f"syntax-{index}", family, prompt, files, fixed, "broken.py", "increment")

    if family == "dependency_error":
        pkg = f"fastjson_{suffix}"
        decoy = f"slowjson_{suffix}"
        files = {
            "service.py": f"import {pkg}\n\ndef encode(payload):\n    return {pkg}.dumps(payload)\n",
            "test_service.py": "import unittest\nfrom service import encode\n\nclass T(unittest.TestCase):\n    def test_encode(self):\n        self.assertEqual(encode({'a': 1}), \"{'a': 1}\")\n",
        }
        registry = {
            pkg: "def dumps(payload):\n    return str(payload)\n",
            decoy: "def dumps(payload):\n    raise RuntimeError('wrong package')\n",
        }
        # Two declaration defects: a misspelled package name, or no declaration at all.
        requirements = f"fast-json-{suffix}>=1.0\n" if index % 2 == 0 else "# no dependencies declared\n"
        return CodingTask(
            f"dependency-{index}",
            family,
            prompt,
            files,
            dict(files),
            "service.py",
            pkg,
            registry=registry,
            requirements=requirements,
            fixed_requirements=f"{pkg}>=1.0\n",
        )

    raise ValueError(f"unknown family: {family}")


def make_split(start: int, per_family: int, *, include_ood: bool = False) -> list[CodingTask]:
    families = ["missing_import", "wrong_constant", "renamed_symbol", "off_by_one"]
    tasks = [make_task(family, start + i) for family in families for i in range(per_family)]
    if include_ood:
        tasks.extend(make_task("syntax_error", start + i) for i in range(max(2, per_family // 2)))
    return tasks
