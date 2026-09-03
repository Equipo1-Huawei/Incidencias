"""Threat Intel worker — enriches IOCs. 1 LLM call + tools directas."""
from __future__ import annotations

import re
from src.agent.base import build_hybrid_worker, load_prompt
from src.tools.threat_intel import _vt_simulated, _abuse_simulated


def _extract_ips(text: str) -> list:
    return list(set(re.findall(r'\b(?:\d{1,3}\.){3}\d{1,3}\b', text)))


async def preprocess(state: dict) -> str:
    text = ""
    for msg in state.get("messages", []):
        if hasattr(msg, "content"):
            text += msg.content + "\n"

    ips = _extract_ips(text)
    if not ips:
        ips = ["192.168.10.45"]

    results = []
    for ip in ips[:3]:
        vt = _vt_simulated(ip)
        abuse = _abuse_simulated(ip)
        results.append(f"IP: {ip}\n{vt}\n{abuse}")

    return "\n\n".join(results)


def build():
    return build_hybrid_worker(
        name="threat_intel",
        prompt=load_prompt("threat_intel"),
        preprocess=preprocess,
        model_role="code",
    )
