#!/usr/bin/env python3
"""
Orquestador Global Pulse — sustituye a n8n.

Encadena las 8 etapas del blueprint con reintentos, fallo aislado y metricas.
Disenado para ejecutarse por Claude Code, cron local o GitHub Actions.

Uso:
  python orchestrator.py run [--mode live|fixture] [--synth auto|api|heuristic]
  python orchestrator.py run --mode fixture          # demo sin red
"""
import argparse
import json
import sys
import time
from datetime import datetime, timezone

from gp import collect, normalize, cluster, synthesize, validate, publish, promote
from gp import config

RETRIES = 3
BACKOFF = 2  # segundos, exponencial


def log(msg: str) -> None:
    print(msg, flush=True)


def _with_retry(fn, *args, **kw):
    last = None
    for attempt in range(RETRIES):
        try:
            return fn(*args, **kw)
        except Exception as e:  # noqa: BLE001 — reintento generico deliberado
            last = e
            wait = BACKOFF * (2 ** attempt)
            log(f"  Reintento {attempt + 1}/{RETRIES} en {wait}s ({e})")
            time.sleep(wait)
    raise last


def run_cycle(mode: str, synth_mode: str) -> dict:
    t0 = time.time()
    log(f"=== Global Pulse · ciclo {datetime.now(timezone.utc).isoformat()} ===")

    pieces = _with_retry(collect.run, mode, log)
    if not pieces:
        log("Sin piezas recolectadas; se conserva el ultimo pulso valido.")
        sys.exit(0)

    pieces = normalize.normalize(pieces, log)
    pieces = normalize.dedup(pieces, log)
    clusters = cluster.run(pieces, log)
    nodes = synthesize.run(clusters, synth_mode, log)
    nodes = validate.run(nodes, pieces, log)

    metrics = {
        "piezas_ingeridas": len(pieces),
        "clusters": len(clusters),
        "nodos": len(nodes),
        "verificados": sum(1 for n in nodes if n["estado"] == "verificado"),
        "duracion_s": round(time.time() - t0, 1),
    }
    engine = ("api" if synth_mode == "api" else
              "heuristic" if synth_mode == "heuristic" else
              ("api" if __import__("os").environ.get("ANTHROPIC_API_KEY")
               else "heuristic"))
    pulse = publish.run(nodes, mode, engine, metrics, log)
    promovidas = promote.run(pulse["nodos"], log)
    metrics["promovidas"] = promovidas

    log(f"=== Ciclo completo en {metrics['duracion_s']}s · "
        f"{metrics['nodos']} nodos ({metrics['verificados']} verificados) ===")
    return pulse


def main() -> None:
    ap = argparse.ArgumentParser(description="Orquestador Global Pulse")
    sub = ap.add_subparsers(dest="cmd", required=True)
    runp = sub.add_parser("run", help="ejecuta el ciclo completo")
    runp.add_argument("--mode", choices=["live", "fixture"], default="live")
    runp.add_argument("--synth", choices=["auto", "api", "heuristic"],
                      default="auto")
    args = ap.parse_args()
    if args.cmd == "run":
        run_cycle(args.mode, args.synth)


if __name__ == "__main__":
    main()
