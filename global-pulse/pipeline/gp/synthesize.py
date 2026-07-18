"""Etapa 5 — Sintesis (Capa 2). Motor hibrido:

  - modo 'api'       : LLM (Anthropic) con el prompt maestro y salida JSON validada.
  - modo 'heuristic' : sintetizador extractivo por reglas (sin dependencias).
  - modo 'auto'      : usa 'api' si hay ANTHROPIC_API_KEY; si no, 'heuristic'.
"""
import json
import os
import re
import urllib.request

from . import config
from .config import CATEGORY_KEYWORDS, GAZETTEER

MASTER_PROMPT = """Eres un analista de inteligencia neutral (Sintetizador de nodos de impacto v3).
Recibes un cluster de piezas informativas (titulo, cuerpo, fuente, idioma, fecha).
Tarea:
1. Resume el evento en 2-4 frases, sin opinion, en ESPANOL NEUTRO y en INGLES.
2. Asigna categoria ({cats}), actores principales y geolocalizacion (lat/lon + region).
3. Puntua impacto 0-100 (alcance x novedad x relevancia estrategica).
4. Cita las fuentes por su id.
Responde UNICAMENTE JSON valido:
{{"titulo":{{"es":"...","en":"..."}},"sintesis":{{"es":"...","en":"..."}},
"categoria":"...","actores":["..."],"geo":{{"lat":0.0,"lon":0.0,"region":"..."}},
"impacto":0,"fuentes":["ev_..."]}}
Si la evidencia es insuficiente usa "impacto": null."""


# ---------------------------------------------------------------------------
# Heuristico
# ---------------------------------------------------------------------------
def _pick_summary(piezas: list[dict], lang: str) -> tuple[str, str]:
    """(titulo, sintesis) extractivos para un idioma; cae al otro si no hay."""
    own = [p for p in piezas if p["idioma"] == lang] or piezas
    own = sorted(own, key=lambda p: len(p["cuerpo"]), reverse=True)
    lead = own[0]
    sentences = re.split(r"(?<=[.!?])\s+", lead["cuerpo"])[:3]
    body = " ".join(s for s in sentences if len(s) > 15)
    return lead["titulo"], (body or lead["titulo"])


def _categoria(text: str) -> str:
    scores = {}
    for cat, kws in CATEGORY_KEYWORDS.items():
        scores[cat] = sum(1 for kw in kws if kw in text)
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "sociedad"


def _geo(text: str):
    for name, (lat, lon, region) in GAZETTEER.items():
        if name in text:
            return {"lat": lat, "lon": lon, "region": region}, name.title()
    return {"lat": 0.0, "lon": 0.0, "region": "Global"}, None


def _actores(piezas: list[dict]) -> list[str]:
    from collections import Counter
    c = Counter()
    for p in piezas:
        for w in re.findall(r"\b[A-Z][a-zA-Z]{2,}(?:\s+[A-Z][a-zA-Z]{2,})?\b",
                            p["titulo"]):
            if w.lower() not in config.STOPWORDS:
                c[w] += 1
    return [w for w, _ in c.most_common(4)]


def _impacto(cluster: dict) -> int:
    """Alcance (fuentes distintas) + cobertura (piezas) + senal translingue.

    Calibrado para discriminar en corpus reales (~900 piezas/dia): un evento
    tipico puntua 30-60; solo la cobertura excepcional se acerca a 95.
    """
    piezas = cluster["piezas"]
    fuentes = len({p["fuente_id"] for p in piezas})
    idiomas = len({p["idioma"] for p in piezas})
    alcance = min(fuentes * 9, 45)
    cobertura = min(len(piezas) * 4, 24)
    translingue = 16 if idiomas > 1 else 4
    entidades = min(len(cluster.get("entidades", [])), 10)  # riqueza del evento
    return min(alcance + cobertura + translingue + entidades, 95)


def synth_heuristic(cluster: dict) -> dict:
    piezas = cluster["piezas"]
    t_es, s_es = _pick_summary(piezas, "es")
    t_en, s_en = _pick_summary(piezas, "en")
    text = " ".join(p["texto_norm"] for p in piezas)
    geo, _ = _geo(text)
    return {
        "titulo": {"es": t_es, "en": t_en},
        "sintesis": {"es": s_es, "en": s_en},
        "categoria": _categoria(text),
        "actores": _actores(piezas),
        "geo": geo,
        "impacto": _impacto(cluster),
        "fuentes": [p["id"] for p in piezas],
    }


# ---------------------------------------------------------------------------
# API (Anthropic)
# ---------------------------------------------------------------------------
def synth_api(cluster: dict, api_key: str) -> dict:
    payload = {
        "model": config.ANTHROPIC_MODEL,
        "max_tokens": 900,
        "temperature": 0.2,
        "system": MASTER_PROMPT.format(cats=", ".join(config.CATEGORIES)),
        "messages": [{"role": "user", "content": json.dumps(
            [{k: p[k] for k in ("id", "titulo", "cuerpo", "fuente", "idioma",
                                "fecha_pub")} for p in cluster["piezas"]],
            ensure_ascii=False)}],
    }
    req = urllib.request.Request(
        config.ANTHROPIC_URL, data=json.dumps(payload).encode(),
        headers={"content-type": "application/json", "x-api-key": api_key,
                 "anthropic-version": "2023-06-01"})
    with urllib.request.urlopen(req, timeout=90) as r:
        resp = json.loads(r.read())
    text = resp["content"][0]["text"]
    m = re.search(r"\{.*\}", text, re.S)
    return json.loads(m.group(0))


REQUIRED = {"titulo", "sintesis", "categoria", "actores", "geo", "impacto", "fuentes"}


def validate_node_shape(node: dict) -> bool:
    if not REQUIRED.issubset(node):
        return False
    if node["categoria"] not in config.CATEGORIES:
        return False
    g = node["geo"]
    return all(k in g for k in ("lat", "lon", "region"))


def run(clusters: list[dict], mode: str = "auto", log=print) -> list[dict]:
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if mode == "auto":
        mode = "api" if api_key else "heuristic"
    log(f"[5/8] Sintesis (motor {mode})")
    nodes = []
    for cl in clusters:
        if len(cl["piezas"]) < config.MIN_CLUSTER_SIZE:
            continue
        node = None
        if mode == "api":
            try:
                node = synth_api(cl, api_key)
                if not validate_node_shape(node):   # reintento unico
                    node = synth_api(cl, api_key)
            except Exception as e:
                log(f"  API fallo en {cl['cluster_id']}: {e} -> heuristico")
                node = None
        if node is None or not validate_node_shape(node):
            node = synth_heuristic(cl)
        node["cluster_id"] = cl["cluster_id"]
        nodes.append(node)
    log(f"  Nodos sintetizados: {len(nodes)}")
    return nodes
