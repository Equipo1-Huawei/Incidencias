import json
from src.agent.state import AgentState, DiagnosticStep
from src.tools.validators import validate_incident_description
from src.tools.queries import check_component_health, query_historical_incidents, search_solutions_in_kb
from src.tools.analyzers import calculate_risk_score, estimate_sla
from src.llm_client import ResilientLLMClient

async def node_analyze_incident(state: AgentState) -> dict:
    """Nodo 1: Análisis inicial, parsing y detección de firmas de seguridad."""
    incident = state.get("incident", {})
    description = incident.get("description", "")
    diagnostic_steps = state.get("diagnostic_steps", [])

    val_res = validate_incident_description(description)
    
    diagnostic_steps.append(DiagnosticStep(
        step_number=1,
        tool_name="validate_incident",
        input={"description": description},
        output=json.dumps(val_res, default=str),
        reasoning="Extract entities, identify component and inspect cybersecurity signatures"
    ))

    # Detectar o preservar evento de seguridad
    is_sec = incident.get("is_security_event", False) or val_res.get("is_security_event", False)
    component = incident.get("component") or val_res.get("extracted_fields", {}).get("component", "frontend")
    incident_type = val_res.get("extracted_fields", {}).get("incident_type", "Infrastructure Anomaly")

    return {
        "identified_component": component,
        "identified_type": incident_type,
        "incident": {
            **incident,
            "component": component,
            "is_security_event": is_sec
        },
        "diagnostic_steps": diagnostic_steps
    }

async def node_execute_tools(state: AgentState) -> dict:
    """Nodo 2: Ejecución de healthcheck activo en Next.js y consulta histórica en Atlas."""
    component = state.get("identified_component", "frontend")
    incident_type = state.get("identified_type", "Anomaly")
    diagnostic_steps = state.get("diagnostic_steps", [])

    # Tool 2: Healthcheck HTTP activo
    health_res = await check_component_health(component)
    diagnostic_steps.append(DiagnosticStep(
        step_number=2,
        tool_name="check_health",
        input={"component": component},
        output=json.dumps(health_res, default=str),
        reasoning=f"Verify live operational health for component: {component}"
    ))

    # Tool 3: Query histórico MongoDB Atlas
    hist_res = await query_historical_incidents(component, incident_type)
    diagnostic_steps.append(DiagnosticStep(
        step_number=3,
        tool_name="query_historical",
        input={"component": component, "incident_type": incident_type},
        output=json.dumps(hist_res, default=str),
        reasoning="Query MongoDB Atlas for past resolution patterns and MTTD/MTTR"
    ))

    # Tool 4: Knowledge base search
    kb_res = await search_solutions_in_kb(incident_type, component)
    diagnostic_steps.append(DiagnosticStep(
        step_number=4,
        tool_name="search_kb",
        input={"incident_type": incident_type, "component": component},
        output=json.dumps(kb_res, default=str),
        reasoning="Retrieve known remediation procedures"
    ))

    return {
        "component_status": health_res,
        "historical_patterns": hist_res.get("incidents", []),
        "kb_solutions": kb_res,
        "diagnostic_steps": diagnostic_steps
    }

async def node_calculate_score(state: AgentState) -> dict:
    """Nodo 3: Scoring de riesgo y estimación de SLA con regla dura de seguridad."""
    incident = state.get("incident", {})
    component = state.get("identified_component", "frontend")
    severity = incident.get("severity", "P2")
    is_sec = incident.get("is_security_event", False)
    comp_status = state.get("component_status", {})
    is_op = comp_status.get("is_operational", True)
    hist_patterns = state.get("historical_patterns", [])

    diagnostic_steps = state.get("diagnostic_steps", [])

    historical_mttd = None
    if hist_patterns:
        mttds = [p.get("mttd_minutes") for p in hist_patterns if p.get("mttd_minutes") is not None]
        if mttds:
            historical_mttd = sum(mttds) / len(mttds)

    risk_res = calculate_risk_score(
        component=component,
        severity=severity,
        is_operational=is_op,
        is_security_event=is_sec,
        historical_mttd=historical_mttd
    )

    diagnostic_steps.append(DiagnosticStep(
        step_number=5,
        tool_name="calculate_risk",
        input={"component": component, "severity": severity, "is_security_event": is_sec},
        output=json.dumps(risk_res, default=str),
        reasoning="Calculate overall incident risk score and assign escalation team"
    ))

    sla_res = estimate_sla(risk_res.get("severity", severity))
    
    return {
        "risk_score": risk_res["risk_score"],
        "escalation_required": risk_res["risk_score"] >= 7.0,
        "escalation_path": risk_res["escalation_team"],
        "estimated_mttr_minutes": sla_res.get("estimated_mttr_minutes"),
        "diagnostic_steps": diagnostic_steps
    }

