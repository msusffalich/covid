"""Etapa 4 — Clustering: TF-IDF intra-idioma + fusion translingue por entidades."""
import math
import re
from collections import Counter

from .config import (STOPWORDS, CLUSTER_SIM_THRESHOLD, ENTITY_MERGE_JACCARD,
                     MAX_CLUSTER_PIECES)


def _tokens(text: str) -> list[str]:
    return [t for t in re.findall(r"[a-z0-9]{3,}", text) if t not in STOPWORDS]


def _entities(piece: dict) -> set[str]:
    """Entidades aproximadas: palabras capitalizadas del titulo original
    (admite acentos y siglas con digitos, p. ej. COP30, Belem)."""
    import unicodedata
    words = re.findall(r"\b[A-ZÁÉÍÓÚÑÜ][\wáéíóúñü-]{2,}\b", piece["titulo"])
    out = set()
    for w in words:
        folded = unicodedata.normalize("NFKD", w.lower())
        folded = "".join(c for c in folded if not unicodedata.combining(c))
        if folded not in STOPWORDS:
            out.add(folded)
    return out


def _tfidf_vectors(pieces: list[dict]) -> list[dict]:
    docs = [_tokens(p["texto_norm"]) for p in pieces]
    df = Counter()
    for d in docs:
        df.update(set(d))
    n = max(len(docs), 1)
    vecs = []
    for d in docs:
        tf = Counter(d)
        vec = {t: (c / len(d)) * math.log(1 + n / df[t]) for t, c in tf.items()} if d else {}
        norm = math.sqrt(sum(v * v for v in vec.values())) or 1.0
        vecs.append({t: v / norm for t, v in vec.items()})
    return vecs


def _cos(a: dict, b: dict) -> float:
    if len(b) < len(a):
        a, b = b, a
    return sum(v * b.get(t, 0.0) for t, v in a.items())


def _cluster_lang(pieces: list[dict]) -> list[list[int]]:
    """Agrupacion greedy por similitud coseno sobre TF-IDF.

    Se compara contra la similitud MEDIA con los miembros del cluster (no la
    maxima) y se limita el tamano: evita el encadenamiento single-linkage que
    produce mega-clusters con corpus grandes.
    """
    vecs = _tfidf_vectors(pieces)
    clusters: list[list[int]] = []
    for i in range(len(pieces)):
        best, best_sim = None, CLUSTER_SIM_THRESHOLD
        for ci, cl in enumerate(clusters):
            if len(cl) >= MAX_CLUSTER_PIECES:
                continue
            sim = sum(_cos(vecs[i], vecs[j]) for j in cl) / len(cl)
            if sim >= best_sim:
                best, best_sim = ci, sim
        if best is None:
            clusters.append([i])
        else:
            clusters[best].append(i)
    return clusters


def _jaccard(a: set, b: set) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def run(pieces: list[dict], log=print) -> list[dict]:
    log("[4/8] Clustering")
    by_lang: dict[str, list[dict]] = {}
    for p in pieces:
        by_lang.setdefault(p["idioma"], []).append(p)

    proto = []       # clusters monolingues con sus entidades
    for lang, group in by_lang.items():
        for idxs in _cluster_lang(group):
            members = [group[i] for i in idxs]
            ents = set()
            for m in members:
                ents |= _entities(m)
            proto.append({"piezas": members, "entidades": ents})

    # Fusion translingue: mismo evento cubierto en es y en.
    # Exige interseccion Y solapamiento proporcional, y respeta el tope de
    # tamano: con corpus grandes la sola interseccion >=2 produce bolas de nieve.
    merged: list[dict] = []
    for c in proto:
        target = None
        for m in merged:
            if len(m["piezas"]) + len(c["piezas"]) > MAX_CLUSTER_PIECES:
                continue
            inter = c["entidades"] & m["entidades"]
            jac = _jaccard(c["entidades"], m["entidades"])
            if (len(inter) >= 2 and jac >= 0.15) or jac >= ENTITY_MERGE_JACCARD:
                target = m
                break
        if target:
            target["piezas"].extend(c["piezas"])
            target["entidades"] |= c["entidades"]
        else:
            merged.append(c)

    for i, c in enumerate(merged):
        c["cluster_id"] = f"cl_{i:03d}"
    log(f"  Clusters: {len(merged)} (desde {len(pieces)} piezas)")
    return merged
