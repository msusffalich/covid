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
    ('un-en', 'ONU (inglés)', 'geopolitica', 'https://news.un.org/feed/subscribe/en/news/all/rss.xml', ['un.org']),
    ('consilium', 'Consejo de la Unión Europea', 'geopolitica', 'https://www.consilium.europa.eu/en/rss/pressreleases.ashx', ['consilium.europa.eu']),
    ('google', 'Google', 'tecnologia', 'https://blog.google/rss/', ['blog.google', 'google.com']),
    ('microsoft', 'Microsoft', 'tecnologia', 'https://blogs.microsoft.com/feed/', ['microsoft.com']),
    ('meta', 'Meta', 'tecnologia', 'https://about.fb.com/news/feed/', ['fb.com', 'meta.com']),
    ('apple', 'Apple', 'tecnologia', 'https://www.apple.com/newsroom/rss-feed.rss', ['apple.com']),
    ('nist', 'NIST', 'tecnologia', 'https://www.nist.gov/news-events/news/rss.xml', ['nist.gov']),
    ('esa', 'Agencia Espacial Europea', 'tecnologia', 'https://www.esa.int/rssfeed/Our_Activities', ['esa.int']),
    ('noaa-ncei', 'NOAA NCEI', 'clima', 'https://www.ncei.noaa.gov/feed', ['noaa.gov']),
    ('noaa-nhc', 'NOAA · Centro Nacional de Huracanes', 'clima', 'https://www.nhc.noaa.gov/index-at.xml', ['noaa.gov']),
    ('nasa-releases', 'NASA · Comunicados', 'tecnologia', 'https://www.nasa.gov/news-release/feed/', ['nasa.gov']),
    ('usda', 'Departamento de Agricultura de EE. UU.', 'recursos', 'https://www.usda.gov/rss/latest-releases.xml', ['usda.gov']),
    ('ec-trade', 'Comisión Europea · Comercio', 'cadenas', 'https://policy.trade.ec.europa.eu/node/2/rss_en', ['ec.europa.eu', 'europa.eu']),
    ('bis', 'Banco de Pagos Internacionales', 'finanzas', 'https://www.bis.org/doclist/all_pressrels.rss', ['bis.org']),
    ('boe', 'Banco de Inglaterra', 'finanzas', 'https://www.bankofengland.co.uk/rss/news', ['bankofengland.co.uk']),
    ('boj', 'Banco de Japón', 'finanzas', 'https://www.boj.or.jp/en/rss/whatsnew.xml', ['boj.or.jp']),
    ('census', 'Oficina del Censo de EE. UU.', 'demografia', 'https://www.census.gov/content/census/en/newsroom/press-releases.xml', ['census.gov']),
]
RSS_SOURCES = [dict(id=i, name=n, dimension=d, url=u, domains=hosts, lang='es' if i == 'un' else 'en')
               for i, n, d, u, hosts in SOURCES]
MEDIA = [
    ('bbc-world', 'BBC News', 'https://feeds.bbci.co.uk/news/world/rss.xml', ['bbc.com', 'bbc.co.uk'], 'en'),
    ('bbc-mundo', 'BBC Mundo', 'https://feeds.bbci.co.uk/mundo/rss.xml', ['bbc.com', 'bbc.co.uk'], 'es'),
    ('cnn', 'CNN', 'https://www.cnn.com/sitemap/news.xml', ['cnn.com'], 'en'),
    ('dw-es', 'Deutsche Welle', 'https://rss.dw.com/rdf/rss-es-all', ['dw.com'], 'es'),
    ('france24', 'France 24', 'https://www.france24.com/es/rss', ['france24.com'], 'es'),
    ('guardian', 'The Guardian', 'https://www.theguardian.com/world/rss', ['theguardian.com'], 'en'),
    ('aljazeera', 'Al Jazeera', 'https://www.aljazeera.com/xml/rss/all.xml', ['aljazeera.com'], 'en'),
    ('elpais', 'El País', 'https://feeds.elpais.com/mrss-s/pages/ep/site/elpais.com/section/internacional/portada', ['elpais.com'], 'es'),
    ('cnbc', 'CNBC', 'https://www.cnbc.com/id/100003114/device/rss/rss.html', ['cnbc.com'], 'en'),
    ('reuters', 'Reuters', 'https://www.reuters.com/arc/outboundfeeds/v3/all/?outputType=xml', ['reuters.com'], 'en'),
    ('reuters-best', 'Reuters Best', 'https://reutersbest.com/region/global/feed/', ['reutersbest.com'], 'en'),
    ('efe', 'Agencia EFE', 'https://efe.com/feed/', ['efe.com'], 'es'),
    ('marketwatch', 'MarketWatch', 'https://feeds.content.dowjones.io/public/rss/mw_topstories', ['marketwatch.com'], 'en'),
    ('guardian-environment', 'The Guardian · Medio ambiente', 'https://www.theguardian.com/environment/rss', ['theguardian.com'], 'en'),
    ('bbc-tech', 'BBC · Tecnología', 'https://feeds.bbci.co.uk/news/technology/rss.xml', ['bbc.com', 'bbc.co.uk'], 'en'),
    ('bbc-business', 'BBC · Economía', 'https://feeds.bbci.co.uk/news/business/rss.xml', ['bbc.com', 'bbc.co.uk'], 'en'),
]
for source in RSS_SOURCES:
    source['tipo'] = 'oficial'
RSS_SOURCES += [dict(id=i, name=n, dimension='geopolitica', url=u, domains=hosts, lang=lang,
                     tipo='agencia' if i in {'reuters', 'reuters-best', 'efe'} else 'medio', transversal=True)
                for i, n, u, hosts, lang in MEDIA]
for source in RSS_SOURCES:
    if source['id'] in {'un', 'un-en', 'govuk', 'consilium', 'worldbank', 'eurostat'}:
        source['transversal'] = True
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
