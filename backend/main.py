import os
import json
import uuid
from datetime import datetime, timezone
from typing import Optional, List, Literal
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field
from sse_starlette.sse import EventSourceResponse

from src.agent.graph import get_triage_graph
from src.agent.state import AgentState, IncidentData, initial_state
from src.db.mongo import close_mongo_connection, init_indexes
from src.tracing.cost import cost_snapshot, reset_cost

class IncidentWebhookPayload(BaseModel):
    incident_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    source: Literal["nextjs", "mongodb", "n8n", "security-scanner"]
    timestamp: str
    component: Literal["frontend", "database", "network", "auth"]
    raw_log: str
    is_security_event: bool = False
    severity_hint: Optional[Literal["P1", "P2", "P3"]] = None

class TriageResponse(BaseModel):
    incident_id: str
    risk_score: float
    severity: str
    checklist: List[str]
    root_cause_hypothesis: str
    escalation_team: Optional[str] = None
    mitigation_commands: Optional[str] = None
    diagnostic_steps: Optional[List[dict]] = None
    processed_at: str
    route: Optional[List[str]] = None
    cost_usd: Optional[float] = None
    pending_approval: Optional[dict] = None

class ApproveRequest(BaseModel):
    thread_id: str
    approved: bool = True
    reason: str = ""

class StreamRequest(BaseModel):
    message: str
    incident: Optional[dict] = None
    thread_id: Optional[str] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_indexes()
    yield
    await close_mongo_connection()

app = FastAPI(
    title="Huawei Cloud MaaS - Autonomous Triage & Active Defense (Multi-Agent)",
    version="4.0.0",
    lifespan=lifespan
)

@app.get("/", status_code=status.HTTP_200_OK)
async def root():
    return {
        "service": "Huawei Cloud MaaS - Multi-Agent Incident Response API",
        "version": "4.0.0",
        "status": "UP",
        "endpoints": {
            "swagger_docs": "/docs",
            "health_check": "/health",
            "webhook_n8n": "/webhook/n8n",
            "stream": "/stream",
            "approve": "/approve",
            "ui_dashboard": "http://localhost:8501"
        }
    }

@app.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    return {"status": "UP", "timestamp": datetime.now(timezone.utc).isoformat()}

def _build_incident_state(payload: IncidentWebhookPayload) -> dict:
    try:
        parsed_time = datetime.fromisoformat(payload.timestamp.replace("Z", "+00:00"))
    except ValueError:
        parsed_time = datetime.now(timezone.utc)

    incident_data = IncidentData(
        incident_id=payload.incident_id,
        description=payload.raw_log,
        component=payload.component,
        severity=payload.severity_hint or "P2",
        source=payload.source,
        is_security_event=payload.is_security_event,
        timestamp=parsed_time,
    )

    from langchain_core.messages import HumanMessage
    state = initial_state(incident_data=incident_data, user_message=payload.raw_log)
    state["incident_id"] = payload.incident_id
    state["severity"] = payload.severity_hint or "P2"
    state["affected_services"] = [payload.component]
    return state

def _extract_result(final_state: dict, payload_incident_id: str) -> TriageResponse:
    messages = final_state.get("messages", [])
    route = [getattr(m, "name", None) for m in messages if getattr(m, "name", None)]
    scratchpad = final_state.get("scratchpad", {})

    root_cause = scratchpad.get("investigator", final_state.get("root_cause_hypothesis", "Unknown"))
    remediation = scratchpad.get("remediator", final_state.get("final_recommendation", ""))
    checklist = final_state.get("diagnostics_checklist", [])
    if not checklist and "communicator" in scratchpad:
        checklist = [scratchpad["communicator"][:200]]

    return TriageResponse(
        incident_id=payload_incident_id,
        risk_score=final_state.get("risk_score", 0.0),
        severity=final_state.get("severity", final_state.get("incident", {}).get("severity", "P2")),
        checklist=checklist,
        root_cause_hypothesis=root_cause or "Under investigation",
        escalation_team=final_state.get("escalation_path"),
        mitigation_commands=remediation or "",
        diagnostic_steps=final_state.get("diagnostic_steps", []),
        processed_at=datetime.now(timezone.utc).isoformat(),
        route=route,
        cost_usd=cost_snapshot()["usd"],
        pending_approval=final_state.get("pending_approval"),
    )

@app.post("/", response_model=TriageResponse, status_code=status.HTTP_200_OK, include_in_schema=False)
@app.post("/triage", response_model=TriageResponse, status_code=status.HTTP_200_OK, include_in_schema=False)
@app.post(
    "/webhook/n8n",
    response_model=TriageResponse,
    status_code=status.HTTP_200_OK,
    responses={
        200: {"description": "Triage procesado exitosamente"},
        422: {"description": "Payload no cumple el contrato de datos"},
        500: {"description": "Error interno durante la ejecución del grafo"},
    }
)
async def handle_n8n_webhook(payload: IncidentWebhookPayload):
    try:
        reset_cost()
        thread_id = payload.incident_id
        config = {"configurable": {"thread_id": thread_id}, "recursion_limit": 40}

        state = _build_incident_state(payload)
        graph = get_triage_graph()
        final_state = await graph.ainvoke(state, config=config)

        return _extract_result(final_state, payload.incident_id)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Agent graph execution failed: {str(exc)}"
        )

@app.post("/stream")
async def stream(req: StreamRequest):
    """Server-Sent Events: one event per node as the graph runs."""
    reset_cost()
    thread_id = req.thread_id or str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}, "recursion_limit": 40}

    incident_data = req.incident or {}
    state = initial_state(incident_data=incident_data, user_message=req.message)

    async def event_gen():
        final = ""
        graph = get_triage_graph()
        async for chunk in graph.astream(state, config=config, stream_mode="updates"):
            for node, update in chunk.items():
                if isinstance(update, dict):
                    msgs = update.get("messages", [])
                else:
                    msgs = []
                text = ""
                if msgs:
                    last = msgs[-1]
                    text = getattr(last, "content", str(last)) if last else ""
                if text:
                    final = text
                yield {
                    "event": "node",
                    "data": json.dumps({
                        "node": node,
                        "text": text,
                        "cost_usd": cost_snapshot()["usd"],
                    }, default=str),
                }
        yield {
            "event": "done",
            "data": json.dumps({
                "answer": final,
                "cost_usd": cost_snapshot()["usd"],
                "thread_id": thread_id,
            }, default=str),
        }

    return EventSourceResponse(event_gen())

@app.post("/approve")
async def approve_action(req: ApproveRequest):
    """Approve or reject a pending gated action. Resumes the graph."""
    graph = get_triage_graph()
    config = {"configurable": {"thread_id": req.thread_id}, "recursion_limit": 40}

    if req.approved:
        update = {
            "pending_approval": None,
            "status": "mitigating",
            "actions_taken": [{"action": "approved", "reason": req.reason, "timestamp": datetime.now(timezone.utc).isoformat()}],
        }
    else:
        update = {
            "pending_approval": None,
            "status": "investigating",
            "actions_taken": [{"action": "rejected", "reason": req.reason, "timestamp": datetime.now(timezone.utc).isoformat()}],
        }

    try:
        await graph.aupdate_state(config, update)
        result = await graph.ainvoke(None, config=config)
        return {"status": "approved" if req.approved else "rejected", "thread_id": req.thread_id}
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to resume graph: {str(exc)}"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
