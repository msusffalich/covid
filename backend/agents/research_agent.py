"""
Research Agent
==============

Orchestrates a LangChain agent that:
  1. Searches the web for real, cited information (Tavily → DuckDuckGo fallback)
  2. Synthesises findings, refusing to include unverified claims
  3. Structures the data into sections ready for any output format
  4. Yields SSE-compatible progress dicts as it works
  5. Writes results into the session store

System-prompt engineering principles applied
--------------------------------------------
- Grounding mandate  : model MUST cite sources; forbidden to invent data
- Format independence: output is a structured JSON blob, not final prose,
                       so any generator (PDF/PPTX/Excel/Image) can consume it
- Bilingual          : language variable drives both the internal reasoning
                       language and all output text
- Retry/resilience   : tenacity wraps LLM calls; fallback search on Tavily fail
"""

import json
import os
from typing import AsyncGenerator

from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.output_parsers import JsonOutputParser
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from utils.session_store import update_session

load_dotenv()

# ---------------------------------------------------------------------------
# LLM setup
# ---------------------------------------------------------------------------

_llm = ChatAnthropic(
    model="claude-sonnet-4-6",
    anthropic_api_key=os.getenv("ANTHROPIC_API_KEY", ""),
    max_tokens=8192,
    temperature=0.2,       # low temp → factual, deterministic output
)

# ---------------------------------------------------------------------------
# Master System Prompt (the "brain")
# ---------------------------------------------------------------------------

_SYSTEM_PROMPT_ES = """
<rol>
Eres un Investigador Científico Senior y Analista de Datos con acceso a búsqueda web en tiempo real.
Tu deber supremo es la veracidad: JAMÁS inventes datos, estadísticas, nombres o fechas.
Si una fuente no confirma un dato, escribe explícitamente "Dato no confirmado por las fuentes disponibles."
</rol>

<mandato_de_fuentes>
- Utiliza EXCLUSIVAMENTE la información recuperada de las herramientas de búsqueda web.
- Cada hecho relevante debe ir acompañado de su cita en formato APA 7.ª ed. Y IEEE.
- Formato APA: Autor(es). (Año). Título. Fuente/Editorial. URL
- Formato IEEE: [N] Autor(es), "Título", *Fuente*, vol., pp., año. [En línea]. Disponible: URL
- Si una URL no está disponible, indica: "Fuente: [nombre del sitio/publicación]"
</mandato_de_fuentes>

<instrucciones_de_salida>
Tu respuesta FINAL debe ser un JSON válido con esta estructura exacta (sin bloques de código markdown):

{
  "topic": "<el tema investigado>",
  "language": "es",
  "executive_summary": "<resumen ejecutivo de 3-5 oraciones, en español>",
  "key_findings": [
    {"finding": "<hallazgo 1>", "citation_apa": "...", "citation_ieee": "...", "url": "..."},
    ...
  ],
  "sections": [
    {
      "title": "<título de sección>",
      "content": "<párrafo detallado, mínimo 150 palabras>",
      "bullet_points": ["<punto 1>", "<punto 2>", "..."],
      "citations": ["<cita APA 1>", "<cita APA 2>"]
    }
  ],
  "data_tables": [
    {
      "title": "<título de tabla>",
      "headers": ["Col1", "Col2", "Col3"],
      "rows": [["val1", "val2", "val3"], ...]
    }
  ],
  "sources": [
    {
      "title": "<título del artículo/página>",
      "url": "<url>",
      "snippet": "<extracto relevante>",
      "citation_apa": "<cita APA completa>",
      "citation_ieee": "<cita IEEE completa>"
    }
  ],
  "credibility_note": "<nota sobre la fiabilidad y limitaciones de las fuentes encontradas>"
}

Recuerda: El JSON debe ser parseado por máquina. No incluyas texto fuera del JSON.
</instrucciones_de_salida>
"""

_SYSTEM_PROMPT_EN = """
<role>
You are a Senior Scientific Researcher and Data Analyst with real-time web search access.
Your supreme duty is truthfulness: NEVER invent data, statistics, names, or dates.
If a source does not confirm a fact, explicitly write "Data not confirmed by available sources."
</role>

<source_mandate>
- Use EXCLUSIVELY information retrieved from web search tools.
- Every relevant fact must be accompanied by its citation in APA 7th ed. AND IEEE format.
- APA format: Author(s). (Year). Title. Source/Publisher. URL
- IEEE format: [N] Author(s), "Title", *Source*, vol., pp., year. [Online]. Available: URL
- If a URL is unavailable, indicate: "Source: [site/publication name]"
</source_mandate>

<output_instructions>
Your FINAL response must be a valid JSON with this exact structure (no markdown code blocks):

{
  "topic": "<the researched topic>",
  "language": "en",
  "executive_summary": "<executive summary in 3-5 sentences, in English>",
  "key_findings": [
    {"finding": "<finding 1>", "citation_apa": "...", "citation_ieee": "...", "url": "..."},
    ...
  ],
  "sections": [
    {
      "title": "<section title>",
      "content": "<detailed paragraph, minimum 150 words>",
      "bullet_points": ["<point 1>", "<point 2>", "..."],
      "citations": ["<APA citation 1>", "<APA citation 2>"]
    }
  ],
  "data_tables": [
    {
      "title": "<table title>",
      "headers": ["Col1", "Col2", "Col3"],
      "rows": [["val1", "val2", "val3"], ...]
    }
  ],
  "sources": [
    {
      "title": "<article/page title>",
      "url": "<url>",
      "snippet": "<relevant excerpt>",
      "citation_apa": "<full APA citation>",
      "citation_ieee": "<full IEEE citation>"
    }
  ],
  "credibility_note": "<note on reliability and limitations of found sources>"
}

Remember: The JSON must be machine-parseable. Include no text outside the JSON.
</output_instructions>
"""


