from typing import TypedDict, Optional, List, Dict, Any
from datetime import datetime

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

class AgentState(TypedDict, total=False):
    """Estado global del grafo agéntico."""
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
    messages: List[Dict[str, str]]
