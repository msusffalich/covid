"""Conservative event anchors shared by grouping and publication."""
import re
from .normalize import _fold

EVENT_TERMS = {
    "ceasefire": ["ceasefire", "truce", "tregua", "alto el fuego"],
    "corruption": ["corruption", "corrupcion", "bribery", "soborno", "ethics", "etica"],
    "elections": ["election", "elections", "eleccion", "elecciones", "midterms", "electoral"],
    "migration": ["migration", "migracion", "migratory", "migratoria", "immigration", "inmigracion"],
    "climate": ["climate", "climatico", "warming", "calentamiento", "deforestation", "deforestacion", "cop30"],
    "energy": ["solar", "renewable", "renovable", "energia", "energy", "diesel", "petroleo", "oil"],
    "quantum": ["quantum", "cuantica", "cuantico", "heisenberg"],
    "technology": ["chip", "chips", "semiconductor", "semiconductors", "ai", "ia", "artificial intelligence", "inteligencia artificial"],
    "disease": ["cancer", "pandemic", "pandemia", "epidemic", "epidemia", "disease", "enfermedad", "pneumonic", "neumonica"],
    "football": ["football", "futbol", "champions league", "premier league", "goals", "goles"],
    "war": ["war", "guerra", "missile", "misil", "misiles", "attack", "ataque", "strikes", "bombardeo"],
    "finance": ["inflation", "inflacion", "bank", "banco", "banking", "banca", "tariff", "arancel", "imf", "fmi"],
}

def keyword_present(text, keyword):
    return bool(re.search(r"(?<!\w)" + re.escape(_fold(keyword.strip())) + r"(?!\w)", _fold(text)))

def event_topics(text):
    return {topic for topic, words in EVENT_TERMS.items() if any(keyword_present(text, w) for w in words)}

def compatible_events(a, b):
    left, right = event_topics(a), event_topics(b)
    return not left or not right or bool(left & right)
