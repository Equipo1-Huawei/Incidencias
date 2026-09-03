import pytest
import asyncio
import json
from src.llm_client import ResilientLLMClient, get_llm_client


def test_llm_client_singleton():
    """El cliente LLM debe ser singleton."""
    client1 = get_llm_client()
    client2 = get_llm_client()
    assert client1 is client2


def test_llm_client_offline_sqli():
    """Modo offline debe detectar SQLi y retornar JSON valido."""
    client = ResilientLLMClient()
    messages = [
        {"role": "system", "content": "test"},
        {"role": "user", "content": "UNION SELECT password FROM users--"}
    ]
    result = asyncio.run(client.call(messages))
    parsed = json.loads(result)
    assert parsed["incident_classification"] == "CYBER_SECURITY_EVENT"
    assert parsed["escalation_team"] == "SOC"


def test_llm_client_offline_xss():
    """Modo offline debe detectar XSS."""
    client = ResilientLLMClient()
    messages = [
        {"role": "system", "content": "test"},
        {"role": "user", "content": "<script>alert('xss')</script>"}
    ]
    result = asyncio.run(client.call(messages))
    parsed = json.loads(result)
    assert parsed["incident_classification"] == "CYBER_SECURITY_EVENT"


def test_llm_client_offline_oom():
    """Modo offline debe detectar OOM."""
    client = ResilientLLMClient()
    messages = [
        {"role": "system", "content": "test"},
        {"role": "user", "content": "fatal error: runtime: out of memory allocating 629145600 bytes"}
    ]
    result = asyncio.run(client.call(messages))
    parsed = json.loads(result)
    assert parsed["incident_classification"] == "INFRASTRUCTURE_FAILURE"
    assert parsed["escalation_team"] == "SRE_ONCALL"


def test_llm_client_offline_generic():
    """Modo offline debe manejar casos genericos."""
    client = ResilientLLMClient()
    messages = [
        {"role": "system", "content": "test"},
        {"role": "user", "content": "High latency detected on API endpoint"}
    ]
    result = asyncio.run(client.call(messages))
    parsed = json.loads(result)
    assert parsed["incident_classification"] == "INFRASTRUCTURE_FAILURE"