# ---------------------------------------------------------------------------
# Web search helpers
# ---------------------------------------------------------------------------


def _tavily_search(query: str, max_results: int) -> list[dict]:
    """Search via Tavily API. Returns list of {title, url, content} dicts."""
    try:
        from tavily import TavilyClient  # type: ignore
        client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY", ""))
        result = client.search(query=query, max_results=max_results, include_raw_content=False)
        return result.get("results", [])
    except Exception:  # noqa: BLE001
        return []


def _ddg_search(query: str, max_results: int) -> list[dict]:
    """DuckDuckGo fallback search."""
    try:
        from duckduckgo_search import DDGS
        ddgs = DDGS()
        results = list(ddgs.text(query, max_results=max_results))
        # normalise to same shape as Tavily
        return [
            {"title": r.get("title", ""), "url": r.get("href", ""), "content": r.get("body", "")}
            for r in results
        ]
    except Exception:  # noqa: BLE001
        return []


def _web_search(query: str, max_results: int = 8) -> list[dict]:
    """Try Tavily first; fall back to DuckDuckGo."""
    results = _tavily_search(query, max_results)
    if not results:
        results = _ddg_search(query, max_results)
    return results


# ---------------------------------------------------------------------------
# Retry-wrapped LLM call
# ---------------------------------------------------------------------------


@retry(
    retry=retry_if_exception_type(Exception),
    wait=wait_exponential(multiplier=1, min=2, max=30),
    stop=stop_after_attempt(3),
    reraise=True,
)
def _call_llm(messages: list) -> str:
    response = _llm.invoke(messages)
    return str(response.content)


# ---------------------------------------------------------------------------
# Public async generator consumed by main.py
# ---------------------------------------------------------------------------


async def run_research(
    session_id: str,
    topic: str,
    language: str,
) -> AsyncGenerator[dict, None]:
    """
    Async generator that drives the full research pipeline.
    Yields dicts: {"event": str, "data": dict}
    Writes final structured_data + sources + summary to session store.
    """
    max_results = int(os.getenv("MAX_SEARCH_RESULTS", 8))
    system_prompt = _SYSTEM_PROMPT_ES if language == "es" else _SYSTEM_PROMPT_EN

    # ---- Step 1: multi-query search ----------------------------------------
    step_label = "Buscando fuentes primarias…" if language == "es" else "Searching primary sources…"
    yield {"event": "progress", "data": {"step": 1, "total": 4, "detail": step_label}}

    # Generate 3 search queries from the topic to improve coverage
    queries = [topic, f"{topic} statistics data", f"{topic} research latest findings"]

    raw_results: list[dict] = []
    for q in queries:
        raw_results.extend(_web_search(q, max_results=max_results // 3 + 1))

    # Deduplicate by URL
    seen_urls: set[str] = set()
    deduped: list[dict] = []
    for r in raw_results:
        url = r.get("url", "")
        if url not in seen_urls:
            seen_urls.add(url)
            deduped.append(r)

    # ---- Step 2: format context for LLM ------------------------------------
    step_label = "Analizando fuentes…" if language == "es" else "Analysing sources…"
    yield {"event": "progress", "data": {"step": 2, "total": 4, "detail": step_label}}

    context_blocks: list[str] = []
    for i, r in enumerate(deduped[:max_results], 1):
        block = (
            f"[Fuente {i}]\n"
            f"Título: {r.get('title', 'Sin título')}\n"
            f"URL: {r.get('url', 'URL no disponible')}\n"
            f"Extracto: {r.get('content', r.get('snippet', ''))[:600]}\n"
        )
        context_blocks.append(block)

    context_str = "\n---\n".join(context_blocks)

    if language == "es":
        user_msg = (
            f"Tema de investigación: {topic}\n\n"
            f"Fuentes recuperadas de la búsqueda web:\n{context_str}\n\n"
            "Sintetiza toda la información anterior y devuelve ÚNICAMENTE el JSON estructurado."
        )
    else:
        user_msg = (
            f"Research topic: {topic}\n\n"
            f"Sources retrieved from web search:\n{context_str}\n\n"
            "Synthesise all the above information and return ONLY the structured JSON."
        )

    # ---- Step 3: LLM synthesis ---------------------------------------------
    step_label = "Sintetizando con IA…" if language == "es" else "Synthesising with AI…"
    yield {"event": "progress", "data": {"step": 3, "total": 4, "detail": step_label}}

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_msg),
    ]

    raw_output = _call_llm(messages)

    # ---- Step 4: parse + store ---------------------------------------------
    step_label = "Guardando hallazgos…" if language == "es" else "Saving findings…"
    yield {"event": "progress", "data": {"step": 4, "total": 4, "detail": step_label}}

    # Strip markdown code fences if the model added them despite instructions
    clean = raw_output.strip()
    if clean.startswith("```"):
        clean = clean.split("```", 2)[1]
        if clean.startswith("json"):
            clean = clean[4:]
        clean = clean.rsplit("```", 1)[0].strip()

    try:
        structured: dict = json.loads(clean)
    except json.JSONDecodeError:
        # Last-resort: extract JSON object between first { and last }
        start = clean.find("{")
        end = clean.rfind("}") + 1
        structured = json.loads(clean[start:end])

    summary = structured.get("executive_summary", "")
    sources = structured.get("sources", [])

    await update_session(
        session_id,
        summary=summary,
        sources=sources,
        structured_data=structured,
    )
