import os
import uuid
from datetime import datetime, timezone
from typing import Optional, List, Literal
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field

from src.agent.graph import get_triage_graph
from src.agent.state import AgentState, IncidentData
from src.db.mongo import close_mongo_connection, init_indexes

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
    processed_at: str

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_indexes()
    yield
    await close_mongo_connection()

app = FastAPI(
    title="Huawei Cloud MaaS - Autonomous Triage & Active Defense",
    version="3.0.0",
    lifespan=lifespan
)

@app.get("/", status_code=status.HTTP_200_OK)
async def root():
    return {
        "service": "Huawei Cloud MaaS - Autonomous Triage Agent API",
        "version": "3.0.0",
        "status": "UP",
        "endpoints": {
            "swagger_docs": "/docs",
            "health_check": "/health",
            "webhook_n8n": "/webhook/n8n",
            "ui_dashboard": "http://localhost:8501"
        }
    }

@app.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    return {"status": "UP", "timestamp": datetime.now(timezone.utc).isoformat()}

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
        try:
            parsed_time = datetime.fromisoformat(payload.timestamp.replace("Z", "+00:00"))
        except ValueError:
            parsed_time = datetime.now(timezone.utc)

        initial_state: AgentState = {
            "incident": IncidentData(
                incident_id=payload.incident_id,
                description=payload.raw_log,
                component=payload.component,
                severity=payload.severity_hint or "P2",
                source=payload.source,
                is_security_event=payload.is_security_event,
                timestamp=parsed_time,
            ),
            "messages": [],
            "diagnostic_steps": [],
        }

        graph = get_triage_graph()
        final_state = await graph.ainvoke(initial_state)

        return TriageResponse(
            incident_id=payload.incident_id,
            risk_score=final_state.get("risk_score", 5.0),
            severity=final_state.get("incident", {}).get("severity", payload.severity_hint or "P2"),
            checklist=final_state.get("diagnostics_checklist", []),
            root_cause_hypothesis=final_state.get("root_cause_hypothesis", "Unknown issue"),
            escalation_team=final_state.get("escalation_path"),
            mitigation_commands=final_state.get("final_recommendation"),
            processed_at=datetime.now(timezone.utc).isoformat(),
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Agent graph execution failed: {str(exc)}"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
