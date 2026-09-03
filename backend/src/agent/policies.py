"""Guardrails: loop count + cost limits."""
from __future__ import annotations

from src.config import config
from src.tracing.cost import cost_snapshot


def should_stop(state: dict) -> tuple[bool, str]:
    loops = state.get("loop_count", 0)
    if loops >= config.MAX_LOOPS:
        return True, f"reached max loops ({config.MAX_LOOPS})"

    usd = cost_snapshot()["usd"]
    if usd >= config.MAX_COST_USD:
        return True, f"reached max cost (${config.MAX_COST_USD})"

    return False, ""
