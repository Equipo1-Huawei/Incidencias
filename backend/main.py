import json
import uuid
from datetime import datetime, timezone
from typing import Optional, List, Literal
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from sse_starlette.sse import EventSourceResponse
from langchain_core.messages import HumanMessage

from src.logging_config import get_logger
from src.config import config
from src.agent.graph import get_triage_graph
from src.agent.state import initial_state
from src.memory import get_checkpointer
from src.tracing.cost import cost_snapshot, reset_cost

logger = get_logger(__name__)

limiter = Limiter(key_func=get_remote_address, default_limits=[f"{config.RATE_LIMIT_PER_MINUTE}/minute"])


class IncidentWebhookPayload(BaseModel):
    incident_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    source: Literal["nextjs", "mongodb", "security-scanner"]
    timestamp: str
    component: Literal["frontend", "database", "network", "auth"]
    raw_log: str
    is_security_event: bool = False
    severity_hint: Optional[Literal["P1", "P2", "P3"]] = None


class TriageResponse(BaseModel):
    incident_id: str
    answer: str
    route: List[str]
    cost_usd: float
    thread_id: str
    processed_at: str


class CopilotChatRequest(BaseModel):
    message: str
    incident_context: Optional[dict] = None


class CopilotChatResponse(BaseModel):
    reply: str


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("app.starting", version="5.0.0")
    yield
    logger.info("app.stopping")


