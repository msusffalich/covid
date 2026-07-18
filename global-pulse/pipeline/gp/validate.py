"""Etapa 6 — Validacion (Capa 3): almacen de evidencia y regla de oro."""
import json

from . import config


def run(nodes: list[dict], pieces: list[dict], log=print) -> list[dict]:
    log("[6/8] Validacion y anclaje a evidencia (Capa 3)")
    config.EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    by_id = {p["id"]: p for p in pieces}

    for node in nodes:
        valid_refs, imagenes = [], []
        for ref in node.get("fuentes", []):
            piece = by_id.get(ref)
            if not piece:
                continue
            valid_refs.append(ref)
            if piece.get("imagen"):
                imagenes.append(piece["imagen"])
            # persistir la pieza como evidencia (Capa 3)
            ev_path = config.EVIDENCE_DIR / f"{ref}.json"
            ev = {k: piece[k] for k in ("id", "titulo", "cuerpo", "url",
                                        "fecha_pub", "imagen", "fuente",
                                        "fuente_id", "idioma", "recolectado")}
            ev_path.write_text(json.dumps(ev, ensure_ascii=False, indent=2),
                               encoding="utf-8")
        node["fuentes"] = valid_refs
        node["imagenes"] = list(dict.fromkeys(imagenes))[:4]
        # Regla de oro: sin evidencia -> sin_verificar y sin impacto
        if valid_refs and node.get("impacto") is not None:
            node["estado"] = "verificado"
        else:
            node["estado"] = "sin_verificar"
            node["impacto"] = None
        # Referencias legibles para la interfaz
        node["referencias"] = [
            {"id": r, "titulo": by_id[r]["titulo"], "url": by_id[r]["url"],
             "fuente": by_id[r]["fuente"], "fecha": by_id[r]["fecha_pub"],
             "idioma": by_id[r]["idioma"]}
            for r in valid_refs
        ]
    verificados = sum(1 for n in nodes if n["estado"] == "verificado")
    log(f"  Verificados: {verificados}/{len(nodes)}")
    return nodes
