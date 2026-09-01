import re
from typing import Dict, Any

SQLI_PATTERN = re.compile(r"(?:union(?:\s+all)?\s+select|'\s*or\s*'?\d+'?\s*=\s*'?\d+|information_schema|--|\bselect\b.*\bfrom\b.*--)", re.IGNORECASE)
XSS_PATTERN = re.compile(r"(?:<script[\s\S]*?>[\s\S]*?<\/script>|<script.*?>|javascript:|onerror\s*=|onload\s*=)", re.IGNORECASE)
PATH_TRAVERSAL_PATTERN = re.compile(r"(?:\.\.\/\.\.\/|\.\.\\\.\.\\|\/etc\/passwd|c:\\windows\\system32)", re.IGNORECASE)

def validate_incident_description(description: str) -> Dict[str, Any]:
    """Analiza la descripción del log en busca de firmas de ciberataques y componentes."""
    is_security_event = False
    security_matches = []

    if SQLI_PATTERN.search(description):
        is_security_event = True
        security_matches.append("SQL_INJECTION")

    if XSS_PATTERN.search(description):
        is_security_event = True
        security_matches.append("CROSS_SITE_SCRIPTING")

    if PATH_TRAVERSAL_PATTERN.search(description):
        is_security_event = True
        security_matches.append("PATH_TRAVERSAL")

    component = "frontend"
    desc_lower = description.lower()
    if any(k in desc_lower for k in ["postgres", "mongo", "database", "sql", "27017"]):
        component = "database"
    elif any(k in desc_lower for k in ["auth", "login", "jwt", "token", "passwd"]):
        component = "auth"
    elif any(k in desc_lower for k in ["gateway", "proxy", "network", "dns", "port", "econnrefused"]):
        component = "network"

    return {
        "is_valid": len(description.strip()) >= 5,
        "is_security_event": is_security_event,
        "security_types": security_matches,
        "extracted_fields": {
            "component": component,
            "incident_type": "Security Alert" if is_security_event else "Infrastructure Anomaly",
            "severity": "P1" if is_security_event else "P2"
        }
    }
