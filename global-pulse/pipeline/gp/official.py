"""Primary-source registry and strict publication-time admission rules."""
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from urllib.parse import urlsplit

DIMENSIONS = {
    'clima': 'Cambio Climático', 'tecnologia': 'Tecnología',
    'recursos': 'Recursos Naturales', 'cadenas': 'Cadenas de Suministro',
    'geopolitica': 'Geopolítica', 'finanzas': 'Finanzas y Seguros',
    'demografia': 'Demografía y Migraciones',
}

# Explicit attribution: links must belong to the institution supplying the feed.
SOURCES = [
    ('noaa', 'NOAA', 'clima', 'https://www.noaa.gov/rss.xml', ['noaa.gov']),
    ('openai', 'OpenAI', 'tecnologia', 'https://openai.com/news/rss.xml', ['openai.com']),
    ('nasa', 'NASA', 'tecnologia', 'https://www.nasa.gov/feed/', ['nasa.gov']),
    ('cisa', 'CISA', 'tecnologia', 'https://www.cisa.gov/cybersecurity-advisories/all.xml', ['cisa.gov']),
    ('eia', 'EIA', 'recursos', 'https://www.eia.gov/rss/todayinenergy.xml', ['eia.gov']),
    ('fao', 'FAO', 'recursos', 'https://www.fao.org/feeds/fao-newsroom-rss', ['fao.org']),
    ('wto', 'OMC', 'cadenas', 'https://www.wto.org/library/rss/latest_news_e.xml', ['wto.org']),
    ('un', 'ONU', 'geopolitica', 'https://news.un.org/feed/subscribe/es/news/all/rss.xml', ['un.org']),
    ('fed', 'Reserva Federal', 'finanzas', 'https://www.federalreserve.gov/feeds/press_all.xml', ['federalreserve.gov']),
    ('ecb', 'BCE', 'finanzas', 'https://www.ecb.europa.eu/rss/press.html', ['ecb.europa.eu']),
    ('imf', 'FMI', 'finanzas', 'https://www.imf.org/en/News/RSS', ['imf.org']),
    ('iom', 'OIM', 'demografia', 'https://www.iom.int/rss.xml', ['iom.int']),
    ('unhcr', 'ACNUR', 'demografia', 'https://www.unhcr.org/rss.xml', ['unhcr.org']),
]
RSS_SOURCES = [dict(id=i, name=n, dimension=d, url=u, domains=hosts, lang='es' if i == 'un' else 'en')
               for i, n, d, u, hosts in SOURCES]
BY_ID = {s['id']: s for s in RSS_SOURCES}


def publication_time(value):
    if not value:
        return None
    try:
        stamp = datetime.fromisoformat(value.replace('Z', '+00:00'))
    except (ValueError, TypeError):
        try:
            stamp = parsedate_to_datetime(value)
        except (ValueError, TypeError, OverflowError):
            return None
    # A date without timezone/time cannot prove membership in a 24-hour window.
    return stamp.astimezone(timezone.utc) if stamp.tzinfo else None


def admit(piece, cutoff):
    source = BY_ID.get(piece.get('fuente_id'))
    stamp = publication_time(piece.get('fecha_pub'))
    url = urlsplit(piece.get('url', ''))
    host = (url.hostname or '').lower()
    return bool(source and stamp and cutoff - timedelta(hours=24) < stamp <= cutoff
                and url.scheme == 'https' and not url.username
                and any(host == d or host.endswith('.' + d) for d in source['domains']))
