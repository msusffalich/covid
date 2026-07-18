# Global Pulse

**ES** · Ecosistema de inteligencia estratégica de triple capa: transforma el ruido
informativo global en conocimiento accionable y lo entreteje con tu segundo cerebro
(Obsidian/PARA). Implementación del *Blueprint de Arquitectura Global Pulse v1.0*.

**EN** · Three-layer strategic intelligence ecosystem: it turns global information
noise into actionable knowledge and weaves it into your second brain
(Obsidian/PARA). Implementation of the *Global Pulse Architecture Blueprint v1.0*.

---

## Arquitectura / Architecture

| Capa | Implementación | Dónde |
|------|----------------|-------|
| **Capa 1 — Pulso Visual** | PWA React (mapa D3 + grafo de fuerzas, ES/EN, TTS, offline) | `app/` |
| **Capa 2 — Síntesis Contextual** | Motor híbrido: LLM (Anthropic) con *prompt maestro* + heurístico de respaldo | `pipeline/gp/synthesize.py` |
| **Capa 3 — Validación y Fuente** | Evidencia por hash de contenido + regla de oro de trazabilidad | `pipeline/gp/validate.py`, `data/evidence/` |
| **Ingesta (transversal)** | RSS (BBC, DW, El País, Guardian, France24) + GDELT 2.0, sin claves | `pipeline/gp/collect.py` |
| **Orquestación (sin n8n)** | Orquestador propio con reintentos, fallo aislado y métricas, dirigido por Claude Code / cron / GitHub Actions | `pipeline/orchestrator.py`, `.github/workflows/global-pulse-daily.yml` |
| **Segundo cerebro** | Notas atómicas Markdown con frontmatter PARA | `data/vault/` |

## Ciclo diario (8 etapas) / Daily cycle

```
Recolección → Normalización → Deduplicación → Clustering (translingüe)
→ Síntesis (Capa 2) → Validación (Capa 3) → Publicación → Promoción a Obsidian
```

```bash
cd pipeline

# Demo sin red (fixture con eventos documentados) / offline demo
python orchestrator.py run --mode fixture --synth heuristic

# Ingesta real / live ingestion  (opcional: export ANTHROPIC_API_KEY=...)
python orchestrator.py run --mode live --synth auto

# Tests
python -m tests.test_pipeline
```

El ciclo publica `data/pulse-YYYYMMDD.json`, actualiza `pulse-latest.json`,
copia el pulso a la PWA y promueve los insights verificados de impacto ≥ 60
como notas Obsidian en `data/vault/` (método PARA).

### Motor de síntesis híbrido / Hybrid synthesis engine
- `--synth auto` — usa la API de Anthropic si `ANTHROPIC_API_KEY` está definida;
  si no, cae al heurístico. / Uses the Anthropic API when `ANTHROPIC_API_KEY`
  is set; falls back to the heuristic engine otherwise.
- **Regla de oro:** ningún nodo es `verificado` sin al menos una pieza de
  evidencia en la Capa 3; sin evidencia → `sin_verificar` e `impacto: null`.

## Aplicación (PWA) / App

```bash
cd app
npm install
npm run dev        # desarrollo
npm run build      # producción -> dist/ (desplegable en cualquier estático/CDN)
```

- **Multilenguaje:** español neutro / inglés (detección automática + conmutador).
- **Multidispositivo:** PWA instalable; el service worker sirve el último pulso
  válido sin conexión (network-first para datos, cache-first para el shell).
- **Multimodal:** texto, mapa geoespacial, grafo de relaciones, imágenes de las
  fuentes originales y lectura por voz (Web Speech API, ES/EN).

## Modelo de datos / Data model

Nodo de impacto (schema 1.1): `id`, `titulo{es,en}`, `sintesis{es,en}`,
`categoria`, `actores[]`, `geo{lat,lon,region}`, `impacto (0-100|null)`,
`relaciones[]`, `fuentes[] (ids de evidencia)`, `imagenes[]`,
`estado (verificado|sin_verificar)`, `fecha`, `referencias[]`.

## Automatización / Automation

`.github/workflows/global-pulse-daily.yml` ejecuta el ciclo cada día a las
05:00 UTC (o manualmente con `workflow_dispatch`), corre los tests y publica
el pulso por commit. Configura el secreto `ANTHROPIC_API_KEY` en el repositorio
para activar la síntesis LLM; sin él, el heurístico mantiene el pulso vivo.

> El pulso incluido en el repositorio se generó en **modo fixture** (demo sin
> red, eventos basados en cobertura pública documentada de 2025). Ejecuta el
> modo `live` para ingesta en tiempo real.