app = FastAPI(
    title="Huawei Cloud MaaS - Autonomous Triage & Active Defense",
    version="5.0.0",
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
    if not config.WEBHOOK_API_KEY:
        return
    auth_header = request.headers.get("Authorization", "")
    api_key_header = request.headers.get("X-Webhook-Key", "")
    if api_key_header == config.WEBHOOK_API_KEY:
        return
    if auth_header.startswith("Bearer ") and auth_header[7:] == config.WEBHOOK_API_KEY:
        return
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or missing webhook authentication")


def _final_answer(result: dict) -> str:
    msgs = result.get("messages", [])
    return msgs[-1].content if msgs else ""


@app.get("/", status_code=status.HTTP_200_OK)
async def root():
    return {
        "service": "Huawei Cloud MaaS - Autonomous Triage Agent API",
        "version": "5.0.0",
        "status": "UP",
        "endpoints": {
            "swagger_docs": "/docs",
            "health_check": "/health",
            "webhook": "/webhook/n8n",
            "stream": "/stream",
            "copilot_chat": "/copilot/chat",
            "copilot_stream": "/copilot/stream",
            "ui_dashboard": "http://localhost:8501"
        }
    }


@app.get("/health", status_code=status.HTTP_200_OK)
@limiter.limit("60/minute")
async def health_check(request: Request):
    return {"status": "UP", "timestamp": datetime.now(timezone.utc).isoformat()}


@app.post("/triage", response_model=TriageResponse, status_code=status.HTTP_200_OK)
@app.post("/webhook/n8n", response_model=TriageResponse, status_code=status.HTTP_200_OK, include_in_schema=False)
@limiter.limit(f"{config.RATE_LIMIT_PER_MINUTE}/minute")
async def handle_triage(request: Request, payload: IncidentWebhookPayload):
    verify_webhook_auth(request)

    try:
        reset_cost()
        thread_id = payload.incident_id
        config_graph = {"configurable": {"thread_id": thread_id}, "recursion_limit": 40}

        incident_text = (
            f"INCIDENT ALERT\n"
            f"Incident ID: {payload.incident_id}\n"
            f"Source: {payload.source}\n"
            f"Component: {payload.component}\n"
            f"Timestamp: {payload.timestamp}\n"
            f"Security Event: {payload.is_security_event}\n"
            f"Severity Hint: {payload.severity_hint or 'P2'}\n"
            f"Raw Log: {payload.raw_log}"
        )

        graph = get_triage_graph()
        result = await graph.ainvoke(
            initial_state(HumanMessage(content=incident_text), incident_id=payload.incident_id),
            config=config_graph
        )

        route = [m.name for m in result.get("messages", []) if getattr(m, "name", None)]

        return TriageResponse(
            incident_id=payload.incident_id,
            answer=_final_answer(result),
            route=route,
            cost_usd=cost_snapshot()["usd"],
            thread_id=thread_id,
            processed_at=datetime.now(timezone.utc).isoformat(),
        )
    except Exception as exc:
        logger.error("webhook.failed", error=str(exc), incident_id=payload.incident_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Agent graph execution failed. Check logs for details."
        )


@app.post("/stream")
@limiter.limit(f"{config.RATE_LIMIT_PER_MINUTE}/minute")
async def stream_endpoint(request: Request, payload: IncidentWebhookPayload):
    """SSE streaming: one event per worker node as it runs."""
    verify_webhook_auth(request)

    reset_cost()
    thread_id = payload.incident_id
    config_graph = {"configurable": {"thread_id": thread_id}, "recursion_limit": 40}

    incident_text = (
        f"INCIDENT ALERT\n"
        f"Incident ID: {payload.incident_id}\n"
        f"Source: {payload.source}\n"
        f"Component: {payload.component}\n"
        f"Timestamp: {payload.timestamp}\n"
        f"Security Event: {payload.is_security_event}\n"
        f"Severity Hint: {payload.severity_hint or 'P2'}\n"
        f"Raw Log: {payload.raw_log}"
    )

    async def event_gen():
        graph = get_triage_graph()
        state = initial_state(HumanMessage(content=incident_text), incident_id=payload.incident_id)
        final = ""
        async for chunk in graph.astream(state, config=config_graph, stream_mode="updates"):
            for node, update in chunk.items():
                msgs = update.get("messages", []) if isinstance(update, dict) else []
                text = msgs[-1].content if msgs else ""
                if text:
                    final = text
                yield {"event": "node", "data": json.dumps({"node": node, "text": text[:500]})}
        yield {"event": "done", "data": json.dumps({"answer": final, "cost_usd": cost_snapshot()["usd"]})}

    return EventSourceResponse(event_gen())


@app.post("/copilot/chat", response_model=CopilotChatResponse, status_code=status.HTTP_200_OK)
@limiter.limit("20/minute")
async def copilot_chat(request: Request, chat_req: CopilotChatRequest):
    from src.llm import get_llm

    client = get_llm("code", temperature=0.3)
    messages = [
        {"role": "system", "content": "You are the Huawei Cloud MaaS SRE Copilot. Answer concisely."},
    ]
    if chat_req.incident_context:
        messages.append({"role": "system", "content": f"Incident context: {chat_req.incident_context}"})
    messages.append({"role": "user", "content": chat_req.message})

    try:
        from langchain_core.messages import HumanMessage, SystemMessage
        lc_messages = []
        for m in messages:
            if m["role"] == "system":
                lc_messages.append(SystemMessage(content=m["content"]))
            else:
                lc_messages.append(HumanMessage(content=m["content"]))
        reply = client.invoke(lc_messages).content
        return CopilotChatResponse(reply=reply)
    except Exception as e:
        logger.error("copilot.chat_failed", error=str(e))
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="LLM service unavailable.")


@app.post("/copilot/stream")
@limiter.limit("20/minute")
async def copilot_stream(request: Request, chat_req: CopilotChatRequest):
    from src.llm import get_llm
    from langchain_core.messages import HumanMessage, SystemMessage

    client = get_llm("code", temperature=0.3)
    messages = [SystemMessage(content="You are the Huawei Cloud MaaS SRE Copilot. Answer concisely.")]
    if chat_req.incident_context:
        messages.append(SystemMessage(content=f"Incident context: {chat_req.incident_context}"))
    messages.append(HumanMessage(content=chat_req.message))

    async def stream_gen():
        try:
            for chunk in client.stream(messages):
                if chunk.content:
                    yield f"data: {chunk.content}\n\n"
            yield "data: [DONE]\n\n"
        except Exception as e:
            yield f"data: Error: {str(e)}\n\n"

    return StreamingResponse(stream_gen(), media_type="text/event-stream")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
