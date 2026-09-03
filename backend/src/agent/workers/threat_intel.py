"""Threat Intel worker — enriches IOCs with external threat intelligence."""
from __future__ import annotations

from src.agent.base import build_worker, load_prompt
from src.tools.threat_intel import query_virustotal, query_abuseipdb
from src.tools.rag_query import rag_query


def build():
    return build_worker(
        name="threat_intel",
        tools=[query_virustotal, query_abuseipdb, rag_query],
        prompt=load_prompt("threat_intel"),
        model_role="code",
    )
