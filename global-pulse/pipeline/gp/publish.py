"""Etapa 7 — Publicacion: pulse-YYYYMMDD.json + relaciones + copia a la app."""
import json
import re
import shutil
import unicodedata
from datetime import datetime, timezone

from . import config

MAX_PER_CATEGORY = 4   # cuota de diversidad en el pulso publicado


def _fold_tokens(text: str) -> set[str]:
    text = unicodedata.normalize("NFKD", text.lower())
    text = "".join(c for c in text if not unicodedata.combining(c))
    return {t for t in re.findall(r"[a-z0-9]{4,}", text)}


def _same_event(a: dict, b: dict) -> bool:
    """Dos nodos son el mismo macro-evento si comparten actores o titulos."""
    act_a = {x.lower() for x in a.get("actores", [])}
    act_b = {x.lower() for x in b.get("actores", [])}
    if len(act_a & act_b) >= 2:
        return True
    ta, tb = _fold_tokens(a["titulo"]["es"]), _fold_tokens(b["titulo"]["es"])
    if not ta or not tb:
        return False
    return len(ta & tb) / len(ta | tb) >= 0.45


def _dedupe(nodes: list[dict], log) -> list[dict]:
    """Fusiona nodos duplicados (mismo evento partido en varios clusters):
    conserva el de mayor impacto y absorbe fuentes/imagenes del resto."""
    nodes = sorted(nodes, key=lambda n: (n.get("impacto") or 0), reverse=True)
    kept: list[dict] = []
    merged = 0
    for n in nodes:
        dup = next((k for k in kept if _same_event(k, n)), None)
        if dup is None:
            kept.append(n)
            continue
        merged += 1
        dup["fuentes"] = list(dict.fromkeys(dup["fuentes"] + n["fuentes"]))
        dup["imagenes"] = list(dict.fromkeys(
            dup.get("imagenes", []) + n.get("imagenes", [])))[:4]
        dup["referencias"] = (dup.get("referencias", [])
                              + n.get("referencias", []))[:config.MAX_REFS_PER_NODE]
    if merged:
        log(f"  Duplicados fusionados: {merged}")
    return kept


def _diverse_top(nodes: list[dict], limit: int) -> list[dict]:
    """Top por impacto con cuota por categoria; el remanente se llena por
    impacto puro si no alcanzan las categorias minoritarias."""
    nodes = sorted(nodes, key=lambda n: (n.get("impacto") or 0), reverse=True)
    picked, counts = [], {}
    for n in nodes:
        if len(picked) >= limit:
            break
        if counts.get(n["categoria"], 0) >= MAX_PER_CATEGORY:
            continue
        picked.append(n)
        counts[n["categoria"]] = counts.get(n["categoria"], 0) + 1
    for n in nodes:                      # relleno si quedaron huecos
        if len(picked) >= limit:
            break
        if n not in picked:
            picked.append(n)
    return picked


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
    publicables = _dedupe(publicables, log)
    publicables = _diverse_top(publicables, config.MAX_NODES_PER_PULSE)

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
