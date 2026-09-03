"""LangChain callback that forwards token usage to the cost accumulator."""
from __future__ import annotations

from typing import Any

from langchain_core.callbacks import BaseCallbackHandler

from src.tracing.cost import add_usage


class CostCallback(BaseCallbackHandler):
    def on_llm_end(self, response: Any, **kwargs: Any) -> None:
        try:
            usage = None
            if getattr(response, "llm_output", None):
                usage = response.llm_output.get("token_usage") or response.llm_output.get("usage")
            if usage:
                add_usage(
                    prompt_tokens=usage.get("prompt_tokens", 0),
                    completion_tokens=usage.get("completion_tokens", 0),
                )
        except Exception:
            pass
