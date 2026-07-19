"""Global Brain — boveda Obsidian alimentada a diario por Global Pulse.

Principio de Kardashev aplicado al conocimiento: cada nodo de impacto se
clasifica por la ESCALA CIVILIZATORIA de su alcance, inspirada en la escala
de Nikolai Kardashov:

  K0 · Local y Nacional   — eventos cuyo impacto se contiene en un pais/region.
  K1 · Planetario         — eventos que afectan a la civilizacion global
                            (clima, pandemias, gobernanza tecnologica, economia
                            mundial, acuerdos internacionales).
  K2 · Estelar y Energia  — dominio del espacio y de la energia a gran escala
                            (misiones espaciales, satelites, fusion, solar).
  K3 · Frontera Cosmica   — descubrimientos sobre el cosmos profundo.

Estructura de la boveda (compatible con PARA de Tiago Forte):

  Global Brain/
  ├── Global Brain — Inicio.md          nota raiz (vision y mapa)
  ├── 00 · Pulso Diario/                una nota-digest por ciclo
  ├── 10 · Nodos/<Categoria>/           notas atomicas (Recursos de PARA)
  ├── 20 · Indices/Escala Kardashev/    MOCs por nivel K (con Dataview)
  ├── 20 · Indices/Categorias/          MOCs por categoria
  └── 30 · PARA/                        Proyectos / Areas / Archivo del usuario
"""
import json
import re
import sys
import unicodedata
from pathlib import Path

from . import config

K_LEVELS = {
    "K0": "K0 · Local y Nacional",
    "K1": "K1 · Planetario",
    "K2": "K2 · Estelar y Energia",
    "K3": "K3 · Frontera Cosmica",
}

_K3_KEYS = ["agujero negro", "black hole", "galaxia", "galaxy", "interestelar",
            "interstellar", "exoplaneta", "exoplanet", "big bang", "cosmolog",
            "materia oscura", "dark matter", "telescopio james webb"]
_K2_KEYS = ["espacio", "space", "nasa", "esa ", "spacex", "cohete", "rocket",
            "satelite", "satellite", "lunar", "marte", "mars", "orbital",
            "astronauta", "astronaut", "fusion nuclear", "nuclear fusion",
            "reactor", "energia solar", "solar power", "renovable", "renewable",
            "hidrogeno", "hydrogen"]
_K1_KEYS = ["mundial", "global", "planeta", "planet", "onu", "un ", "oms",
            "who ", "internacional", "international", "humanidad", "humanity",
            "clima", "climate", "pandemia", "pandemic", "inteligencia artificial",
            "artificial intelligence", "acuerdo de paris", "g20", "g7", "fmi",
            "imf", "tratado", "treaty", "cumbre", "summit"]


def classify_kardashev(node: dict) -> str:
    """Devuelve el codigo K del nodo segun su alcance civilizatorio."""
    text = (node["titulo"]["es"] + " " + node["titulo"]["en"] + " "
            + node["sintesis"]["es"] + " " + node["sintesis"]["en"]).lower()
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))

    if any(k in text for k in _K3_KEYS):
        return "K3"
    if any(k in text for k in _K2_KEYS):
        return "K2"
    if node["categoria"] == "clima" or any(k in text for k in _K1_KEYS):
        return "K1"
    # Cobertura translingue masiva de alto impacto -> trasciende lo local
    if (node.get("impacto") or 0) >= 85 and len(node.get("fuentes", [])) >= 8:
        return "K1"
    return "K0"


# ---------------------------------------------------------------------------
# Renderizado de notas
# ---------------------------------------------------------------------------
def _slug(text: str, max_len: int = 64) -> str:
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = re.sub(r"[^A-Za-z0-9 -]", "", text).strip()
    return re.sub(r"\s+", "-", text)[:max_len] or "nodo"


def _cat_title(cat: str) -> str:
    names = {"geopolitica": "Geopolitica", "economia": "Economia",
             "ciencia": "Ciencia", "clima": "Impacto Climatico",
             "tecnologia": "Tecnologia", "innovacion": "Innovacion",
             "salud": "Salud y Bienestar", "sociedad": "Sociedad"}
    return names.get(cat, cat.title())


