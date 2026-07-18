"""Configuracion central del pipeline Global Pulse."""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data"
EVIDENCE_DIR = DATA_DIR / "evidence"
APP_DATA_DIR = ROOT / "app" / "public" / "data"
# Notas Obsidian (PARA). Define GP_VAULT_DIR con la ruta de tu boveda para
# que el pipeline escriba las notas directamente en tu segundo cerebro.
VAULT_DIR = (Path(os.environ["GP_VAULT_DIR"])
             if os.environ.get("GP_VAULT_DIR") else DATA_DIR / "vault")

SCHEMA_VERSION = "1.1"

# ---- Fuentes RSS (gratuitas, sin clave) -----------------------------------
# Cada fuente falla de forma aislada: si un feed cambia o cae, el ciclo
# continua y lo registra en el log. Revisar el log del cron para depurar.
RSS_SOURCES = [
    # --- Generales en espanol ---
    {"id": "bbc-mundo",   "lang": "es", "name": "BBC Mundo",
     "url": "https://feeds.bbci.co.uk/mundo/rss.xml"},
    {"id": "dw-es",       "lang": "es", "name": "DW Espanol",
     "url": "https://rss.dw.com/rdf/rss-es-all"},
    {"id": "elpais-int",  "lang": "es", "name": "El Pais Internacional",
     "url": "https://feeds.elpais.com/mrss-s/pages/ep/site/elpais.com/section/internacional/portada"},
    {"id": "france24-es", "lang": "es", "name": "France 24 Espanol",
     "url": "https://www.france24.com/es/rss"},
    {"id": "rfi-es",      "lang": "es", "name": "RFI Espanol",
     "url": "https://www.rfi.fr/es/rss"},
    {"id": "euronews-es", "lang": "es", "name": "Euronews Espanol",
     "url": "https://es.euronews.com/rss"},
    {"id": "cnn-es",      "lang": "es", "name": "CNN en Espanol",
     "url": "http://cnnespanol.cnn.com/feed/"},
    {"id": "onu-es",      "lang": "es", "name": "Noticias ONU",
     "url": "https://news.un.org/feed/subscribe/es/news/all/rss.xml"},
    {"id": "elmundo-int", "lang": "es", "name": "El Mundo Internacional",
     "url": "https://e00-elmundo.uecdn.es/elmundo/rss/internacional.xml"},
    {"id": "infobae",     "lang": "es", "name": "Infobae America",
     "url": "https://www.infobae.com/feeds/rss/"},
    # --- Generales en ingles ---
    {"id": "bbc-world",   "lang": "en", "name": "BBC News World",
     "url": "https://feeds.bbci.co.uk/news/world/rss.xml"},
    {"id": "dw-en",       "lang": "en", "name": "DW English",
     "url": "https://rss.dw.com/rdf/rss-en-all"},
    {"id": "guardian-world", "lang": "en", "name": "The Guardian World",
     "url": "https://www.theguardian.com/world/rss"},
    {"id": "france24-en", "lang": "en", "name": "France 24 English",
     "url": "https://www.france24.com/en/rss"},
    {"id": "aljazeera",   "lang": "en", "name": "Al Jazeera",
     "url": "https://www.aljazeera.com/xml/rss/all.xml"},
    {"id": "npr",         "lang": "en", "name": "NPR News",
     "url": "https://feeds.npr.org/1001/rss.xml"},
    {"id": "nyt-world",   "lang": "en", "name": "NYT World",
     "url": "https://rss.nytimes.com/services/xml/rss/nyt/World.xml"},
    {"id": "euronews-en", "lang": "en", "name": "Euronews English",
     "url": "https://www.euronews.com/rss"},
    {"id": "un-news-en",  "lang": "en", "name": "UN News",
     "url": "https://news.un.org/feed/subscribe/en/news/all/rss.xml"},
    {"id": "skynews",     "lang": "en", "name": "Sky News World",
     "url": "https://feeds.skynews.com/feeds/rss/world.xml"},
    {"id": "independent", "lang": "en", "name": "The Independent World",
     "url": "https://www.independent.co.uk/news/world/rss"},
    {"id": "cbc-world",   "lang": "en", "name": "CBC World",
     "url": "https://www.cbc.ca/webfeed/rss/rss-world"},
    {"id": "abc-au",      "lang": "en", "name": "ABC News Australia",
     "url": "https://www.abc.net.au/news/feed/51120/rss.xml"},
    # --- Ciencia y clima ---
    {"id": "nature",      "lang": "en", "name": "Nature News",
     "url": "https://www.nature.com/nature.rss"},
    {"id": "sciencedaily", "lang": "en", "name": "ScienceDaily",
     "url": "https://www.sciencedaily.com/rss/top/science.xml"},
    {"id": "physorg",     "lang": "en", "name": "Phys.org",
     "url": "https://phys.org/rss-feed/"},
    {"id": "nasa",        "lang": "en", "name": "NASA News",
     "url": "https://www.nasa.gov/rss/dyn/breaking_news.rss"},
    {"id": "who-news",    "lang": "en", "name": "WHO News",
     "url": "https://www.who.int/rss-feeds/news-english.xml"},
    # --- Tecnologia ---
    {"id": "arstechnica", "lang": "en", "name": "Ars Technica",
     "url": "https://feeds.arstechnica.com/arstechnica/index"},
    {"id": "verge",       "lang": "en", "name": "The Verge",
     "url": "https://www.theverge.com/rss/index.xml"},
    {"id": "wired",       "lang": "en", "name": "WIRED",
     "url": "https://www.wired.com/feed/rss"},
    # --- Economia ---
    {"id": "cnbc-top",    "lang": "en", "name": "CNBC Top News",
     "url": "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=100003114"},
    {"id": "marketwatch", "lang": "en", "name": "MarketWatch",
     "url": "https://feeds.content.dowjones.io/public/rss/mw_topstories"},
]

