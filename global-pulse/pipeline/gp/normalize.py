"""Etapas 2-3 — Normalizacion y deduplicacion (hash de contenido = id Capa 3)."""
import hashlib
import html
import re
import unicodedata


def _clean(text: str) -> str:
    text = html.unescape(text or "")
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _fold(text: str) -> str:
    """minusculas + sin acentos, para comparaciones."""
    text = unicodedata.normalize("NFKD", text.lower())
    return "".join(c for c in text if not unicodedata.combining(c))


def content_hash(piece: dict) -> str:
    basis = _fold(piece.get("titulo", ""))[:160]
    return "ev_" + hashlib.sha256(basis.encode("utf-8")).hexdigest()[:10]


_DIGEST_RE = re.compile(
    r"(las noticias del|noticias del d[ií]a|resumen del d[ií]a|"
    r"lo que hay que saber|what to know|news of the day|morning briefing|"
    r"evening briefing|the papers|in pictures|en im[aá]genes|news quiz)",
    re.IGNORECASE)


def normalize(pieces: list[dict], log=print) -> list[dict]:
    log("[2/8] Normalizacion")
    out = []
    for p in pieces:
        titulo = _clean(p.get("titulo", ""))
        if len(titulo) < 12:          # descarta restos sin contenido
            continue
        if _DIGEST_RE.search(titulo):  # boletines-resumen: mezclan historias
            continue
        q = {
            "titulo": titulo,
            "cuerpo": _clean(p.get("cuerpo", ""))[:1200],
            "url": (p.get("url") or "").strip(),
            "fecha_pub": (p.get("fecha_pub") or "").strip(),
            "imagen": (p.get("imagen") or "").strip(),
            "fuente": p.get("fuente", "desconocida"),
            "fuente_id": p.get("fuente_id", ""),
            "idioma": p.get("idioma", "es"),
            "recolectado": p.get("recolectado", ""),
        }
        q["id"] = content_hash(q)
        q["texto_norm"] = _fold(q["titulo"] + " " + q["cuerpo"])
        out.append(q)
    log(f"  Piezas validas: {len(out)}")
    return out


def dedup(pieces: list[dict], log=print) -> list[dict]:
    log("[3/8] Deduplicacion por hash de contenido")
    seen, out = {}, []
    for p in pieces:
        if p["id"] in seen:            # conserva la version con mas cuerpo
            prev = seen[p["id"]]
            if len(p["cuerpo"]) > len(prev["cuerpo"]):
                out[out.index(prev)] = p
                seen[p["id"]] = p
            continue
        seen[p["id"]] = p
        out.append(p)
    log(f"  Unicas: {len(out)} (eliminadas {len(pieces) - len(out)})")
    return out
