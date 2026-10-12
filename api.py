"""HTTP interface for the existing LangGraph project planner."""

import io
import json
import re
from collections.abc import Iterator
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from fastapi.responses import Response, StreamingResponse
from pydantic import BaseModel


from app.config.settings import settings
from app.graph.state import initial_state
from app.graph.workflow import stream_pipeline
from app.services.agent_trace import build_agent_trace_step
from app.services.pdf_generator import generate_pdf_from_dict
from app.utils.validators import ValidationError, validate_user_idea


api = FastAPI(title="Planorai API", version="1.0.0")


class BuildRequest(BaseModel):
    idea: str


@api.get("/health")
def health() -> dict:
    return {
        "ok": True,
        "model": settings.llm_model,
        "configured": bool(settings.google_api_key),
        "langsmith_tracing": settings.langsmith_enabled,
    }


def events(idea: str) -> Iterator[str]:
    def emit(payload: dict) -> str:
        return json.dumps(payload, ensure_ascii=False) + "\n"

    trace_id = uuid4()
    trace_state = initial_state(idea)
    sequence = 0
    yield emit({
        "type": "started",
        "trace": {
            "id": str(trace_id),
            "project": settings.langsmith_project,
            "enabled": settings.langsmith_enabled,
        },
    })
    try:
        for node, update in stream_pipeline(idea, run_id=trace_id):
            if node.startswith("__"):
                continue
            sequence += 1
            trace_step, trace_state = build_agent_trace_step(
                node,
                trace_state,
                update,
                sequence,
            )
            yield emit({
                "type": "step",
                "node": node,
                "revision_count": update.get("revision_count"),
                "critic_status": update.get("critic_feedback", {}).get("status"),
                "next_agent": update.get("current_agent"),
                "trace_step": trace_step,
            })
            if node == "report":
                report = update.get("final_report")
                if not report:
                    raise RuntimeError("The report agent returned no report.")
                yield emit({"type": "complete", "report": report})
                return
        raise RuntimeError("The pipeline ended before a report was generated.")
    except Exception as exc:
        yield emit({"type": "error", "message": str(exc)})


@api.post("/build")
def build(request: BuildRequest) -> StreamingResponse:
    if not settings.google_api_key:
        raise HTTPException(status_code=503, detail="GOOGLE_API_KEY is not configured.")
    try:
        idea = validate_user_idea(request.idea)
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return StreamingResponse(
        events(idea),
        media_type="application/x-ndjson",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@api.post("/export/pdf")
def export_pdf(report: dict) -> Response:
    try:
        buffer = io.BytesIO()
        generate_pdf_from_dict(report, buffer)
        pdf_bytes = buffer.getvalue()
        title = str(report.get("project_title") or "project-plan")
        filename = re.sub(r"[^a-zA-Z0-9_-]+", "-", title.lower()).strip("-") or "project-plan"
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}.pdf"',
                "Access-Control-Expose-Headers": "Content-Disposition",
            },
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to generate PDF: {exc}")

