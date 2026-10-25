"""Etapa 1 — Recoleccion: RSS + GDELT (o fixture en modo offline/demo)."""
import json
import re
import urllib.request
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor
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
    if root.tag == '{http://www.sitemaps.org/schemas/sitemap/0.9}urlset':
        ns = {'s': 'http://www.sitemaps.org/schemas/sitemap/0.9', 'n': 'http://www.google.com/schemas/sitemap-news/0.9'}
        return [dict(titulo=_text(it.find('n:news/n:title', ns)), cuerpo='',
                     url=_text(it.find('s:loc', ns)), fecha_pub=_text(it.find('n:news/n:publication_date', ns)),
                     imagen='', fuente=source['name'], fuente_id=source['id'], idioma=source['lang'])
                for it in root.findall('s:url', ns) if it.find('n:news/n:publication_date', ns) is not None]
    items = root.findall(".//item") or root.findall('.//{http://purl.org/rss/1.0/}item')
    if not items:  # Atom
        items = root.findall(".//{http://www.w3.org/2005/Atom}entry")
    out = []
    for it in items:
        title = _text(it.find("title")) or _text(
            it.find("{http://www.w3.org/2005/Atom}title")) or _text(it.find('{http://purl.org/rss/1.0/}title'))
        desc = _text(it.find("description")) or _text(
            it.find("{http://www.w3.org/2005/Atom}summary")) or _text(it.find('{http://purl.org/rss/1.0/}description'))
        link_el = it.find("link")
        link = (link_el.text or "").strip() if link_el is not None else ""
        if not link and it.find("{http://www.w3.org/2005/Atom}link") is not None:
            link = it.find("{http://www.w3.org/2005/Atom}link").get("href", "")
        if not link:
            link = _text(it.find('{http://purl.org/rss/1.0/}link'))
        pub = (_text(it.find("pubDate")) or _text(it.find(
            "{http://purl.org/dc/elements/1.1/}date")) or _text(it.find(
            "{http://www.w3.org/2005/Atom}published")))
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


def collect_rss(log, sources=None, coverage=None) -> list[dict]:
    pieces = []
    def fetch_source(src):
        try:
            raw = _fetch(src["url"])
            got = parse_rss(raw, src)
            return src, got, None
        except Exception as e:  # fallo aislado: la fuente caida no rompe el ciclo
            return src, [], str(e)[:200]
    with ThreadPoolExecutor(max_workers=8) as pool:
        results = pool.map(fetch_source, config.RSS_SOURCES if sources is None else sources)
        for src, got, error in results:
            pieces.extend(got)
            if coverage is not None:
                coverage[src['id']] = {'ok': error is None and bool(got), 'piezas': len(got),
                    'fuente': src['name'], 'tipo': src.get('tipo', 'medio'),
                    'error': error or ('' if got else 'El canal no devolvió documentos')}
            log(f"  Canal {src['id']}: {len(got)} piezas" + (f' · ERROR {error}' if error else ''))
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
