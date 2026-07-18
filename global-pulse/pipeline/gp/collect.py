"""Etapa 1 — Recoleccion: RSS + GDELT (o fixture en modo offline/demo)."""
import json
import re
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

from . import config

UA = {"User-Agent": "GlobalPulse/1.0 (+pipeline de sintesis; uso personal)"}


def _fetch(url: str, timeout: int = 20) -> bytes:
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def _text(el) -> str:
    return re.sub(r"<[^>]+>", " ", (el.text or "")).strip() if el is not None else ""


def _first_image(item) -> str:
    """Extrae la imagen destacada de un item RSS (media:content/thumbnail o enclosure)."""
    ns = {"media": "http://search.yahoo.com/mrss/"}
    for tag in ("media:content", "media:thumbnail"):
        el = item.find(tag, ns)
        if el is not None and el.get("url"):
            return el.get("url")
    enc = item.find("enclosure")
    if enc is not None and (enc.get("type") or "").startswith("image"):
        return enc.get("url") or ""
    return ""


def parse_rss(raw: bytes, source: dict) -> list[dict]:
    """Convierte un feed RSS/RDF/Atom en piezas crudas normalizables."""
    root = ET.fromstring(raw)
    items = root.findall(".//item")
    if not items:  # Atom
        items = root.findall(".//{http://www.w3.org/2005/Atom}entry")
    out = []
    for it in items:
        title = _text(it.find("title")) or _text(
            it.find("{http://www.w3.org/2005/Atom}title"))
        desc = _text(it.find("description")) or _text(
            it.find("{http://www.w3.org/2005/Atom}summary"))
        link_el = it.find("link")
        link = (link_el.text or "").strip() if link_el is not None else ""
        if not link and it.find("{http://www.w3.org/2005/Atom}link") is not None:
            link = it.find("{http://www.w3.org/2005/Atom}link").get("href", "")
        pub = _text(it.find("pubDate")) or _text(it.find(
            "{http://purl.org/dc/elements/1.1/}date"))
        if not title:
            continue
        out.append({
            "titulo": title,
            "cuerpo": desc,
            "url": link,
            "fecha_pub": pub,
            "imagen": _first_image(it),
            "fuente": source["name"],
            "fuente_id": source["id"],
            "idioma": source["lang"],
        })
    return out


def collect_rss(log) -> list[dict]:
    pieces = []
    for src in config.RSS_SOURCES:
        try:
            raw = _fetch(src["url"])
            got = parse_rss(raw, src)
            pieces.extend(got)
            log(f"  RSS {src['id']}: {len(got)} piezas")
        except Exception as e:  # fallo aislado: la fuente caida no rompe el ciclo
            log(f"  RSS {src['id']}: ERROR {e} (fallo aislado, se continua)")
    return pieces


def collect_gdelt(log) -> list[dict]:
    pieces = []
    for q in config.GDELT_QUERIES:
        try:
            url = config.GDELT_URL.format(query=urllib.request.quote(q))
            data = json.loads(_fetch(url))
            for art in data.get("articles", []):
                pieces.append({
                    "titulo": art.get("title", ""),
                    "cuerpo": "",
                    "url": art.get("url", ""),
                    "fecha_pub": art.get("seendate", ""),
                    "imagen": art.get("socialimage", ""),
                    "fuente": art.get("domain", "GDELT"),
                    "fuente_id": "gdelt",
                    "idioma": "es" if art.get("language", "").lower() == "spanish" else "en",
                })
            log(f"  GDELT '{q[:30]}...': {len(data.get('articles', []))} piezas")
        except Exception as e:
            log(f"  GDELT: ERROR {e} (fallo aislado, se continua)")
    return pieces


def collect_fixture(log) -> list[dict]:
    """Modo demo/offline: lee piezas de fixtures/raw_sample.json."""
    path = Path(__file__).resolve().parents[1] / "fixtures" / "raw_sample.json"
    pieces = json.loads(path.read_text(encoding="utf-8"))
    log(f"  Fixture: {len(pieces)} piezas (modo demo, sin red)")
    return pieces


def run(mode: str, log=print) -> list[dict]:
    """mode: 'live' (RSS+GDELT) | 'fixture' (demo offline)."""
    log(f"[1/8] Recoleccion (modo {mode})")
    if mode == "fixture":
        pieces = collect_fixture(log)
    else:
        pieces = collect_rss(log) + collect_gdelt(log)
    stamp = datetime.now(timezone.utc).isoformat()
    for p in pieces:
        p.setdefault("recolectado", stamp)
    log(f"  Total recolectado: {len(pieces)} piezas")
    return pieces
