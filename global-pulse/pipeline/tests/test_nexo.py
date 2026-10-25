import json
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch
from gp import daily, collect, config, publish
from gp.official import admit


class NexoTests(unittest.TestCase):
    def setUp(self):
        self.cutoff = datetime(2026, 10, 25, 5, tzinfo=timezone.utc)
        self.piece = dict(fuente_id='fed', url='https://www.federalreserve.gov/newsevents/pressreleases/example.htm', fecha_pub=self.cutoff.isoformat())

    def test_admission(self):
        self.assertTrue(admit(self.piece, self.cutoff))
        for changes in ({'fuente_id': 'bbc'}, {'url': 'https://federalreserve.gov.evil.org/x'},
                        {'url': 'https://evil.org/federalreserve.gov'}, {'fecha_pub': '2026-10-25'},
                        {'fecha_pub': (self.cutoff + timedelta(seconds=1)).isoformat()},
                        {'fecha_pub': (self.cutoff - timedelta(hours=24)).isoformat()},
                        {'fecha_pub': ''}):
            self.assertFalse(admit(dict(self.piece, **changes), self.cutoff))

    def test_atom_published_not_updated(self):
        feed = b'<feed xmlns="http://www.w3.org/2005/Atom"><entry><title>Official publication</title><published>2026-10-25T05:00:00Z</published><updated>2026-10-26T05:00:00Z</updated><link href="https://www.federalreserve.gov/item"/></entry></feed>'
        pieces = collect.parse_rss(feed, dict(id='fed', name='Fed', lang='en'))
        self.assertEqual(pieces[0]['fecha_pub'], '2026-10-25T05:00:00Z')

    def test_empty_and_pending_report(self):
        state = dict(fecha='2026-10-25', corte=self.cutoff.isoformat(), inicio_ventana='2026-10-24T05:00:00+00:00', hechos=[], cobertura={})
        pending = daily.markdown(state)
        self.assertEqual(pending.count(daily.NO_FACTS), 7)
        self.assertIn('análisis pendiente', pending)
        state['analisis'] = daily.analyze([])
        complete = daily.markdown(state)
        self.assertNotIn('análisis pendiente', complete)
        self.assertEqual(complete.count(daily.NO_MOVEMENT), 7)
        for key in ('dimensiones', 'lugares', 'paises', 'entidades', 'temas', 'bucles_activos'):
            self.assertIn(key + ': []', complete)

    def test_analysis_rejects_unpublished_citations(self):
        fake = dict(resumen=['a', 'b', 'c'], flujos={n: dict(estado=daily.NO_MOVEMENT, texto='', hechos=[]) for n in daily.FLOWS},
                    bucles={n: dict(estado=daily.NO_MOVEMENT, texto='', hechos=[]) for n in daily.LOOPS}, senales=[], correcciones=[])
        fake['flujos']['Presión Climática'] = dict(estado='Con movimiento', texto='Unsupported', hechos=['unknown'])
        with patch.object(daily, 'ask', return_value=fake), self.assertRaises(ValueError):
            daily.analyze([dict(id='ev_1', dimension='clima')])

    def test_publish_keeps_canonical_bytes_and_empty_day(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            state = dict(fecha='2026-10-25', corte=self.cutoff.isoformat(), analisis={}, cobertura={}, hechos=[])
            report = '# Pulso Global — 2026-10-25\n'
            with patch.object(config, 'DATA_DIR', root / 'data'), patch.object(config, 'APP_DATA_DIR', root / 'app'):
                out = publish.run([], 'live', 'api', {}, lambda _: None, report=report, state=state)
                self.assertEqual(out['reporte_markdown'], report)
                self.assertEqual((root / 'app' / '2026-10-25 — Pulso.md').read_bytes(), report.encode())
                self.assertEqual(out['meta']['schema'], '2.0')
                self.assertEqual(len(json.loads((root / 'app/history.json').read_text())['reportes']), 1)

    def test_media_and_cnn_publication_date(self):
        p = dict(self.piece, fuente_id='bbc-world', url='https://www.bbc.com/news/articles/test')
        self.assertTrue(admit(p, self.cutoff))
        self.assertFalse(admit(dict(p, url='https://fake-bbc.com/item'), self.cutoff))
        xml = b'<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:n="http://www.google.com/schemas/sitemap-news/0.9"><url><loc>https://www.cnn.com/article</loc><lastmod>2026-10-26T05:00:00Z</lastmod><n:news><n:publication_date>2026-10-25T05:00:00Z</n:publication_date><n:title>Published news</n:title></n:news></url></urlset>'
        item = collect.parse_rss(xml, dict(id='cnn', name='CNN', lang='en'))[0]
        self.assertEqual(item['fecha_pub'], '2026-10-25T05:00:00Z')


if __name__ == '__main__':
    unittest.main()
