"""Queries a Supabase (PostgreSQL) con degradación controlada a fixtures locales."""
import httpx
from typing import Dict, Any, Optional, List
from src.config import config
from src.db.supabase_client import get_supabase_client, is_supabase_available
from src.logging_config import get_logger

logger = get_logger(__name__)


async def check_component_health(component: str) -> Dict[str, Any]:
    """Consulta la salud del componente via HTTP hacia Next.js con degradacion controlada."""
    nextjs_health_url = config.NEXTJS_HEALTH_URL

    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(2.5, connect=1.5)) as client:
            response = await client.get(nextjs_health_url)
            data = response.json()
            return {
                "component": component,
                "status": data.get("status", "UNKNOWN"),
                "latency_ms": data.get("latency_ms", 0),
                "is_operational": data.get("status") == "UP",
                "error_code": data.get("error_code")
            }
    except (httpx.TimeoutException, httpx.ConnectError):
        return {
            "component": component,
            "status": "UNKNOWN",
            "latency_ms": None,
            "is_operational": False,
            "error_code": "HEALTHCHECK_TIMEOUT"
        }
    except Exception as e:
        return {
            "component": component,
            "status": "UNKNOWN",
            "latency_ms": None,
            "is_operational": False,
            "error_code": str(e)
        }


async def query_historical_incidents(component: str, incident_type: Optional[str] = None, limit: int = 5) -> Dict[str, Any]:
    """Consulta incidentes pasados en Supabase (PostgreSQL)."""
    if not is_supabase_available():
        return _fallback_historical(component)

    try:
        client = get_supabase_client()
        query = client.table("incident_history").select(
            "incident_id, incident_type, component, severity, mttd_minutes, mttr_minutes, resolution, timestamp"
        ).eq("component", component).order("timestamp", desc=True).limit(limit)

        if incident_type:
            query = query.ilike("incident_type", f"%{incident_type}%")

        result = query.execute()
        incidents: List[Dict[str, Any]] = result.data or []

        if incidents:
            valid_mttr = [i["mttr_minutes"] for i in incidents if i.get("mttr_minutes") is not None]
            valid_mttd = [i["mttd_minutes"] for i in incidents if i.get("mttd_minutes") is not None]
            avg_mttr = sum(valid_mttr) / len(valid_mttr) if valid_mttr else None
            avg_mttd = sum(valid_mttd) / len(valid_mttd) if valid_mttd else None
        else:
            avg_mttr = None
            avg_mttd = None

        logger.info("queries.historical_fetched", component=component, count=len(incidents))
        return {
            "component": component,
            "total_incidents": len(incidents),
            "incidents": incidents,
            "average_mttr_minutes": avg_mttr,
            "average_mttd_minutes": avg_mttd,
        }
    except Exception as e:
        logger.warning("queries.historical_failed", error=str(e), fallback="fixtures")
        return _fallback_historical(component)


def _fallback_historical(component: str) -> Dict[str, Any]:
    from src.db.fixtures import HISTORICAL_INCIDENTS
    mock_matches = [i for i in HISTORICAL_INCIDENTS if i.get("component") == component]
    if not mock_matches:
        mock_matches = HISTORICAL_INCIDENTS[:2]

    valid_mttr = [i["mttr_minutes"] for i in mock_matches if i.get("mttr_minutes")]
    valid_mttd = [i["mttd_minutes"] for i in mock_matches if i.get("mttd_minutes")]
    avg_mttr = sum(valid_mttr) / len(valid_mttr) if valid_mttr else None
    avg_mttd = sum(valid_mttd) / len(valid_mttd) if valid_mttd else None

    return {
        "component": component,
        "total_incidents": len(mock_matches),
        "incidents": mock_matches,
        "average_mttr_minutes": avg_mttr,
        "average_mttd_minutes": avg_mttd,
    }


async def search_solutions_in_kb(incident_type: str, component: str) -> List[Dict[str, Any]]:
    """Busca soluciones en la base de conocimiento de Supabase o fallback a KB local."""
    if not is_supabase_available():
        return _fallback_kb(incident_type, component)

    try:
        client = get_supabase_client()
        result = client.table("knowledge_base").select(
            "incident_type, component, symptom, root_cause, resolution_steps, confidence"
        ).or_(
            f"incident_type.ilike.%{incident_type}%,component.eq.{component}"
        ).limit(3).execute()

        solutions = result.data or []
        if solutions:
            logger.info("queries.kb_fetched", component=component, count=len(solutions))
            return solutions
    except Exception as e:
        logger.warning("queries.kb_failed", error=str(e), fallback="fixtures")

    return _fallback_kb(incident_type, component)


def _fallback_kb(incident_type: str, component: str) -> List[Dict[str, Any]]:
    from src.db.fixtures import KB_DATA
    matching = [
        k for k in KB_DATA
        if incident_type.lower() in k.get("incident_type", "").lower()
        or component.lower() == k.get("component", "").lower()
    ]
    return matching if matching else KB_DATA[:1]


async def save_incident_result(state: Dict[str, Any]) -> None:
    """Persiste el resultado del triage en Supabase."""
    if not is_supabase_available():
        logger.info("queries.save_skipped", reason="supabase_not_configured")
        return

    try:
        incident = state.get("incident", {})
        client = get_supabase_client()

        record = {
            "incident_id": incident.get("incident_id"),
            "component": state.get("identified_component", incident.get("component")),
            "severity": incident.get("severity", "P2"),
            "source": incident.get("source"),
            "description": incident.get("description"),
            "is_security_event": incident.get("is_security_event", False),
            "risk_score": state.get("risk_score", 0.0),
            "root_cause_hypothesis": state.get("root_cause_hypothesis"),
            "escalation_team": state.get("escalation_path"),
            "mitigation_commands": state.get("final_recommendation"),
            "diagnostics_checklist": state.get("diagnostics_checklist", []),
            "diagnostic_steps": state.get("diagnostic_steps", []),
        }

        client.table("incident_history").insert(record).execute()
        logger.info("queries.incident_saved", incident_id=record["incident_id"])
    except Exception as e:
        logger.error("queries.save_failed", error=str(e))


async def save_audit_event(event_type: str, incident_id: Optional[str] = None,
                           actor: Optional[str] = None, detail: Optional[Dict] = None,
                           approved: Optional[bool] = None, reason: Optional[str] = None) -> None:
    """Persiste un evento de auditoria en Supabase."""
    if not is_supabase_available():
        return

    try:
        client = get_supabase_client()
        record = {
            "event_type": event_type,
            "incident_id": incident_id,
            "actor": actor,
            "detail": detail or {},
            "approved": approved,
            "reason": reason,
        }
        client.table("audit_log").insert(record).execute()
    except Exception as e:
        logger.error("queries.audit_save_failed", error=str(e))