def node_note(node: dict) -> str:
    k = node["kardashev"]
    actores = ", ".join(node.get("actores", []))
    enlaces = " · ".join(f"[[{a}]]" for a in node.get("actores", [])[:4])
    refs = "\n".join(f"- [{r['fuente']}]({r['url']}) — {r['titulo']}"
                     for r in node.get("referencias", []))
    return f"""---
titulo: "{node['titulo']['es']}"
title_en: "{node['titulo']['en']}"
fecha: {node['fecha']}
categoria: {node['categoria']}
impacto: {node['impacto']}
kardashev: {k}
actores: [{actores}]
fuentes: [{', '.join(node.get('fuentes', []))}]
estado: {node['estado']}
para: Recursos
origen: global-pulse
---
# {node['titulo']['es']}

> [!info] Escala Kardashev: [[{K_LEVELS[k]}]] · Categoria: [[{_cat_title(node['categoria'])}]] · Impacto {node['impacto']}

## Sintesis
{node['sintesis']['es']}

## Synthesis (EN)
{node['sintesis']['en']}

## Enlaces
{enlaces}

## Referencias (Capa 3)
{refs}
"""


def daily_note(pulse: dict, promoted: list[dict]) -> str:
    m = pulse["meta"]
    fecha = m["fecha"]
    filas = []
    for n in sorted(pulse["nodos"], key=lambda x: x.get("impacto") or 0,
                    reverse=True):
        marca = " ↳ promovido" if n in promoted else ""
        link = (f"[[{fecha}-{_slug(n['titulo']['es'])}|{n['titulo']['es'][:70]}]]"
                if n in promoted else n["titulo"]["es"][:70])
        filas.append(f"| {n.get('impacto') or '—'} | {n['kardashev']} | "
                     f"{_cat_title(n['categoria'])} | {link}{marca} |")
    tabla = "\n".join(filas)
    return f"""---
fecha: {fecha}
tipo: pulso-diario
modo: {m['modo']}
motor: {m['motor_sintesis']}
nodos: {len(pulse['nodos'])}
promovidos: {len(promoted)}
origen: global-pulse
---
# Pulso del {fecha}

> {len(pulse['nodos'])} nodos publicados · {len(promoted)} promovidos al Global Brain
> Motor: {m['motor_sintesis']} · Modo: {m['modo']}

| Impacto | K | Categoria | Nodo |
|---|---|---|---|
{tabla}

[[Global Brain — Inicio|← Inicio]]
"""


HOME = """---
tipo: inicio
origen: global-pulse
---
# Global Brain

Cerebro de conocimiento alimentado automaticamente cada dia por **Global
Pulse**: los nodos de impacto verificados de alto valor se archivan aqui como
notas atomicas, clasificados por el **principio de Kardashev** y organizados
segun **PARA** (Tiago Forte).

## El principio de Kardashev
Inspirado en la escala del astrofisico Nikolai Kardashov, cada nodo se
clasifica por la **escala civilizatoria de su impacto**:

- [[K0 · Local y Nacional]] — el impacto se contiene en un pais o region.
- [[K1 · Planetario]] — afecta a la civilizacion global: clima, pandemias,
  gobernanza tecnologica, economia mundial, grandes acuerdos.
- [[K2 · Estelar y Energia]] — dominio del espacio y de la energia a gran
  escala: misiones, satelites, fusion, transicion energetica.
- [[K3 · Frontera Cosmica]] — descubrimientos sobre el cosmos profundo.

## Estructura
- **00 · Pulso Diario** — una nota por ciclo con todos los nodos del dia.
- **10 · Nodos** — notas atomicas por categoria (los *Recursos* de PARA).
- **20 · Indices** — mapas de contenido por escala Kardashev y por categoria.
- **30 · PARA** — tus *Proyectos*, *Areas* y *Archivo*: enlaza aqui los nodos
  que se conviertan en accion.

## Como se alimenta
El pipeline de Global Pulse corre cada dia (05:00 UTC), sintetiza las noticias
de 30+ fuentes verificables y escribe aqui las notas nuevas. Tu papel es la
curacion: el sistema propone, tu decides que asciende de *Recurso* a
*Proyecto* o *Area*.
"""

