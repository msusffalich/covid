"""Etapa 7 — Publicacion: pulse-YYYYMMDD.json + relaciones + copia a la app."""
import json
import re
import shutil
import unicodedata
from datetime import datetime, timezone

from . import config
from .topics import compatible_events

MAX_PER_CATEGORY = 4   # cuota de diversidad en el pulso publicado


def _fold_tokens(text: str) -> set[str]:
    text = unicodedata.normalize("NFKD", text.lower())
    text = "".join(c for c in text if not unicodedata.combining(c))
    return {t for t in re.findall(r"[a-z0-9]{4,}", text)}


def _same_event(a: dict, b: dict) -> bool:
    """Dos nodos son el mismo macro-evento si comparten actores o titulos."""
    act_a = {x.lower() for x in a.get("actores", [])}
    act_b = {x.lower() for x in b.get("actores", [])}
    ta, tb = _fold_tokens(a["titulo"]["es"]), _fold_tokens(b["titulo"]["es"])
    if not ta or not tb:
        return False
    if not compatible_events(a["titulo"]["es"] + " " + a["titulo"]["en"], b["titulo"]["es"] + " " + b["titulo"]["en"]):
        return False
    similarity = len(ta & tb) / len(ta | tb)
    return similarity >= 0.45 or (len(act_a & act_b) >= 2 and similarity >= 0.20)


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


def archive_history(data_dir=None, app_data_dir=None):
    """Expose dated live reports so consumers can recover missed days."""
    import hashlib
    data_dir = data_dir or config.DATA_DIR
    app_data_dir = app_data_dir or config.APP_DATA_DIR
    app_data_dir.mkdir(parents=True, exist_ok=True)
    entries = []
    for path in sorted(data_dir.glob('pulse-20*.json')):
        # Git may normalize CRLF on Windows checkouts. Publish/hash LF bytes
        # consistently so the manifest remains valid after deployment.
        blob = path.read_bytes().replace(b'\r\n', b'\n')
        pulse = json.loads(blob)
        if pulse.get('meta', {}).get('modo') != 'live':
            continue
        date = pulse['meta']['fecha']
        if path.name != 'pulse-' + date.replace('-', '') + '.json':
            raise ValueError('Historical pulse filename/date mismatch')
        (app_data_dir / path.name).write_bytes(blob)
        entry = {'fecha': date, 'archivo': path.name,
                 'sha256': hashlib.sha256(blob).hexdigest()}
        trend = data_dir / ('trends-' + date.replace('-', '') + '.json')
        if trend.exists():
            trend_blob = trend.read_bytes().replace(b'\r\n', b'\n')
            (app_data_dir / trend.name).write_bytes(trend_blob)
            entry.update({'tendencias': trend.name,
                          'tendencias_sha256': hashlib.sha256(trend_blob).hexdigest()})
        entries.append(entry)
    (app_data_dir / 'history.json').write_text(
        json.dumps({'schema': 1, 'reportes': entries}, ensure_ascii=False, indent=2),
        encoding='utf-8')
    return entries


def run(nodes: list[dict], mode: str, engine: str, metrics: dict,
        log=print, report=None, state=None) -> dict:
    log("[7/8] Publicacion")
    today = datetime.now(timezone.utc)
    fecha = state['fecha'] if state else today.strftime("%Y-%m-%d")

    publicables = [n for n in nodes
                   if n["estado"] == "sin_verificar"
                   or (n.get("impacto") or 0) >= config.IMPACT_THRESHOLD]
    if report is not None:
        import hashlib
        publicables = nodes  # already selected: up to five per Nexo dimension
    else:
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
    if report is not None:
        pulse['reporte_markdown'] = report
        pulse['nexo'] = state.get('analisis')
        pulse['cobertura'] = state['cobertura']
        pulse['meta'].update({'schema': '2.0', 'corte': state['corte'],
            'reporte_sha256': hashlib.sha256(report.encode('utf-8')).hexdigest(),
            'estado': 'completo' if state.get('analisis') is not None else 'análisis pendiente',
            'reporte_archivo': f'{fecha} — Pulso.md'})

    config.DATA_DIR.mkdir(parents=True, exist_ok=True)
    daily = config.DATA_DIR / f"pulse-{fecha.replace('-', '')}.json"
    daily.write_text(json.dumps(pulse, ensure_ascii=False, indent=2),
                     encoding="utf-8")
    latest = config.DATA_DIR / "pulse-latest.json"
    shutil.copyfile(daily, latest)

    # Copia para la PWA
    config.APP_DATA_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(daily, config.APP_DATA_DIR / "pulse-latest.json")
    if report is not None:
        (config.APP_DATA_DIR / f'{fecha} — Pulso.md').write_bytes(report.encode('utf-8'))
    if mode == 'live':
        archive_history()

    log(f"  Publicados {len(publicables)} nodos -> {daily.name} (+ latest, + app)")
    return pulse