async def node_generate_output(state: AgentState) -> dict:
    """Nodo 4: Invocación del LLM Pangu 40B / fallback OpenAI para salida estructurada."""
    incident = state.get("incident", {})
    client = ResilientLLMClient()

    system_prompt = """You are the Lead SRE and Security Orchestrator for the Huawei Cloud Autonomous Triage System.
Your job is to analyze real incident diagnostics and produce ONLY a valid, parseable JSON object.

CRITICAL CONSTRAINTS:
1. Differentiate strictly between an INFRASTRUCTURE FAILURE (e.g., OOM, DB timeout, network partition) and an ACTIVE SECURITY EVENT (e.g., SQL Injection, XSS, Path Traversal, credential stuffing).
2. DO NOT hallucinate or invent components that do not appear in the raw_log or diagnostic state.
3. In "mitigation_commands", provide ONLY defensive and containment bash/CLI commands (e.g., isolating containers, rotating credentials, applying iptables/Security Group blocks). NEVER output offensive or scanning tools (no nmap, sqlmap, hydra).
4. Output MUST BE STRICT JSON with NO markdown wrappers (no ```json), NO commentary before or after.

JSON OUTPUT SCHEMA:
{
  "incident_classification": "INFRASTRUCTURE_FAILURE | CYBER_SECURITY_EVENT",
  "root_cause_hypothesis": "string (concise, factual summary of the exact failure root cause)",
  "escalation_team": "SOC | SRE_ONCALL | PLATFORM_TEAM",
  "mitigation_commands": [
    "string (safe defensive bash/CLI command 1)"
  ],
  "operator_checklist": [
    "string (step 1)"
  ]
}"""

    user_payload = {
        "incident_id": incident.get("incident_id"),
        "raw_log": incident.get("description"),
        "component": state.get("identified_component"),
        "is_security_event": incident.get("is_security_event"),
        "risk_score": state.get("risk_score"),
        "component_status": state.get("component_status"),
        "kb_solutions_count": len(state.get("kb_solutions", []))
    }

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": json.dumps(user_payload, default=str)}
    ]

    try:
        raw_response = await client.call(messages)
        cleaned = raw_response.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        parsed = json.loads(cleaned)

        return {
            "root_cause_hypothesis": parsed.get("root_cause_hypothesis", "Under investigation"),
            "escalation_path": parsed.get("escalation_team", state.get("escalation_path")),
            "diagnostics_checklist": parsed.get("operator_checklist", [
                f"Verify {state.get('identified_component')} operational state",
                "Inspect system logs and firewall tables"
            ]),
            "final_recommendation": "\n".join(parsed.get("mitigation_commands", []))
        }
    except Exception:
        # Fallback determinista seguro
        is_sec = incident.get("is_security_event", False)
        return {
            "root_cause_hypothesis": "Active Cybersecurity Attack detected" if is_sec else f"Service failure detected on {state.get('identified_component')}",
            "escalation_path": "SOC" if is_sec else "SRE_ONCALL",
            "diagnostics_checklist": [
                "Isolate suspicious network source",
                "Verify database connection pool",
                "Review recent container logs"
            ],
            "final_recommendation": "docker logs triage-nextjs --tail 100"
        }
