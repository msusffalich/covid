import asyncio
import io
import json
import sys
import unittest
import urllib.error
from pathlib import Path
from unittest.mock import AsyncMock, patch

from gp import daily, openai_client, synthesize, trends

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / 'backend'))
from agents import research_agent
from utils import openai_client as backend_client


def response(value, function=False, status='completed'):
    item = ({'type': 'function_call', 'name': 'entregar_resultado', 'arguments': json.dumps(value)}
            if function else {'type': 'message', 'content': [{'type': 'output_text', 'text': json.dumps(value)}]})
    return io.BytesIO(json.dumps({'status': status, 'output': [item]}).encode())


class OpenAITests(unittest.TestCase):
    def test_transports_options_and_model_override(self):
        for client in (openai_client, backend_client):
            with self.subTest(client=client.__name__), patch.dict('os.environ', {'OPENAI_MODEL': 'custom-model'}), patch(
                    'urllib.request.urlopen', return_value=response({'ok': True})) as send:
                self.assertEqual(json.loads(client.respond('JSON please', 'data', api_key='fake', max_tokens=42)), {'ok': True})
                request = send.call_args.args[0]
                payload = json.loads(request.data)
                self.assertEqual(request.full_url, 'https://api.openai.com/v1/responses')
                self.assertEqual(request.get_header('Authorization'), 'Bearer fake')
                self.assertNotIn('X-api-key', request.headers)
                self.assertEqual(payload['model'], 'custom-model')
                self.assertEqual(payload['max_output_tokens'], 42)
                self.assertFalse(payload['store'])
                self.assertNotIn('prompt_cache_key', payload)

    def test_incomplete_refused_and_malformed_responses(self):
        for value in ({'status': 'incomplete', 'output': []}, {'status': 'failed'},
                      {'status': 'completed', 'output': [{'type': 'message', 'content': [{'type': 'refusal'}]}]}):
            for client in (openai_client, backend_client):
                with patch('urllib.request.urlopen', return_value=io.BytesIO(json.dumps(value).encode())), self.assertRaises(ValueError):
                    client.respond('JSON', 'test', api_key='fake')
        with patch('urllib.request.urlopen', return_value=response([], function=True)), self.assertRaises(ValueError):
            openai_client.respond('JSON', 'test', api_key='fake', schema={'type': 'object'})

    def test_http_errors_do_not_expose_secrets(self):
        error = urllib.error.HTTPError('https://api.openai.com/v1/responses', 429, 'rate limit', {},
                                     io.BytesIO(b'{"error":{"code":"insufficient_quota"}}'))
        with patch('urllib.request.urlopen', side_effect=error), self.assertRaisesRegex(RuntimeError, '429: insufficient_quota'):
            openai_client.respond('JSON', 'test', api_key='never-log-this')

    def test_missing_key_fails_before_network(self):
        with patch.dict('os.environ', {'OPENAI_API_KEY': ''}), patch('urllib.request.urlopen') as send, self.assertRaises(RuntimeError):
            openai_client.respond('JSON', 'test')
        send.assert_not_called()

    def test_nexo_facts_and_analysis_force_data_function(self):
        for value, result in (([], {'hechos': []}), ({}, {'resumen': [], 'flujos': {}, 'bucles': {}, 'senales': [], 'correcciones': []})):
            with patch.dict('os.environ', {'OPENAI_API_KEY': 'fake'}), patch('urllib.request.urlopen', return_value=response(result, True)) as send:
                self.assertEqual(daily.ask('JSON', value), result)
                payload = json.loads(send.call_args.args[0].data)
                self.assertEqual(payload['tool_choice']['name'], 'entregar_resultado')
                self.assertFalse(payload['parallel_tool_calls'])
                self.assertEqual(payload['max_output_tokens'], 16000)
                self.assertEqual(set(payload['tools'][0]['parameters']['required']), set(result))

    def test_cluster_and_trend_routes(self):
        piece = dict(id='ev_test', titulo='Test', cuerpo='A source statement.', fuente='Test', idioma='en', fecha_pub='2026-11-12')
        with patch('urllib.request.urlopen', return_value=response({'titulo': {'es': 'Prueba'}})) as send:
            self.assertIn('titulo', synthesize.synth_api({'piezas': [piece]}, 'fake'))
            self.assertEqual(json.loads(send.call_args.args[0].data)['max_output_tokens'], 900)
        node = dict(fecha='2026-11-12', titulo={'es': 'Prueba'}, sintesis={'es': 'Resumen'})
        with patch('urllib.request.urlopen', return_value=response({'resumen': {}, 'estado': {}})) as send:
            self.assertIn('resumen', trends._synth_api({'nombre': {'es': 'Tema'}}, [node], 'fake'))
            self.assertEqual(json.loads(send.call_args.args[0].data)['max_output_tokens'], 500)

    def test_research_progress_and_session_persistence(self):
        result = {'executive_summary': 'Summary', 'sources': [{'url': 'https://example.org'}], 'sections': []}
        async def run():
            with patch.object(research_agent, '_web_search', return_value=[{'url': 'https://example.org', 'title': 'Test', 'content': 'Evidence'}]), patch.object(
                    research_agent, 'update_session', new_callable=AsyncMock) as persist, patch.dict('os.environ', {'OPENAI_API_KEY': 'fake'}), patch(
                    'urllib.request.urlopen', return_value=response(result)) as send:
                events = [event async for event in research_agent.run_research('test-session', 'Test', 'es')]
                self.assertEqual([e['data']['step'] for e in events], [1, 2, 3, 4])
                persist.assert_awaited_once_with('test-session', summary='Summary', sources=result['sources'], structured_data=result)
                payload = json.loads(send.call_args.args[0].data)
                self.assertEqual(payload['max_output_tokens'], 8192)
                self.assertIn('Investigador', payload['input'][0]['content'])
        asyncio.run(run())


if __name__ == '__main__':
    unittest.main()
