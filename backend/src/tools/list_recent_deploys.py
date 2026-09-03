"""List recent deployments / config changes. For the demo, returns simulated
deploy history so the investigator can correlate an incident with a recent change.
"""

from langchain_core.tools import tool


_SIMULATED_DEPLOYS = [
    {"id": "deploy-012", "service": "frontend", "time": "2026-09-03T10:10:00Z",
     "commit": "a3f9c2d", "description": "Bump node to 18.19, add memory-intensive SSR cache"},
    {"id": "deploy-011", "service": "auth", "time": "2026-09-03T09:45:00Z",
     "commit": "e1b4c7a", "description": "Refactor login query builder (removed ORM layer)"},
    {"id": "deploy-010", "service": "database", "time": "2026-09-02T22:30:00Z",
     "commit": "5d2e7a1", "description": "Update connection pool config: maxPoolSize 50→10"},
]


@tool
def list_recent_deploys(service: str = "") -> str:
    """List recent deployments and config changes. Pass a service name to filter,
    or empty string for all. Use this to check if a recent change correlates with the incident.
    """
    deploys = _SIMULATED_DEPLOYS
    if service:
        deploys = [d for d in deploys if d["service"] == service]
    if not deploys:
        return "No recent deployments found."
    lines = []
    for d in deploys:
        lines.append(f"[{d['time']}] {d['id']} service={d['service']} commit={d['commit']} — {d['description']}")
    return "\n".join(lines)
