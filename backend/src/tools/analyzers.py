from typing import Dict, Any, Optional

def calculate_risk_score(
    component: str,
    severity: str,
    is_operational: bool,
    is_security_event: bool = False,
    historical_mttd: Optional[float] = 10.0,
) -> Dict[str, Any]:
    """Función pura para calcular el scoring y nivel de escalamiento."""
    # Override prioritario e inmediato para eventos de ciberseguridad
    if is_security_event:
        return {
            "risk_score": 10.0,
            "category": "CRITICAL_SECURITY",
            "severity": "P1",
            "escalation_team": "SOC",
            "factors": {
                "security_override": True,
                "vector": "Active Cyber Attack Vector"
            },
            "recommendation": "Isolate host, block source IP in Security Group and notify SOC immediately."
        }

    score = 0.0
    severity_map = {"P1": 3.5, "P2": 2.0, "P3": 1.0}
    score += severity_map.get(severity, 1.0)

    if not is_operational:
        score += 3.5
    elif component in ["database", "auth"]:
        score += 2.0

    if historical_mttd is not None and historical_mttd < 5.0:
        score += 2.0
    elif historical_mttd is not None and historical_mttd < 15.0:
        score += 1.0

    final_score = round(min(10.0, score), 1)
    category = "CRITICAL" if final_score >= 8.0 else ("HIGH" if final_score >= 6.0 else "MEDIUM")

    return {
        "risk_score": final_score,
        "category": category,
        "severity": severity,
        "escalation_team": "On-call SRE" if final_score >= 7.0 else "Platform Team",
        "factors": {
            "severity_weight": severity_map.get(severity, 1.0),
            "service_down": not is_operational,
            "historical_mttd": historical_mttd
        },
        "recommendation": "Escalate immediately" if final_score >= 7.0 else "Standard triage"
    }

def estimate_sla(severity: str, historical_mttr: Optional[float] = None) -> Dict[str, Any]:
    """Estima SLAs de respuesta y recuperación."""
    sla_map = {
        "P1": {"response_min": 15, "resolution_min": 60},
        "P2": {"response_min": 30, "resolution_min": 240},
        "P3": {"response_min": 60, "resolution_min": 480}
    }
    targets = sla_map.get(severity, {"response_min": 120, "resolution_min": 1440})
    estimated_mttr = historical_mttr if historical_mttr is not None else targets["resolution_min"]
    
    return {
        "sla_response_minutes": targets["response_min"],
        "sla_resolution_minutes": targets["resolution_min"],
        "estimated_mttr_minutes": estimated_mttr,
        "sla_risk": "HIGH" if estimated_mttr > targets["resolution_min"] else "NORMAL"
    }