# GDELT DOC 2.0 (eventos globales, sin clave)
GDELT_URL = ("https://api.gdeltproject.org/api/v2/doc/doc"
             "?query={query}&mode=artlist&maxrecords=60&format=json"
             "&timespan=24h")
GDELT_QUERIES = ["crisis OR summit OR breakthrough OR disaster OR election"]

# ---- Sintesis --------------------------------------------------------------
ANTHROPIC_MODEL = "claude-sonnet-5"
ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"

# Umbrales
MIN_CLUSTER_SIZE = 1          # piezas minimas para sintetizar un cluster
MAX_NODES_PER_PULSE = 14      # nodos maximos publicados por dia
IMPACT_THRESHOLD = 35         # impacto minimo para publicar
PROMOTE_THRESHOLD = 60        # impacto minimo para promover a Obsidian
CLUSTER_SIM_THRESHOLD = 0.32  # similitud TF-IDF minima intra-idioma (media)
ENTITY_MERGE_JACCARD = 0.34   # fusion de clusters entre idiomas
MAX_CLUSTER_PIECES = 12       # tope de piezas por cluster (evita bolas de nieve)
MAX_REFS_PER_NODE = 12        # referencias maximas mostradas por nodo

CATEGORIES = ["geopolitica", "economia", "ciencia", "clima", "tecnologia", "sociedad"]

# Palabras clave por categoria (es + en, minusculas)
CATEGORY_KEYWORDS = {
    "geopolitica": ["guerra", "war", "tratado", "treaty", "cumbre", "summit",
                    "sancion", "sanction", "eleccion", "election", "otan", "nato",
                    "onu", "un ", "frontera", "border", "conflicto", "conflict",
                    "diplomacia", "diplomacy", "militar", "military", "acuerdo"],
    "economia":    ["inflacion", "inflation", "banco central", "central bank",
                    "mercado", "market", "pib", "gdp", "arancel", "tariff",
                    "comercio", "trade", "divisa", "currency", "recesion",
                    "recession", "empleo", "employment", "fmi", "imf"],
    "ciencia":     ["vacuna", "vaccine", "descubrimiento", "discovery",
                    "investigacion", "research", "estudio", "study", "nasa",
                    "esa", "telescopio", "telescope", "genoma", "genome",
                    "farmaco", "drug", "ensayo clinico", "clinical trial"],
    "clima":       ["clima", "climate", "sequia", "drought", "inundacion",
                    "flood", "huracan", "hurricane", "emision", "emission",
                    "cop", "temperatura", "temperature", "incendio", "wildfire",
                    "glaciar", "glacier", "energia renovable", "renewable"],
    "tecnologia":  ["inteligencia artificial", "artificial intelligence", " ia ",
                    " ai ", "chip", "semiconductor", "ciberseguridad",
                    "cybersecurity", "satelite", "satellite", "software",
                    "startup", "quantum", "cuantica", "robot", "5g", "datos"],
    "sociedad":    ["salud", "health", "educacion", "education", "migracion",
                    "migration", "derechos", "rights", "protesta", "protest",
                    "cultura", "culture", "poblacion", "population"],
}

