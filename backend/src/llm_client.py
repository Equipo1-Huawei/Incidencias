"""Cliente LLM resiliente: Pangu 40B primario, failover OpenAI, modo simulacion offline.

Mejoras:
- Singleton via get_llm_client()
- Timeout desde config (no hardcoded)
- Retry con backoff exponencial (tenacity)
- Streaming para copilot chat
- Logging estructurado
"""
import os
import json
from abc import ABC, abstractmethod
from typing import Optional, List, Dict, AsyncIterator
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from src.config import config
from src.logging_config import get_logger

logger = get_logger(__name__)


class LLMClient(ABC):
    """Abstract base class para clientes LLM del sistema de triage."""

    @abstractmethod
    async def call(self, messages: List[Dict[str, str]], temperature: Optional[float] = None, max_tokens: Optional[int] = None) -> str:
        pass

    @abstractmethod
    async def stream(self, messages: List[Dict[str, str]], temperature: Optional[float] = None, max_tokens: Optional[int] = None) -> AsyncIterator[str]:
        pass


class ResilientLLMClient(LLMClient):
    """Cliente resiliente con Pangu 40B primario y failover automatico a OpenAI."""

    _instance: Optional["ResilientLLMClient"] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if getattr(self, "_initialized", False):
            return
        self.pangu_api_key = config.PANGU_API_KEY
        self.pangu_base_url = config.PANGU_BASE_URL.rstrip("/")
        self.openai_key = config.OPENAI_FALLBACK_KEY
        self.openai_base_url = config.OPENAI_BASE_URL.rstrip("/")
        self.timeout = httpx.Timeout(timeout=config.AGENT_TIMEOUT_SECONDS, connect=3.0)
        self._initialized = True
        logger.info("llm_client.init", pangu=bool(self.pangu_api_key), openai=bool(self.openai_key))

    async def _execute_http(self, base_url: str, api_key: str, model: str,
                            messages: List[Dict[str, str]], temperature: float, max_tokens: int) -> str:
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(f"{base_url}/v1/chat/completions", json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=5),
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.HTTPError)),
        reraise=True,
    )
    async def _call_with_retry(self, base_url: str, api_key: str, model: str,
                               messages: List[Dict[str, str]], temperature: float, max_tokens: int) -> str:
        return await self._execute_http(base_url, api_key, model, messages, temperature, max_tokens)

    async def call(self, messages: List[Dict[str, str]], temperature: Optional[float] = None, max_tokens: Optional[int] = None) -> str:
        temp = temperature if temperature is not None else config.AGENT_TEMPERATURE
        tokens = max_tokens or config.AGENT_MAX_TOKENS

        if self.pangu_api_key:
            try:
                result = await self._call_with_retry(
                    base_url=self.pangu_base_url,
                    api_key=self.pangu_api_key,
                    model=config.HUAWEI_MODEL,
                    messages=messages,
                    temperature=temp,
                    max_tokens=tokens
                )
                logger.info("llm_client.success", provider="pangu", model=config.HUAWEI_MODEL)
                return result
            except (httpx.TimeoutException, httpx.HTTPError) as err:
                logger.warning("llm_client.pangu_failed", error=str(err), fallback="openai")

        if self.openai_key:
            try:
                result = await self._call_with_retry(
                    base_url=self.openai_base_url,
                    api_key=self.openai_key,
                    model=config.OPENAI_MODEL,
                    messages=messages,
                    temperature=temp,
                    max_tokens=tokens
                )
                logger.info("llm_client.success", provider="openai", model=config.OPENAI_MODEL)
                return result
            except Exception as e:
                logger.error("llm_client.all_providers_failed", error=str(e))
                raise RuntimeError(f"All LLM providers failed. Fallback error: {str(e)}")

        logger.info("llm_client.offline_mode", reason="no_api_keys")
        return self._offline_inference(messages)

    async def stream(self, messages: List[Dict[str, str]], temperature: Optional[float] = None, max_tokens: Optional[int] = None) -> AsyncIterator[str]:
        """Streaming para copilot chat. Si no soporta streaming, delega a call()."""
        temp = temperature if temperature is not None else config.AGENT_TEMPERATURE
        tokens = max_tokens or config.AGENT_MAX_TOKENS

        provider_url = None
        provider_key = None
        provider_model = None

        if self.pangu_api_key:
            provider_url = self.pangu_base_url
            provider_key = self.pangu_api_key
            provider_model = config.HUAWEI_MODEL
        elif self.openai_key:
            provider_url = self.openai_base_url
            provider_key = self.openai_key
            provider_model = config.OPENAI_MODEL

        if provider_url and provider_key:
            headers = {
                "Authorization": f"Bearer {provider_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": provider_model,
                "messages": messages,
                "temperature": temp,
                "max_tokens": tokens,
                "stream": True
            }
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    async with client.stream("POST", f"{provider_url}/v1/chat/completions", json=payload, headers=headers) as response:
                        response.raise_for_status()
                        async for line in response.aiter_lines():
                            if line.startswith("data: ") and line.strip() != "data: [DONE]":
                                try:
                                    chunk = json.loads(line[6:])
                                    delta = chunk["choices"][0]["delta"].get("content", "")
                                    if delta:
                                        yield delta
                                except (json.JSONDecodeError, KeyError, IndexError):
                                    continue
                return
            except Exception as e:
                logger.warning("llm_client.stream_failed", error=str(e), fallback="non_stream")

        result = await self.call(messages, temperature, max_tokens)
        yield result

    def _offline_inference(self, messages: List[Dict[str, str]]) -> str:
        """Modo simulacion offline con deteccion contextual del incidente."""
        prompt_content = ""
        for m in messages:
            if m.get("role") == "user":
                prompt_content = m.get("content", "")
                break

        content_lower = prompt_content.lower()

        if "union" in content_lower or "sql" in content_lower or "auth" in content_lower:
            return json.dumps({
                "incident_classification": "CYBER_SECURITY_EVENT",
                "root_cause_hypothesis": "SQL Injection vulnerability exploited on authentication endpoint via UNION SELECT payload.",
                "escalation_team": "SOC",
                "mitigation_commands": [
                    "iptables -A INPUT -s 192.168.10.45 -j DROP",
                    "aws ec2 create-security-group-rule --group-id sg-01 --protocol tcp --port 80 --cidr 192.168.10.45/32 --rule-action deny"
                ],
                "operator_checklist": [
                    "Confirm malicious IP 192.168.10.45 is isolated",
                    "Enable WAF rule for SQLi signature prevention",
                    "Audit affected user credentials in database"
                ]
            })
        elif "script" in content_lower or "xss" in content_lower:
            return json.dumps({
                "incident_classification": "CYBER_SECURITY_EVENT",
                "root_cause_hypothesis": "Reflected Cross-Site Scripting (XSS) payload detected targeting search parameter cookie exfiltration.",
                "escalation_team": "SOC",
                "mitigation_commands": [
                    "iptables -A INPUT -s 192.168.10.88 -j DROP",
                    "nginx -s reload # Apply sanitized CSP policy"
                ],
                "operator_checklist": [
                    "Block attacker source IP 192.168.10.88",
                    "Verify Content-Security-Policy (CSP) headers are active",
                    "Invalidate active operator session tokens"
                ]
            })
        elif "passwd" in content_lower or "traversal" in content_lower or ".." in content_lower:
            return json.dumps({
                "incident_classification": "CYBER_SECURITY_EVENT",
                "root_cause_hypothesis": "Path Traversal attack attempting directory escape to read sensitive file /etc/passwd.",
                "escalation_team": "SOC",
                "mitigation_commands": [
                    "iptables -A INPUT -s 192.168.10.92 -j DROP",
                    "chmod 600 /etc/passwd"
                ],
                "operator_checklist": [
                    "Block attacker source IP 192.168.10.92",
                    "Verify static file server disables dot-dot path resolution",
                    "Check system integrity and file access audit logs"
                ]
            })
        elif "mongonetworkerror" in content_lower or "database" in content_lower or "27017" in content_lower:
            return json.dumps({
                "incident_classification": "INFRASTRUCTURE_FAILURE",
                "root_cause_hypothesis": "Database connectivity failure caused by network egress partition or blocked TCP port 27017.",
                "escalation_team": "SRE_ONCALL",
                "mitigation_commands": [
                    "iptables -D OUTPUT -p tcp --dport 27017 -j REJECT || true",
                    "nc -zv cluster0.mongodb.net 27017",
                    "docker restart triage-nextjs"
                ],
                "operator_checklist": [
                    "Verify database cluster status in cloud console",
                    "Check egress firewall rules and routing table",
                    "Inspect frontend connection pool metrics"
                ]
            })
        elif "oom" in content_lower or "memory" in content_lower or "stress" in content_lower:
            return json.dumps({
                "incident_classification": "INFRASTRUCTURE_FAILURE",
                "root_cause_hypothesis": "Container Out-Of-Memory (OOM) crash: Process heap exceeded 512MB cgroup allocation threshold.",
                "escalation_team": "SRE_ONCALL",
                "mitigation_commands": [
                    "docker restart triage-nextjs",
                    "docker stats triage-nextjs --no-stream"
                ],
                "operator_checklist": [
                    "Verify memory utilization and restart container",
                    "Review recent deployments for uncollected memory leaks",
                    "Adjust Docker Compose memory limit if workload increased"
                ]
            })
        else:
            return json.dumps({
                "incident_classification": "INFRASTRUCTURE_FAILURE",
                "root_cause_hypothesis": "High latency or degraded service performance detected in telemetry.",
                "escalation_team": "PLATFORM_TEAM",
                "mitigation_commands": [
                    "docker logs triage-nextjs --tail 100",
                    "docker stats --no-stream"
                ],
                "operator_checklist": [
                    "Check service logs for unhandled errors",
                    "Monitor CPU and memory utilization across hosts"
                ]
            })


_llm_client_instance: Optional[ResilientLLMClient] = None

def get_llm_client() -> ResilientLLMClient:
    """Factory singleton."""
    global _llm_client_instance
    if _llm_client_instance is None:
        _llm_client_instance = ResilientLLMClient()
    return _llm_client_instance
