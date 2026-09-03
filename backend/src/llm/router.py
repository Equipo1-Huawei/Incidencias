"""Maps a semantic role to a concrete model."""
from __future__ import annotations

from functools import lru_cache

from langchain_openai import ChatOpenAI

from src.config import config
from src.llm.kostra_client import make_llm
from src.llm.callbacks import CostCallback


@lru_cache(maxsize=16)
def _cached_llm(model: str, temperature: float) -> ChatOpenAI:
    llm = make_llm(model, temperature=temperature)
    llm.callbacks = [CostCallback()]
    return llm


def get_llm(role: str = "code", temperature: float = 0.2) -> ChatOpenAI:
    role_map = {
        "code": config.HUAWEI_MODEL,
        "fast": config.HUAWEI_MODEL,
        "think": config.HUAWEI_MODEL,
    }
    model = role_map.get(role, config.HUAWEI_MODEL)
    return _cached_llm(model, temperature)