# Gazetteer minimo: pais/region -> (lat, lon, region legible)
GAZETTEER = {
    "ucrania": (48.4, 31.2, "Europa del Este"), "ukraine": (48.4, 31.2, "Europa del Este"),
    "rusia": (61.5, 105.3, "Rusia"), "russia": (61.5, 105.3, "Rusia"),
    "china": (35.9, 104.2, "Asia Oriental"),
    "taiwan": (23.7, 121.0, "Asia Oriental"),
    "estados unidos": (39.8, -98.6, "Norteamerica"), "united states": (39.8, -98.6, "Norteamerica"),
    "washington": (38.9, -77.0, "Norteamerica"), "eeuu": (39.8, -98.6, "Norteamerica"),
    "mexico": (23.6, -102.5, "Norteamerica"),
    "brasil": (-14.2, -51.9, "Sudamerica"), "brazil": (-14.2, -51.9, "Sudamerica"),
    "argentina": (-38.4, -63.6, "Sudamerica"),
    "chile": (-35.7, -71.5, "Sudamerica"),
    "colombia": (4.6, -74.3, "Sudamerica"),
    "peru": (-9.2, -75.0, "Sudamerica"),
    "venezuela": (6.4, -66.6, "Sudamerica"),
    "union europea": (50.8, 4.4, "Europa"), "european union": (50.8, 4.4, "Europa"),
    "bruselas": (50.8, 4.4, "Europa"), "brussels": (50.8, 4.4, "Europa"),
    "alemania": (51.2, 10.4, "Europa"), "germany": (51.2, 10.4, "Europa"),
    "francia": (46.6, 2.2, "Europa"), "france": (46.6, 2.2, "Europa"),
    "espana": (40.5, -3.7, "Europa"), "spain": (40.5, -3.7, "Europa"),
    "reino unido": (54.0, -2.5, "Europa"), "united kingdom": (54.0, -2.5, "Europa"),
    "italia": (41.9, 12.6, "Europa"), "italy": (41.9, 12.6, "Europa"),
    "india": (20.6, 79.0, "Asia Meridional"),
    "pakistan": (30.4, 69.3, "Asia Meridional"),
    "japon": (36.2, 138.3, "Asia Oriental"), "japan": (36.2, 138.3, "Asia Oriental"),
    "corea del sur": (35.9, 127.8, "Asia Oriental"), "south korea": (35.9, 127.8, "Asia Oriental"),
    "corea del norte": (40.3, 127.5, "Asia Oriental"), "north korea": (40.3, 127.5, "Asia Oriental"),
    "iran": (32.4, 53.7, "Oriente Medio"),
    "israel": (31.0, 34.9, "Oriente Medio"),
    "gaza": (31.4, 34.4, "Oriente Medio"),
    "arabia saudita": (23.9, 45.1, "Oriente Medio"), "saudi arabia": (23.9, 45.1, "Oriente Medio"),
    "turquia": (39.0, 35.2, "Oriente Medio"), "turkey": (39.0, 35.2, "Oriente Medio"),
    "egipto": (26.8, 30.8, "Africa del Norte"), "egypt": (26.8, 30.8, "Africa del Norte"),
    "nigeria": (9.1, 8.7, "Africa Occidental"),
    "sudafrica": (-30.6, 22.9, "Africa Austral"), "south africa": (-30.6, 22.9, "Africa Austral"),
    "etiopia": (9.1, 40.5, "Africa Oriental"), "ethiopia": (9.1, 40.5, "Africa Oriental"),
    "kenia": (-0.02, 37.9, "Africa Oriental"), "kenya": (-0.02, 37.9, "Africa Oriental"),
    "australia": (-25.3, 133.8, "Oceania"),
    "antartida": (-82.9, 135.0, "Antartida"), "antarctica": (-82.9, 135.0, "Antartida"),
    "artico": (78.0, 15.0, "Artico"), "arctic": (78.0, 15.0, "Artico"),
    "ginebra": (46.2, 6.1, "Europa"), "geneva": (46.2, 6.1, "Europa"),
    "indonesia": (-0.8, 113.9, "Sudeste Asiatico"),
    "filipinas": (12.9, 121.8, "Sudeste Asiatico"), "philippines": (12.9, 121.8, "Sudeste Asiatico"),
    "vietnam": (14.1, 108.3, "Sudeste Asiatico"),
    "canada": (56.1, -106.3, "Norteamerica"),
}

STOPWORDS = set("""el la los las un una unos unas de del al a en y o que se su sus por para con sin sobre entre tras es son fue fueron ser esta estan como mas pero ya no si lo le les este esta estos estas
the a an of in on and or that is are was were be as it its this these those with for from by at to not but have has had will would can could their there
""".split())
