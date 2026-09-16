from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .p24 import run_p24_benchmark, summarize_p24_payload

P24_ARTIFACT = "core_p24_type_b.json"


def _find_results_dir(explicit: str | None, name: str) -> Path | None:
    """Locate a results directory: explicit path, then the working directory, then upward from the package."""
    if explicit:
        path = Path(explicit)
        return path if (path / P24_ARTIFACT).exists() else None
    candidates = [Path.cwd() / "results" / name]
    here = Path(__file__).resolve()
    for parent in here.parents:
        candidates.append(parent / "results" / name)
    for c in candidates:
        if (c / P24_ARTIFACT).exists():
            return c
    return None


def _benchmark_p24(args: argparse.Namespace) -> int:
    if args.from_cache:
        root = _find_results_dir(args.results, "core_p24")
        if root is None:
            print("No recorded P2.4 artifact found. Pass --results <dir> containing core_p24_type_b.json.", file=sys.stderr)
            return 2
        payload = json.loads((root / P24_ARTIFACT).read_text(encoding="utf-8"))
        sys.stdout.write(summarize_p24_payload(payload))
        return 0
    if not args.model:
        print(
            "A live run needs at least one --model 'name|api_style|base_url' and a reachable endpoint. "
            "Use --from-cache to print the recorded result without any model.",
            file=sys.stderr,
        )
        return 2
    payload = run_p24_benchmark(
        models=args.model,
        orderings=args.orderings,
        online=args.online,
        output=args.results or "results/core_p24",
        log=lambda m: print(m, flush=True),
    )
    sys.stdout.write(summarize_p24_payload(payload))
    return 0


def _serve(args: argparse.Namespace) -> int:
    from .integration.engine import Paradigm
    from .integration.laruche import LaRucheAdapter
    from .integration.service import ParadigmService, serve

    adapter = LaRucheAdapter()
    state_file = Path(args.state_file) if args.state_file else None
    if state_file is not None and state_file.exists():
        engine = Paradigm.load(state_file, policy=adapter.policy())
    else:
        engine = Paradigm(policy=adapter.policy())
    adapter.templates = engine.action_templates  # one shared template map, persisted with the engine
    if args.certification:
        # Certification rule is a deployment choice; thresholds are unchanged either way.
        engine.compiler.certification = args.certification
        engine.compiler.shadow_certification = None if args.certification == "family_scoped" else ("recent" if args.certification == "family_aware" else "family_aware")
    service = ParadigmService(engine, state_file=state_file, adapter=adapter)
    server = serve(service, host=args.host, port=args.port)
    print(f"paradigm service listening on http://{args.host}:{args.port} (active reflex version {engine.compiler.state.version})", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
        if state_file is not None:
            engine.save(state_file)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="paradigm", description="Paradigm: validated deliberation to trusted reflexes")
    sub = parser.add_subparsers(dest="command", required=True)
    bench = sub.add_parser("benchmark", help="run or replay a recorded benchmark")
    bench_sub = bench.add_subparsers(dest="benchmark", required=True)
    p24 = bench_sub.add_parser("p24", help="P2.4 Type B procedural skill acquisition")
    p24.add_argument("--from-cache", action="store_true", help="print the recorded result from committed artifacts; no model endpoint needed")
    p24.add_argument("--model", action="append", help="model|api_style|base_url (repeatable) for a live run")
    p24.add_argument("--orderings", type=int, default=5)
    p24.add_argument("--online", action="store_true", help="run the online loop when the offline sweep shows acquisition")
    p24.add_argument("--results", help="results directory (default: results/core_p24)")
    p24.set_defaults(func=_benchmark_p24)
    srv = sub.add_parser("serve", help="run the local integration service (JSON over HTTP)")
    srv.add_argument("--host", default="127.0.0.1")
    srv.add_argument("--port", type=int, default=8765)
    srv.add_argument("--state-file", help="pickle file to load and persist the engine state")
    srv.add_argument("--certification", choices=("recent", "family_aware", "family_scoped"), help="promotion rule (default: family_aware with recent in shadow)")
    srv.set_defaults(func=_serve)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
