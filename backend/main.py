"""
Investigador Inteligente Multimodal — FastAPI Backend
=====================================================

Endpoints
---------
POST /api/session/start          → create session, return session_id
GET  /api/research/stream/{id}   → SSE stream: run research phase
POST /api/generate/{id}          → start async file generation
GET  /api/generate/stream/{id}   → SSE stream: track generation progress
GET  /api/download/{id}          → download the generated file
DELETE /api/session/{id}         → cleanup

State machine per session
-------------------------
idle → researching → awaiting_format → generating → done
                                              ↓
                                           error (at any step)
"""

import asyncio
import json
import os
import tempfile
from pathlib import Path
from typing import AsyncGenerator

import uvicorn
from dotenv import load_dotenv
from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from sse_starlette.sse import EventSourceResponse

load_dotenv()

from agents.research_agent import run_research          # noqa: E402
from generators.pdf_generator import build_pdf          # noqa: E402
from generators.pptx_generator import build_pptx        # noqa: E402
from generators.excel_generator import build_excel      # noqa: E402
from generators.image_generator import build_infographic  # noqa: E402
from utils.session_store import (                        # noqa: E402
    create_session,
    delete_session,
    get_session,
    update_session,
)

# ---------------------------------------------------------------------------
# App + CORS
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Investigador Inteligente Multimodal",
    version="1.0.0",
    description="Agentic research + multi-format document generation API",
)

