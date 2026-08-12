"""Seguidor automatico de tendencias por tema.

Cada ciclo, para una lista fija de temas, reune los nodos recientes de la
historia de pulsos (data/pulse-*.json), construye una serie temporal y una
sintesis de tendencia (LLM con respaldo heuristico), y publica:

  - data/trends-latest.json          -> lo consume la pestana "Tendencias" del app
  - app/public/data/trends-latest.json (copia)
  - 40 · Analisis/Auto/<Tema>.md     -> reporte auto en la boveda (junto a los
                                         cuadros de autor, sin pisarlos)

La ventana por defecto es de 21 dias.
"""
import json
import os
import re
import unicodedata
import urllib.request
from datetime import datetime, timezone

from . import config

WINDOW_DAYS = 21
MAX_NODES_PER_THEME = 12

# Temas seguidos de forma permanente (el usuario eligio estos 6)
THEMES = [
    {"id": "iran-eeuu", "color": "#E4634F",
     "nombre": {"es": "Iran vs. EE.UU.", "en": "Iran vs. USA"},
     "kw": ["iran", "teheran", "ormuz", "hormuz", "irgc", "hutie", "houthi"]},
    {"id": "rusia-ucrania", "color": "#7C6FE4",
     "nombre": {"es": "Rusia vs. Ucrania", "en": "Russia vs. Ukraine"},
     "kw": ["ucrania", "ukrain", "rusia", "russia", "kyiv", "kiev", "zelensk",
            "putin", "moscu", "moscow", "kremlin"]},
    {"id": "gaza-om", "color": "#C75FA8",
     "nombre": {"es": "Gaza y Oriente Medio", "en": "Gaza & Middle East"},
     "kw": ["gaza", "hamas", "israel", "netanyahu", "cisjordania", "libano",
            "rafah", "mar rojo", "red sea", "hezbol"]},
    {"id": "ia", "color": "#3D9BE4",
     "nombre": {"es": "Gobernanza y riesgo de la IA", "en": "AI governance & risk"},
     "kw": ["inteligencia artificial", "artificial intelligence", "openai",
            "hugging face", "chatbot", "modelo de lenguaje", "semiconductor",
            "robot humanoide", "humanoid robot", "algoritmo", "chip de ia",
            "ai chip"]},
    {"id": "clima", "color": "#3FA65C",
     "nombre": {"es": "Impacto climatico", "en": "Climate impact"},
     "kw": ["cambio climatico", "climate change", "calentamiento", "sequia",
            "drought", "inundacion", "flood", "huracan", "hurricane",
            "ola de calor", "heatwave", "incendio forestal", "wildfire",
            "deshielo", "nivel del mar", "sea level", "emision", "cop3",
            "acuerdo de paris"]},
    {"id": "economia", "color": "#E4A11B",
     "nombre": {"es": "Economia global", "en": "Global economy"},
     "kw": ["inflacion", "inflation", "banco central", "central bank",
            "arancel", "tariff", "recesion", "recession", "petroleo", "oil",
            "bolsa", "acciones", "shares", "mercado bursatil", "pib", "gdp",
            "fmi", "imf", "divisa", "currency"]},
]


def _fold(text: str) -> str:
    text = unicodedata.normalize("NFKD", (text or "").lower())
    return "".join(c for c in text if not unicodedata.combining(c))


def _matches(node: dict, kws: list[str]) -> bool:
    blob = _fold(" ".join([
        node["titulo"]["es"], node["titulo"]["en"],
        node["sintesis"]["es"], node["sintesis"]["en"],
        " ".join(node.get("actores", [])),
    ]))
    return any(k in blob for k in kws)


def _load_history(log) -> list[dict]:
    """Carga los pulsos diarios de los ultimos WINDOW_DAYS."""
    files = sorted(config.DATA_DIR.glob("pulse-20*.json"))
    files = files[-WINDOW_DAYS:]
    pulses = []
    for f in files:
        try:
            pulses.append(json.loads(f.read_text(encoding="utf-8")))
        except Exception as e:  # noqa: BLE001
            log(f"  trends: no se pudo leer {f.name}: {e}")
    return pulses


# ---------------------------------------------------------------------------
# Sintesis de tendencia
# ---------------------------------------------------------------------------
TREND_PROMPT = """Eres un analista de tendencias. Recibes los titulares y sintesis
de un mismo tema a lo largo de varios dias (con fecha e impacto).
Redacta, en ESPANOL NEUTRO y en INGLES, de forma neutral y sin inventar nada:
- "resumen": 2-3 frases sobre la EVOLUCION del tema en el periodo (que cambia,
  hacia donde va), no un listado.
- "estado": una sola frase con el estado mas reciente.
Responde UNICAMENTE JSON: {"resumen":{"es":"...","en":"..."},"estado":{"es":"...","en":"..."}}"""


def _synth_api(theme: dict, nodes: list[dict], api_key: str) -> dict:
    items = [{"fecha": n["fecha"], "impacto": n.get("impacto"),
              "titulo": n["titulo"]["es"], "sintesis": n["sintesis"]["es"]}
             for n in nodes[:14]]
    payload = {
        "model": config.ANTHROPIC_MODEL, "max_tokens": 500,
        "system": TREND_PROMPT,
        "messages": [{"role": "user", "content": json.dumps(
            {"tema": theme["nombre"]["es"], "nodos": items}, ensure_ascii=False)}],
    }
    req = urllib.request.Request(
        config.ANTHROPIC_URL, data=json.dumps(payload).encode(),
        headers={"content-type": "application/json", "x-api-key": api_key,
                 "anthropic-version": "2023-06-01"})
    with urllib.request.urlopen(req, timeout=60) as r:
        resp = json.loads(r.read())
    text = resp["content"][0]["text"]
    m = re.search(r"\{.*\}", text, re.S)
    return json.loads(m.group(0))


