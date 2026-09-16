"""Run P2.2 against any OpenAI-compatible local or remote endpoint.

Example with llama.cpp server:

    PARADIGM_LLM_BASE_URL=http://127.0.0.1:8080/v1 \\
    PARADIGM_LLM_MODEL=qwen \\
    python benchmarks/core_p22_llm.py --quick
"""

from paradigm.llm_controller import OpenAICompatibleCodingDeliberator
from paradigm.p22 import run_p22_live_benchmark

controller = OpenAICompatibleCodingDeliberator.from_env()
result = run_p22_live_benchmark(controller, quick=True)
print(result["evaluation"])
