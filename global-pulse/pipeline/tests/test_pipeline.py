"""Tests del pipeline Global Pulse (sin dependencias externas).

Ejecutar:  python -m tests.test_pipeline   (desde global-pulse/pipeline)
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from gp import collect, normalize, cluster, synthesize, validate, config  # noqa: E402


def log_silent(_msg):
    pass


def test_normalize_dedup():
    pieces = [
        {"titulo": "Prueba de <b>titulo</b> con HTML &amp; entidades largas",
         "cuerpo": "Cuerpo x", "idioma": "es", "fuente_id": "t"},
        {"titulo": "Prueba de titulo con HTML & entidades largas",
         "cuerpo": "Cuerpo con mas texto que el anterior", "idioma": "es",
         "fuente_id": "t"},
        {"titulo": "corto", "cuerpo": "", "idioma": "es", "fuente_id": "t"},
    ]
    norm = normalize.normalize(pieces, log_silent)
    assert len(norm) == 2, "el titulo corto debe descartarse"
    dd = normalize.dedup(norm, log_silent)
    assert len(dd) == 1, "duplicados por hash deben fusionarse"
    assert "mas texto" in dd[0]["cuerpo"], "debe conservar la version con mas cuerpo"
    assert dd[0]["id"].startswith("ev_")


def test_full_cycle_fixture():
    pieces = collect.run("fixture", log_silent)
    pieces = normalize.normalize(pieces, log_silent)
    pieces = normalize.dedup(pieces, log_silent)
    assert len(pieces) >= 14

    clusters = cluster.run(pieces, log_silent)
    # Los 8 eventos bilingues deben fusionarse translingualmente (no 16 clusters)
    assert len(clusters) <= 10, f"fusion translingue fallo: {len(clusters)} clusters"
    bilingual = [c for c in clusters
                 if len({p['idioma'] for p in c['piezas']}) == 2]
    assert len(bilingual) >= 6, f"solo {len(bilingual)} clusters bilingues"

    nodes = synthesize.run(clusters, "heuristic", log_silent)
    assert nodes, "debe producir nodos"
    for n in nodes:
        assert synthesize.validate_node_shape(n)
        assert n["sintesis"]["es"] and n["sintesis"]["en"]

    nodes = validate.run(nodes, pieces, log_silent)
    for n in nodes:
        if n["estado"] == "verificado":
            assert n["fuentes"], "regla de oro: verificado exige fuentes"
            assert n["impacto"] is not None
        else:
            assert n["impacto"] is None, "sin_verificar no lleva impacto"

    geolocated = [n for n in nodes if n["geo"]["region"] != "Global"]
    assert len(geolocated) >= 4, "el gazetteer debe geolocalizar la mayoria"


def test_pulse_schema():
    path = config.DATA_DIR / "pulse-latest.json"
    if not path.exists():
        print("  (pulse-latest.json aun no generado; se omite)")
        return
    pulse = json.loads(path.read_text(encoding="utf-8"))
    assert pulse["meta"]["schema"] == config.SCHEMA_VERSION
    for n in pulse["nodos"]:
        for field in ("id", "titulo", "sintesis", "categoria", "actores",
                      "geo", "impacto", "relaciones", "fuentes", "imagenes",
                      "estado", "fecha", "referencias"):
            assert field in n, f"falta campo {field} en {n.get('id')}"
        assert n["categoria"] in config.CATEGORIES
        assert n["id"].startswith("nd_")


def test_global_brain():
    import tempfile
    from pathlib import Path as P
    from gp import brain

    pulse_path = config.DATA_DIR / "pulse-latest.json"
    if not pulse_path.exists():
        print("  (pulse-latest.json aun no generado; se omite)")
        return
    pulse = json.loads(pulse_path.read_text(encoding="utf-8"))

    old_vault = config.VAULT_DIR
    with tempfile.TemporaryDirectory() as tmp:
        config.VAULT_DIR = P(tmp) / "Global Brain"
        try:
            promoted = brain.build(pulse, lambda m: None)
        finally:
            root, config.VAULT_DIR = config.VAULT_DIR, old_vault
        assert (root / "Global Brain — Inicio.md").exists()
        assert (root / "20 · Indices" / "Escala Kardashev"
                / "K1 · Planetario.md").exists()
        fecha = pulse["meta"]["fecha"]
        assert (root / "00 · Pulso Diario" / f"{fecha} — Pulso.md").exists()
        # Todos los nodos quedan clasificados en la escala Kardashev
        for n in pulse["nodos"]:
            assert n["kardashev"] in brain.K_LEVELS
        if promoted:
            notes = list((root / "10 · Nodos").rglob("*.md"))
            assert len(notes) == promoted
            body = notes[0].read_text(encoding="utf-8")
            assert "kardashev:" in body and "Capa 3" in body


if __name__ == "__main__":
    fails = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
                print(f"PASS {name}")
            except AssertionError as e:
                fails += 1
                print(f"FAIL {name}: {e}")
    sys.exit(1 if fails else 0)
