"""Running cost accumulator."""
from __future__ import annotations

from dataclasses import dataclass

PRICE_PER_1K_PROMPT = 0.0005
PRICE_PER_1K_COMPLETION = 0.0015


@dataclass
class _Cost:
    prompt_tokens: int = 0
    completion_tokens: int = 0

    @property
    def usd(self) -> float:
        return (
            self.prompt_tokens / 1000 * PRICE_PER_1K_PROMPT
            + self.completion_tokens / 1000 * PRICE_PER_1K_COMPLETION
        )


_state: _Cost = _Cost()


def add_usage(prompt_tokens: int = 0, completion_tokens: int = 0) -> None:
    _state.prompt_tokens += int(prompt_tokens or 0)
    _state.completion_tokens += int(completion_tokens or 0)


def cost_snapshot() -> dict:
    return {
        "prompt_tokens": _state.prompt_tokens,
        "completion_tokens": _state.completion_tokens,
        "usd": round(_state.usd, 6),
    }


def reset_cost() -> None:
    global _state
    _state = _Cost()
