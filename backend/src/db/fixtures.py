"""Fixtures locales de conocimiento historico e incidentes (fallback offline)."""
from datetime import datetime, timezone, timedelta

KB_DATA = [
    {
        "incident_type": "Database Connectivity",
        "component": "database",
        "symptom": "MongoNetworkError or connection refused",
        "root_cause": "Database firewall rule blocking IP or egress network partition",
        "resolution_steps": [
            "1. Verify database Network Access whitelist",
            "2. Inspect firewall/iptables rules: iptables -L",
            "3. Test TCP connection: nc -zv cluster0.mongodb.net 27017",
            "4. Verify application connection string credentials"
        ],
        "confidence": 0.95
    },
    {
        "incident_type": "Memory Pressure",
        "component": "frontend",
        "symptom": "OOM killer triggered, container restarts",
        "root_cause": "Process memory allocation exceeds container limits (512M cgroup limit)",
        "resolution_steps": [
            "1. Check container memory usage: docker stats triage-nextjs",
            "2. Review heap profile and recent deployments",
            "3. Increase Docker Compose memory limit if required",
            "4. Restart frontend container: docker restart triage-nextjs"
        ],
        "confidence": 0.90
    },
    {
        "incident_type": "Security Alert",
        "component": "auth",
        "symptom": "SQL Injection attempt detected in login parameters",
        "root_cause": "Malicious payload detected from external IP attempting SQL injection",
        "resolution_steps": [
            "1. Block offending source IP in firewall/Security Group",
            "2. Enable WAF strict filtering rules",
            "3. Notify SOC and initiate credential audit"
        ],
        "confidence": 0.99
    }
]

HISTORICAL_INCIDENTS = [
    {
        "incident_id": "hist-001",
        "incident_type": "Database Connectivity",
        "component": "database",
        "severity": "P1",
        "mttd_minutes": 2.5,
        "mttr_minutes": 14.0,
        "resolution": "Restored egress network rule",
        "timestamp": (datetime.now(timezone.utc) - timedelta(days=2)).isoformat()
    },
    {
        "incident_id": "hist-002",
        "incident_type": "Memory Pressure",
        "component": "frontend",
        "severity": "P2",
        "mttd_minutes": 4.0,
        "mttr_minutes": 20.0,
        "resolution": "Cleared memory leak and restarted service",
        "timestamp": (datetime.now(timezone.utc) - timedelta(days=5)).isoformat()
    },
    {
        "incident_id": "hist-003",
        "incident_type": "High Latency",
        "component": "network",
        "severity": "P3",
        "mttd_minutes": 8.0,
        "mttr_minutes": 35.0,
        "resolution": "Scaled container instances",
        "timestamp": (datetime.now(timezone.utc) - timedelta(days=10)).isoformat()
    }
]
