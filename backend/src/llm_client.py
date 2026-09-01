import os
import json
from abc import ABC, abstractmethod
from typing import Optional, List, Dict
import httpx
from src.config import config

class LLMClient(ABC):
    """Abstract base class para clientes LLM del sistema de triage."""
    @abstractmethod
    async def call(self, messages: List[Dict[str, str]], temperature: Optional[float] = None, max_tokens: Optional[int] = None) -> str:
        pass

class ResilientLLMClient(LLMClient):
    """Cliente resiliente con Pangu 40B primario y failover automático a OpenAI."""
    def __init__(self):
        self.pangu_api_key = config.PANGU_API_KEY
        self.pangu_base_url = config.PANGU_BASE_URL.rstrip("/")
        self.openai_key = config.OPENAI_FALLBACK_KEY
        self.openai_base_url = config.OPENAI_BASE_URL.rstrip("/")
        self.timeout = httpx.Timeout(timeout=10.0, connect=3.0)

    async def _execute_http(self, base_url: str, api_key: str, model: str, messages: List[Dict[str, str]], temperature: float, max_tokens: int) -> str:
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

    async def call(self, messages: List[Dict[str, str]], temperature: Optional[float] = None, max_tokens: Optional[int] = None) -> str:
        temp = temperature if temperature is not None else config.AGENT_TEMPERATURE
        tokens = max_tokens or config.AGENT_MAX_TOKENS

        # 1. Intento primario con Huawei Cloud MaaS (Pangu 40B)
        if self.pangu_api_key:
            for attempt in range(2):
                try:
                    return await self._execute_http(
                        base_url=self.pangu_base_url,
                        api_key=self.pangu_api_key,
                        model=config.HUAWEI_MODEL,
                        messages=messages,
                        temperature=temp,
                        max_tokens=tokens
                    )
                except (httpx.TimeoutException, httpx.HTTPError) as err:
                    if attempt == 1:
                        # Log error internally and switch to fallback
                        break

        # 2. Failover automático a OpenAI / API compatible
        if self.openai_key:
            try:
                return await self._execute_http(
                    base_url=self.openai_base_url,
                    api_key=self.openai_key,
                    model=config.OPENAI_MODEL,
                    messages=messages,
                    temperature=temp,
                    max_tokens=tokens
                )
            except Exception as e:
                raise RuntimeError(f"All LLM providers failed. Fallback error: {str(e)}")

        # 3. Fallback heurístico en modo offline / testing si no hay keys configuradas
        return json.dumps({
            "incident_classification": "INFRASTRUCTURE_FAILURE",
            "root_cause_hypothesis": "Heuristic analysis: High latency or connectivity refusal detected in service telemetry.",
            "escalation_team": "SRE_ONCALL",
            "mitigation_commands": [
                "docker logs triage-nextjs --tail 100",
                "docker restart triage-nextjs"
            ],
            "operator_checklist": [
                "Verify MongoDB Atlas connectivity",
                "Check system memory and container metrics"
            ]
        })
