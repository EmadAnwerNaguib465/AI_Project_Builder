"""HTTP interface for the existing LangGraph project planner."""

import json
from collections.abc import Iterator

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.config.settings import settings
from app.graph.workflow import stream_pipeline
from app.utils.validators import ValidationError, validate_user_idea

api = FastAPI(title="AI Project Builder API", version="1.0.0")


class BuildRequest(BaseModel):
    idea: str


@api.get("/health")
def health() -> dict:
    return {"ok": True, "model": settings.llm_model, "configured": bool(settings.google_api_key)}


def events(idea: str) -> Iterator[str]:
    def emit(payload: dict) -> str:
        return json.dumps(payload, ensure_ascii=False) + "\n"

    yield emit({"type": "started"})
    try:
        for node, update in stream_pipeline(idea):
            if node.startswith("__"):
                continue
            yield emit({
                "type": "step",
                "node": node,
                "revision_count": update.get("revision_count"),
                "critic_status": update.get("critic_feedback", {}).get("status"),
                "next_agent": update.get("current_agent"),
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