K_MOC = """---
tipo: indice
kardashev: {code}
origen: global-pulse
---
# {name}

{desc}

## Nodos en este nivel
```dataview
TABLE fecha AS Fecha, impacto AS Impacto, categoria AS Categoria
FROM "10 · Nodos"
WHERE kardashev = "{code}"
SORT fecha DESC, impacto DESC
```
> Requiere el plugin **Dataview**. Sin el, usa la busqueda: `kardashev: {code}`.

[[Global Brain — Inicio|← Inicio]]
"""

K_DESCS = {
    "K0": "Eventos cuyo impacto se contiene en un pais o region.",
    "K1": "Eventos que afectan a la civilizacion global en su conjunto.",
    "K2": "Dominio del espacio y de la energia a gran escala.",
    "K3": "Descubrimientos sobre el cosmos profundo.",
}

CAT_MOC = """---
tipo: indice
categoria: {cat}
origen: global-pulse
---
# {title}

## Nodos de esta categoria
```dataview
TABLE fecha AS Fecha, impacto AS Impacto, kardashev AS K
FROM "10 · Nodos"
WHERE categoria = "{cat}"
SORT fecha DESC, impacto DESC
```
> Requiere el plugin **Dataview**. Sin el, usa la busqueda: `categoria: {cat}`.

[[Global Brain — Inicio|← Inicio]]
"""

PARA_README = """# 30 · PARA

Espacio del usuario segun el metodo PARA de Tiago Forte:

- **Proyectos/** — esfuerzos con objetivo y fecha. Enlaza aqui los nodos que
  disparen una accion concreta.
- **Areas/** — responsabilidades continuas que quieres vigilar.
- **Archivo/** — lo que dejo de estar activo.

Los *Recursos* de PARA son las notas de `10 · Nodos`: Global Pulse los
mantiene por ti; tu solo curas y enlazas.
"""


# ---------------------------------------------------------------------------
# Construccion
# ---------------------------------------------------------------------------
def build(pulse: dict, log=print) -> int:
    """Escribe/actualiza la boveda Global Brain. Devuelve nodos promovidos."""
    root = config.VAULT_DIR
    nodes_dir = root / "10 · Nodos"
    daily_dir = root / "00 · Pulso Diario"
    idx_k = root / "20 · Indices" / "Escala Kardashev"
    idx_c = root / "20 · Indices" / "Categorias"
    para = root / "30 · PARA"

    for d in (daily_dir, idx_k, idx_c, para / "Proyectos", para / "Areas",
              para / "Archivo"):
        d.mkdir(parents=True, exist_ok=True)

    # Clasificacion Kardashev de todos los nodos del pulso
    for n in pulse["nodos"]:
        n["kardashev"] = classify_kardashev(n)

    # Estructura estatica (idempotente)
    (root / "Global Brain — Inicio.md").write_text(HOME, encoding="utf-8")
    for code, name in K_LEVELS.items():
        (idx_k / f"{name}.md").write_text(
            K_MOC.format(code=code, name=name, desc=K_DESCS[code]),
            encoding="utf-8")
    for cat in config.CATEGORIES:
        (idx_c / f"{_cat_title(cat)}.md").write_text(
            CAT_MOC.format(cat=cat, title=_cat_title(cat)), encoding="utf-8")
    (para / "README.md").write_text(PARA_README, encoding="utf-8")

    # Notas atomicas de los nodos que superan el umbral
    promoted = []
    for n in pulse["nodos"]:
        if n["estado"] != "verificado":
            continue
        if (n.get("impacto") or 0) < config.PROMOTE_THRESHOLD:
            continue
        cat_dir = nodes_dir / _cat_title(n["categoria"])
        cat_dir.mkdir(parents=True, exist_ok=True)
        fname = f"{n['fecha']}-{_slug(n['titulo']['es'])}.md"
        (cat_dir / fname).write_text(node_note(n), encoding="utf-8")
        promoted.append(n)

    # Nota-digest del dia
    fecha = pulse["meta"]["fecha"]
    (daily_dir / f"{fecha} — Pulso.md").write_text(
        daily_note(pulse, promoted), encoding="utf-8")

    log(f"  Global Brain: {len(promoted)} notas promovidas -> {root}")
    return len(promoted)


def main() -> None:
    """Uso: python -m gp.brain [ruta/al/pulse.json]  (siembra manual)."""
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else (
        config.DATA_DIR / "pulse-latest.json")
    pulse = json.loads(path.read_text(encoding="utf-8"))
    build(pulse)


if __name__ == "__main__":
    main()
