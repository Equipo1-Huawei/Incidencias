"""Forensics worker — investigates root cause via logs, health, and history."""
from __future__ import annotations

from src.agent.base import build_worker, load_prompt
from src.tools.langchain_tools import check_health, query_historical, search_kb
from src.tools.rag_query import rag_query


def build():
    return build_worker(
        name="forensics",
        tools=[check_health, query_historical, search_kb, rag_query],
        prompt=load_prompt("forensics"),
        model_role="code",
    )
