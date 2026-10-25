import hashlib
import importlib.util
import json
import sys
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch


class BridgeTests(unittest.TestCase):
    def test_canonical_empty_day_preserves_annotations(self):
        path = Path(__file__).resolve().parents[2] / 'integrations/archivar-global-brain.py'
        spec = importlib.util.spec_from_file_location('bridge', path)
        bridge = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(bridge)
        date = datetime.now().date().isoformat()
        report = '---\ntipo: "pulso-global"\nfecha: "' + date + '"\ndimensiones: []\nlugares: []\n---\n\n# Pulso Global — ' + date + '\n\nSin novedad oficial verificable en las últimas 24 horas.\n'
        pulse = {'meta': {'schema': '2.0', 'modo': 'live', 'fecha': date, 'reporte_sha256': hashlib.sha256(report.encode()).hexdigest()}, 'nodos': [], 'reporte_markdown': report}
        trends = {'meta': {'modo': 'live', 'generado': date + 'T05:00:00+00:00'}, 'temas': []}
        def get_json(url):
            value = {'reportes': [], 'schema': 1} if url.endswith('history.json') else (pulse if url.endswith('pulse-latest.json') else trends)
            return value, json.dumps(value).encode()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            vault = root / 'vault'
            vault.mkdir()
            (vault / '00 Oria.md').write_text('# Oria\n', encoding='utf-8')
            (root / 'oria.config.json').write_text(json.dumps({'boveda': str(vault)}))
            note = vault / 'Global Brain/Reportes' / ('Global Brain — Reporte ' + date + '.md')
            note.parent.mkdir(parents=True)
            note.write_text('---\ntipo: reporte-global-brain\nfecha: ' + date + '\naliases: [Mi alias]\n---\n\n<!-- global-brain-generado -->\nOld\n<!-- /global-brain-generado -->\n\n## Mis notas\nTexto personal intacto.\n', encoding='utf-8')
            with patch.object(bridge, 'get_json', side_effect=get_json), patch.object(sys, 'argv', ['bridge', '--oria', str(root), '--actualizar']):
                bridge.main()
                first = note.read_bytes()
                bridge.main()
            self.assertEqual(note.read_bytes(), first)
            text = first.decode()
            self.assertIn('Texto personal intacto.', text)
            self.assertIn('aliases: [Mi alias]', text)
            self.assertIn('tipo: "pulso-global"', text.split('\n---\n')[0])
            self.assertNotIn('Old', text)
            self.assertEqual((vault / 'Global Brain/Fuentes' / date / 'reporte.md').read_text(encoding='utf-8'), report)


if __name__ == '__main__':
    unittest.main()