def _synth_heuristic(theme: dict, nodes: list[dict], total: int = None) -> dict:
    latest = nodes[0] if nodes else None
    n = total if total is not None else len(nodes)
    if not latest:
        return {"resumen": {"es": "Sin nodos en el periodo.",
                            "en": "No nodes in the period."},
                "estado": {"es": "-", "en": "-"}}
    res_es = (f"{n} nodos registrados en el periodo. Lo mas reciente: "
              f"{latest['titulo']['es']}.")
    res_en = (f"{n} nodes recorded in the period. Most recent: "
              f"{latest['titulo']['en']}.")
    return {"resumen": {"es": res_es, "en": res_en},
            "estado": {"es": latest["titulo"]["es"],
                       "en": latest["titulo"]["en"]}}


# ---------------------------------------------------------------------------
def _series(nodes_by_day: dict) -> list[dict]:
    return [{"fecha": d, "max": max((x.get("impacto") or 0 for x in ns), default=0),
             "n": len(ns)}
            for d, ns in sorted(nodes_by_day.items())]


def run(mode: str, log=print) -> dict:
    log("[9/9] Seguidor de tendencias por tema")
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    engine = "api" if api_key else "heuristic"
    pulses = _load_history(log)

    temas_out = []
    for theme in THEMES:
        by_day: dict = {}
        matched: list[dict] = []
        for p in pulses:
            fecha = p["meta"]["fecha"]
            hits = [n for n in p["nodos"] if _matches(n, theme["kw"])]
            if hits:
                by_day.setdefault(fecha, []).extend(hits)
                matched.extend(hits)
        # mas recientes primero, dedup por titulo
        matched.sort(key=lambda n: (n["fecha"], n.get("impacto") or 0),
                     reverse=True)
        seen, recientes = set(), []
        for n in matched:
            key = _fold(n["titulo"]["es"])[:60]
            if key in seen:
                continue
            seen.add(key)
            recientes.append(n)
            if len(recientes) >= MAX_NODES_PER_THEME:
                break

        if matched:
            try:
                resumen = (_synth_api(theme, recientes, api_key) if engine == "api"
                           else _synth_heuristic(theme, recientes, len(matched)))
            except Exception as e:  # noqa: BLE001
                log(f"  trends: LLM fallo en {theme['id']}: {e} -> heuristico")
                resumen = _synth_heuristic(theme, recientes, len(matched))
        else:
            resumen = _synth_heuristic(theme, recientes, 0)

        temas_out.append({
            "id": theme["id"], "nombre": theme["nombre"], "color": theme["color"],
            "n_nodos": len(matched),
            "ultima_fecha": recientes[0]["fecha"] if recientes else None,
            "resumen": resumen["resumen"], "estado": resumen["estado"],
            "serie": _series(by_day),
            "nodos": [{
                "fecha": n["fecha"], "titulo": n["titulo"],
                "impacto": n.get("impacto"), "categoria": n["categoria"],
                "kardashev": n.get("kardashev", ""),
                "url": (n.get("referencias") or [{}])[0].get("url", ""),
                "fuente": (n.get("referencias") or [{}])[0].get("fuente", ""),
            } for n in recientes],
        })
        log(f"  {theme['id']}: {len(matched)} nodos, {len(recientes)} recientes")

    out = {
        "meta": {"generado": datetime.now(timezone.utc).isoformat(),
                 "ventana_dias": WINDOW_DAYS, "motor": engine, "modo": mode},
        "temas": temas_out,
    }
    # Publicacion
    daily = config.DATA_DIR / "trends-latest.json"
    daily.write_text(json.dumps(out, ensure_ascii=False, indent=2),
                     encoding="utf-8")
    config.APP_DATA_DIR.mkdir(parents=True, exist_ok=True)
    (config.APP_DATA_DIR / "trends-latest.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    _write_vault(out, log)
    log(f"  Tendencias publicadas: {len(temas_out)} temas (motor {engine})")
    return out


def _write_vault(out: dict, log) -> None:
    auto_dir = config.VAULT_DIR / "40 · Analisis" / "Auto"
    auto_dir.mkdir(parents=True, exist_ok=True)
    fecha = out["meta"]["generado"][:10]
    for t in out["temas"]:
        filas = "\n".join(
            f"| {n['fecha']} | {n.get('impacto') or '—'} | {n['kardashev']} | "
            f"{n['titulo']['es'][:64]} |" for n in t["nodos"])
        body = f"""---
titulo: "Tendencia automatica — {t['nombre']['es']}"
tipo: tendencia-auto
tema: {t['id']}
actualizado: {fecha}
nodos: {t['n_nodos']}
origen: global-pulse
---
# Tendencia automatica — {t['nombre']['es']}

> [!info] Reporte **generado automaticamente** cada dia por Global Pulse
> (motor: {out['meta']['motor']}). Ventana: {out['meta']['ventana_dias']} dias ·
> Actualizado: {fecha}. Para el analisis de autor ver la carpeta superior.

## Resumen de tendencia
{t['resumen']['es']}

## Trend summary (EN)
{t['resumen']['en']}

> [!note] Estado actual
> {t['estado']['es']}

## Nodos recientes ({t['n_nodos']} en la ventana)
| Fecha | Impacto | K | Nodo |
|---|---|---|---|
{filas}

[[Global Brain — Inicio|← Inicio]]
"""
        safe = re.sub(r"[^A-Za-z0-9 -]", "", _fold(t["nombre"]["es"])).strip()
        (auto_dir / f"{safe}.md").write_text(body, encoding="utf-8")
    log(f"  Reportes auto en la boveda: {len(out['temas'])}")
