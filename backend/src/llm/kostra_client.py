"""Kostra/Huawei MaaS LLM client. OpenAI-compatible."""
from __future__ import annotations

from langchain_openai import ChatOpenAI

from src.config import config


def make_llm(model: str, temperature: float = 0.2, **kwargs) -> ChatOpenAI:
    api_key = config.PANGU_API_KEY or config.OPENAI_FALLBACK_KEY or "sk-placeholder-for-compilation"
    base_url = config.PANGU_BASE_URL if config.PANGU_API_KEY else config.OPENAI_BASE_URL

    return ChatOpenAI(
        model=model,
        base_url=base_url,
        api_key=api_key,
        temperature=temperature,
        timeout=config.AGENT_TIMEOUT_SECONDS,
        max_retries=2,
        **kwargs,
    )
