"""Query logs from the monitored application. For the demo, reads from
data/seed/logs/ or falls back to simulated log lines based on the component.
"""

from langchain_core.tools import tool


_SIMULATED_LOGS = {
    "frontend": [
        "[2026-09-03T10:14:22Z] INFO  GET /api/health 200 18ms",
        "[2026-09-03T10:14:25Z] ERROR Out of memory allocating 629145600 bytes. Killed process 1422 (node).",
        "[2026-09-03T10:14:26Z] WARN  Container triage-nextjs restarted by OOM killer.",
    ],
    "database": [
        "[2026-09-03T10:15:01Z] ERROR MongoNetworkError: connection 1 to cluster0.mongodb.net:27017 timed out after 2000ms.",
        "[2026-09-03T10:15:03Z] WARN  Retrying connection attempt 2/3...",
        "[2026-09-03T10:15:05Z] ERROR Egress packet rejected on TCP 27017.",
    ],
    "auth": [
        "[2026-09-03T10:14:22Z] WARN  POST /api/auth/login 401 — suspicious payload from 192.168.10.45",
        "[2026-09-03T10:14:23Z] ERROR SQLi signature detected: UNION SELECT in username field.",
        "[2026-09-03T10:14:24Z] INFO  Rate limiter activated for IP 192.168.10.45.",
    ],
    "network": [
        "[2026-09-03T10:15:30Z] WARN  P95 latency spike: 3480ms on /api/health.",
        "[2026-09-03T10:15:31Z] INFO  iptables INPUT chain: 3 DROP rules active.",
    ],
}


@tool
def query_logs(component: str, lines: int = 20) -> str:
    """Query recent log lines for a given component (frontend, database, auth, network).
    Use this to investigate what happened around the time of an incident.
    """
    logs = _SIMULATED_LOGS.get(component, _SIMULATED_LOGS["frontend"])
    return "\n".join(logs[:lines])
