import uuid
from datetime import datetime, timezone
from typing import Optional, List, Literal
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, status, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from src.logging_config import get_logger
from src.config import config
from src.agent.graph import get_triage_graph
from src.agent.state import AgentState, IncidentData
from src.llm_client import get_llm_client

logger = get_logger(__name__)

limiter = Limiter(key_func=get_remote_address, default_limits=[f"{config.RATE_LIMIT_PER_MINUTE}/minute"])


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
    guardrail_approved: bool = True
    guardrail_reason: Optional[str] = None
    processed_at: str


class CopilotChatRequest(BaseModel):
    message: str
    incident_context: Optional[dict] = None


class CopilotChatResponse(BaseModel):
    reply: str


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("app.starting", version="4.0.0")
    yield
    logger.info("app.stopping")


app = FastAPI(
    title="Huawei Cloud MaaS - Autonomous Triage & Active Defense",
    version="4.0.0",
    lifespan=lifespan
)

app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


def verify_webhook_auth(request: Request):
    """Verifica la autenticacion del webhook via API key header o Supabase JWT."""
    if not config.WEBHOOK_API_KEY:
        return

    auth_header = request.headers.get("Authorization", "")
    api_key_header = request.headers.get("X-Webhook-Key", "")

    if api_key_header == config.WEBHOOK_API_KEY:
        return

    if auth_header.startswith("Bearer ") and auth_header[7:] == config.WEBHOOK_API_KEY:
        return

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or missing webhook authentication"
    )


@app.get("/", status_code=status.HTTP_200_OK)
async def root():
    return {
        "service": "Huawei Cloud MaaS - Autonomous Triage Agent API",
        "version": "4.0.0",
        "status": "UP",
        "endpoints": {
            "swagger_docs": "/docs",
            "health_check": "/health",
            "webhook": "/webhook/n8n",
            "copilot_chat": "/copilot/chat",
            "copilot_stream": "/copilot/stream",
            "ui_dashboard": "http://localhost:8501"
        }
    }


@app.get("/health", status_code=status.HTTP_200_OK)
@limiter.limit("60/minute")
async def health_check(request: Request):
    return {"status": "UP", "timestamp": datetime.now(timezone.utc).isoformat()}


@app.post("/", response_model=TriageResponse, status_code=status.HTTP_200_OK, include_in_schema=False)
@app.post("/triage", response_model=TriageResponse, status_code=status.HTTP_200_OK, include_in_schema=False)
@app.post(
    "/webhook/n8n",
    response_model=TriageResponse,
    status_code=status.HTTP_200_OK,
    responses={
        200: {"description": "Triage procesado exitosamente"},
        401: {"description": "Autenticacion invalida"},
        422: {"description": "Payload no cumple el contrato de datos"},
        429: {"description": "Rate limit excedido"},
        500: {"description": "Error interno durante la ejecucion del grafo"},
    }
)
@limiter.limit(f"{config.RATE_LIMIT_PER_MINUTE}/minute")
async def handle_n8n_webhook(request: Request, payload: IncidentWebhookPayload):
    verify_webhook_auth(request)

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
            diagnostic_steps=final_state.get("diagnostic_steps", []),
            guardrail_approved=final_state.get("guardrail_approved", True),
            guardrail_reason=final_state.get("guardrail_reason"),
            processed_at=datetime.now(timezone.utc).isoformat(),
        )
    except Exception as exc:
        logger.error("webhook.failed", error=str(exc), incident_id=payload.incident_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Agent graph execution failed. Check logs for details."
        )


@app.post("/copilot/chat", response_model=CopilotChatResponse, status_code=status.HTTP_200_OK)
@limiter.limit("20/minute")
async def copilot_chat(request: Request, chat_req: CopilotChatRequest):
    """Endpoint para el copilot chat con el LLM real (Pangu 40B / OpenAI)."""
    client = get_llm_client()

    system_prompt = """You are the Huawei Cloud MaaS SRE Copilot.
You have full context on the current infrastructure and security state.
Answer concisely and professionally. If asked about incidents, provide actionable remediation advice."""

    messages = [
        {"role": "system", "content": system_prompt},
    ]

    if chat_req.incident_context:
        messages.append({
            "role": "system",
            "content": f"Current incident context: {chat_req.incident_context}"
        })

    messages.append({"role": "user", "content": chat_req.message})

    try:
        reply = await client.call(messages, temperature=0.3, max_tokens=800)
        logger.info("copilot.chat_success")
        return CopilotChatResponse(reply=reply)
    except Exception as e:
        logger.error("copilot.chat_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="LLM service unavailable. Check API keys configuration."
        )


@app.post("/copilot/stream", status_code=status.HTTP_200_OK)
@limiter.limit("20/minute")
async def copilot_stream(request: Request, chat_req: CopilotChatRequest):
    """Endpoint de streaming para el copilot chat."""
    client = get_llm_client()

    system_prompt = """You are the Huawei Cloud MaaS SRE Copilot.
You have full context on the current infrastructure and security state.
Answer concisely and professionally."""

    messages = [
        {"role": "system", "content": system_prompt},
    ]

    if chat_req.incident_context:
        messages.append({
            "role": "system",
            "content": f"Current incident context: {chat_req.incident_context}"
        })

    messages.append({"role": "user", "content": chat_req.message})

    async def stream_generator():
        try:
            async for chunk in client.stream(messages, temperature=0.3, max_tokens=800):
                yield f"data: {chunk}\n\n"
            yield "data: [DONE]\n\n"
        except Exception as e:
            logger.error("copilot.stream_failed", error=str(e))
            yield f"data: Error: LLM service unavailable.\n\n"

    return StreamingResponse(stream_generator(), media_type="text/event-stream")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