_origins = os.getenv(
    "CORS_ORIGINS", "http://localhost:5173,http://localhost:4173"
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Temp directory for generated files
_TMP_DIR = Path(tempfile.gettempdir()) / "investigador_files"
_TMP_DIR.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------


class StartSessionRequest(BaseModel):
    language: str = Field(..., pattern="^(es|en)$", description="'es' or 'en'")
    topic: str = Field(..., min_length=3, max_length=500)


class StartSessionResponse(BaseModel):
    session_id: str


class GenerateRequest(BaseModel):
    output_format: str = Field(
        ...,
        pattern="^(pdf|pptx|excel|image)$",
        description="pdf | pptx | excel | image",
    )
    extra_instructions: str = Field(
        default="",
        max_length=1000,
        description="Optional extra user instructions for the file",
    )


# ---------------------------------------------------------------------------
# Helper: SSE event builder
# ---------------------------------------------------------------------------


def _sse_event(event: str, data: dict) -> dict:
    return {"event": event, "data": json.dumps(data, ensure_ascii=False)}


# ---------------------------------------------------------------------------
# 1. POST /api/session/start
# ---------------------------------------------------------------------------


@app.post("/api/session/start", response_model=StartSessionResponse)
async def start_session(body: StartSessionRequest) -> StartSessionResponse:
    """Create a new research session and return its ID."""
    session_id = await create_session(language=body.language, topic=body.topic)
    return StartSessionResponse(session_id=session_id)


# ---------------------------------------------------------------------------
# 2. GET /api/research/stream/{session_id}  — SSE
# ---------------------------------------------------------------------------


@app.get("/api/research/stream/{session_id}")
async def research_stream(session_id: str) -> EventSourceResponse:
    """
    SSE endpoint that drives the research phase.

    Emits events:
      status   → {message: str}
      progress → {step: int, total: int, detail: str}
      result   → {summary: str, sources: list}
      error    → {message: str}
    """
    session = await get_session(session_id)
    if session is None:
        raise HTTPException(404, "Session not found or expired")
    if session["status"] not in ("idle", "error"):
        raise HTTPException(409, f"Session is already in state: {session['status']}")

    async def generator() -> AsyncGenerator[dict, None]:
        try:
            await update_session(session_id, status="researching")

            yield _sse_event("status", {"message": "Iniciando investigación…" if session["language"] == "es" else "Starting research…"})

            # Delegate to the LangChain agent; it yields progress dicts
            async for progress in run_research(
                session_id=session_id,
                topic=session["topic"],
                language=session["language"],
            ):
                yield _sse_event(progress["event"], progress["data"])

            # After run_research completes the session store is updated
            updated = await get_session(session_id)
            yield _sse_event(
                "result",
                {
                    "summary": updated["summary"],
                    "sources": updated["sources"],
                },
            )
            await update_session(session_id, status="awaiting_format")
            yield _sse_event("status", {"message": "awaiting_format"})

        except Exception as exc:  # noqa: BLE001
            await update_session(session_id, status="error", error=str(exc))
            yield _sse_event("error", {"message": str(exc)})

    return EventSourceResponse(generator())


# ---------------------------------------------------------------------------
# 3. POST /api/generate/{session_id}
# ---------------------------------------------------------------------------


@app.post("/api/generate/{session_id}", status_code=202)
async def start_generation(
    session_id: str,
    body: GenerateRequest,
    background_tasks: BackgroundTasks,
) -> dict:
    """
    Accepts the user's chosen output format and starts async file generation.
    Returns immediately with 202; client polls /api/generate/stream/{id}.
    """
    session = await get_session(session_id)
    if session is None:
        raise HTTPException(404, "Session not found or expired")
    if session["status"] != "awaiting_format":
        raise HTTPException(409, f"Cannot generate from state: {session['status']}")

    await update_session(
        session_id,
        status="generating",
        output_format=body.output_format,
        extra_instructions=body.extra_instructions,
    )

    background_tasks.add_task(
        _run_generation,
        session_id,
        body.output_format,
        body.extra_instructions,
    )

    return {"detail": "Generation started", "session_id": session_id}


async def _run_generation(
    session_id: str,
    output_format: str,
    extra_instructions: str,
) -> None:
    """Background task: build file and persist path in session."""
    try:
        session = await get_session(session_id)
        lang = session["language"]
        topic = session["topic"]
        structured = session["structured_data"]
        sources = session["sources"]

        output_path: Path

        if output_format == "pdf":
            output_path = await asyncio.to_thread(
                build_pdf, topic, lang, structured, sources, extra_instructions, _TMP_DIR
            )
        elif output_format == "pptx":
            output_path = await asyncio.to_thread(
                build_pptx, topic, lang, structured, sources, extra_instructions, _TMP_DIR
            )
        elif output_format == "excel":
            output_path = await asyncio.to_thread(
                build_excel, topic, lang, structured, sources, extra_instructions, _TMP_DIR
            )
        elif output_format == "image":
            output_path = await asyncio.to_thread(
                build_infographic, topic, lang, structured, sources, extra_instructions, _TMP_DIR
            )
        else:
            raise ValueError(f"Unknown format: {output_format}")

        await update_session(session_id, status="done", output_path=str(output_path))

    except Exception as exc:  # noqa: BLE001
        await update_session(session_id, status="error", error=str(exc))


# ---------------------------------------------------------------------------
# 4. GET /api/generate/stream/{session_id}  — SSE polling
# ---------------------------------------------------------------------------


@app.get("/api/generate/stream/{session_id}")
async def generation_stream(session_id: str) -> EventSourceResponse:
    """
    Lightweight SSE that polls session state every second until done/error.
    Emits:
      status   → {state: str}
      done     → {download_url: str}
      error    → {message: str}
    """
    async def generator() -> AsyncGenerator[dict, None]:
        while True:
            session = await get_session(session_id)
            if session is None:
                yield _sse_event("error", {"message": "Session expired"})
                return

            state = session["status"]
            yield _sse_event("status", {"state": state})

            if state == "done":
                yield _sse_event("done", {"download_url": f"/api/download/{session_id}"})
                return
            if state == "error":
                yield _sse_event("error", {"message": session.get("error", "Unknown error")})
                return

            await asyncio.sleep(1)

    return EventSourceResponse(generator())


# ---------------------------------------------------------------------------
# 5. GET /api/download/{session_id}
# ---------------------------------------------------------------------------

_MIME_MAP = {
    "pdf": "application/pdf",
    "pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    "excel": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "image": "image/png",
}

_EXT_MAP = {"pdf": "pdf", "pptx": "pptx", "excel": "xlsx", "image": "png"}


@app.get("/api/download/{session_id}")
async def download_file(session_id: str) -> FileResponse:
    """Stream the generated file for download."""
    session = await get_session(session_id)
    if session is None:
        raise HTTPException(404, "Session not found or expired")
    if session["status"] != "done":
        raise HTTPException(409, "File not ready yet")

    path = Path(session["output_path"])
    if not path.exists():
        raise HTTPException(500, "Generated file missing on disk")

    fmt = session.get("output_format", "pdf")
    safe_topic = "".join(c if c.isalnum() else "_" for c in session["topic"])[:40]
    filename = f"{safe_topic}.{_EXT_MAP.get(fmt, 'bin')}"

    return FileResponse(
        path=str(path),
        media_type=_MIME_MAP.get(fmt, "application/octet-stream"),
        filename=filename,
    )


# ---------------------------------------------------------------------------
# 6. DELETE /api/session/{session_id}
# ---------------------------------------------------------------------------


@app.delete("/api/session/{session_id}", status_code=204)
async def cleanup_session(session_id: str) -> None:
    session = await get_session(session_id)
    if session and session.get("output_path"):
        try:
            Path(session["output_path"]).unlink(missing_ok=True)
        except OSError:
            pass
    await delete_session(session_id)


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=os.getenv("APP_HOST", "0.0.0.0"),
        port=int(os.getenv("APP_PORT", 8000)),
        reload=True,
    )
