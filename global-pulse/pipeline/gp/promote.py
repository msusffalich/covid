"""Etapa 8 — Promocion: insights verificados de alto impacto -> notas Obsidian (PARA)."""
from . import config


def _note(node: dict) -> str:
    actores = ", ".join(node.get("actores", []))
    fuentes = ", ".join(node.get("fuentes", []))
    enlaces = " · ".join(f"[[{a}]]" for a in node.get("actores", [])[:4])
    refs = "\n".join(f"- [{r['fuente']}]({r['url']}) — {r['titulo']}"
                     for r in node.get("referencias", []))
    return f"""---
titulo: "{node['titulo']['es']}"
title_en: "{node['titulo']['en']}"
fecha: {node['fecha']}
categoria: {node['categoria']}
impacto: {node['impacto']}
actores: [{actores}]
fuentes: [{fuentes}]
estado: {node['estado']}
para: Recursos
origen: global-pulse
---
## Sintesis
{node['sintesis']['es']}

## Synthesis (EN)
{node['sintesis']['en']}

## Enlaces
{enlaces}

## Referencias
{refs}
"""


def run(nodes: list[dict], log=print) -> int:
    log("[8/8] Promocion al segundo cerebro (Obsidian/PARA)")
    config.VAULT_DIR.mkdir(parents=True, exist_ok=True)
    count = 0
    for node in nodes:
        if node["estado"] != "verificado":
            continue
        if (node.get("impacto") or 0) < config.PROMOTE_THRESHOLD:
            continue
        safe = "".join(c if c.isalnum() or c in " -_" else "" for c in
                       node["titulo"]["es"])[:70].strip().replace(" ", "-")
        path = config.VAULT_DIR / f"{node['fecha']}-{safe or node['id']}.md"
        path.write_text(_note(node), encoding="utf-8")
        count += 1
    log(f"  Notas promovidas: {count} -> {config.VAULT_DIR}")
    return count
