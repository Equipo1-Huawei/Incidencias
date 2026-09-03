from typing import TypedDict, Optional, List, Dict, Any
from datetime import datetime

from langgraph.graph import MessagesState


class IncidentData(TypedDict, total=False):
    """Datos del incidente recibido por webhook o UI."""
    incident_id: str
    description: str
    component: Optional[str]
    severity: Optional[str] # P1, P2, P3
    source: Optional[str]
    is_security_event: bool
    timestamp: datetime

class DiagnosticStep(TypedDict, total=False):
    """Registro de cada paso y herramienta ejecutada por el agente."""
    step_number: int
    tool_name: str
    input: Dict[str, Any]
    output: str
    reasoning: str

class AgentState(MessagesState, total=False):
    """Estado global del grafo agéntico — extendido con campos de multiagente.
    Extiende MessagesState para que `messages` use el reducer add_messages."""
    # --- Dominio IR (original de Pato) ---
    incident: IncidentData
    identified_type: Optional[str]
    identified_component: Optional[str]
    diagnostic_steps: List[DiagnosticStep]
    component_status: Optional[Dict[str, Any]]
    historical_patterns: List[Dict[str, Any]]
    kb_solutions: List[Dict[str, Any]]
    risk_score: float
    estimated_mttr_minutes: Optional[float]
    escalation_required: bool
    escalation_path: Optional[str]
    diagnostics_checklist: List[str]
    root_cause_hypothesis: str
    final_recommendation: str

    # --- Multiagente: orquestación ---
    next_agent: Optional[str]          # routing del supervisor
    plan: List[str]                    # subtasks del plan
    scratchpad: Dict[str, Any]         # findings intermedios por worker
    citations: List[Dict]              # fuentes para anti-alucinación

    # --- Multiagente: guardrails ---
    loop_count: int
    total_cost_usd: float

    # --- Incident Response: auditoría + HITL ---
    incident_id: str
    severity: Optional[str]            # SEV1..SEV4 / P1..P3
    affected_services: List[str]
    status: str                        # investigating | mitigating | resolved
    actions_taken: List[Dict]          # auditoría de cada acción ejecutada
    pending_approval: Optional[Dict]   # acción esperando luz verde humana


def initial_state(incident_data: dict = None, user_message: str = None) -> dict:
    """Construye el estado inicial para una nueva corrida."""
    from langchain_core.messages import HumanMessage
    import uuid

    incident_id = str(uuid.uuid4())
    messages = []
    if user_message:
        messages = [HumanMessage(content=user_message)]

    state = {
        "incident": incident_data or {},
        "incident_id": incident_id,
        "messages": messages,
        "diagnostic_steps": [],
        "plan": [],
        "scratchpad": {},
        "citations": [],
        "next_agent": None,
        "loop_count": 0,
        "total_cost_usd": 0.0,
        "actions_taken": [],
        "pending_approval": None,
        "status": "investigating",
        "affected_services": [],
        "severity": None,
        "root_cause_hypothesis": "",
        "final_recommendation": "",
        "diagnostics_checklist": [],
        "risk_score": 0.0,
        "escalation_path": None,
    }
    return state
