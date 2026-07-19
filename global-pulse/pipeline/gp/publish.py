"""Etapa 7 — Publicacion: pulse-YYYYMMDD.json + relaciones + copia a la app."""
import json
import shutil
from datetime import datetime, timezone

from . import config


def _relaciones(nodes: list[dict]) -> None:
    """Enlaza nodos que comparten actores o region (grafo de la Capa 1)."""
    for n in nodes:
        n["relaciones"] = []
    for i, a in enumerate(nodes):
        ents_a = {x.lower() for x in a.get("actores", [])}
        for b in nodes[i + 1:]:
            ents_b = {x.lower() for x in b.get("actores", [])}
            same_region = (a["geo"]["region"] == b["geo"]["region"]
                           and a["geo"]["region"] != "Global")
            if ents_a & ents_b or same_region:
                a["relaciones"].append(b["id"])
                b["relaciones"].append(a["id"])


def run(nodes: list[dict], mode: str, engine: str, metrics: dict,
        log=print) -> dict:
    log("[7/8] Publicacion")
    today = datetime.now(timezone.utc)
    fecha = today.strftime("%Y-%m-%d")

    publicables = [n for n in nodes
                   if n["estado"] == "sin_verificar"
                   or (n.get("impacto") or 0) >= config.IMPACT_THRESHOLD]
    publicables.sort(key=lambda n: (n.get("impacto") or 0), reverse=True)
    publicables = publicables[:config.MAX_NODES_PER_PULSE]

    from .brain import classify_kardashev
    for i, n in enumerate(publicables):
        n["id"] = f"nd_{fecha}_{i:04d}"
        n["fecha"] = fecha
        n["kardashev"] = classify_kardashev(n)   # escala civilizatoria K0-K3
    _relaciones(publicables)

    pulse = {
        "meta": {
            "schema": config.SCHEMA_VERSION,
            "fecha": fecha,
            "generado": today.isoformat(),
            "modo": mode,                    # live | fixture(demo)
            "motor_sintesis": engine,
            "metricas": metrics,
            "descargo": ("Datos de demostracion basados en cobertura publica; "
                         "ejecutar en modo live para ingesta en tiempo real")
                        if mode == "fixture" else "",
        },
        "nodos": publicables,
    }

    config.DATA_DIR.mkdir(parents=True, exist_ok=True)
    daily = config.DATA_DIR / f"pulse-{fecha.replace('-', '')}.json"
    daily.write_text(json.dumps(pulse, ensure_ascii=False, indent=2),
                     encoding="utf-8")
    latest = config.DATA_DIR / "pulse-latest.json"
    shutil.copyfile(daily, latest)

    # Copia para la PWA
    config.APP_DATA_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(daily, config.APP_DATA_DIR / "pulse-latest.json")

    log(f"  Publicados {len(publicables)} nodos -> {daily.name} (+ latest, + app)")
    return pulse
