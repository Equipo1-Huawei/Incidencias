"""Factory for worker nodes.

Two patterns:
- reasoning-only (tools=[]): 1 LLM call, no tool execution
- hybrid (preprocess func): calls tools directly in Python, then 1 LLM call with results as context

This avoids the ReAct multi-call loop — each worker is exactly 1 LLM call.
"""
from __future__ import annotations

from pathlib import Path
from typing import Callable, Optional

from langchain_core.messages import SystemMessage, HumanMessage
from src.llm import get_llm
from src.tracing import get_logger

_PROMPTS_DIR = Path(__file__).resolve().parent / "prompts"
log = get_logger("worker")


def load_prompt(name: str) -> str:
    return (_PROMPTS_DIR / f"{name}.md").read_text(encoding="utf-8")


def build_worker(
    name: str,
    tools: list,
    prompt: str,
    model_role: str = "code",
) -> Callable:
    """Reasoning-only worker: 1 LLM call, no tools."""
    llm = get_llm(model_role)

    async def worker_node(state: dict) -> dict:
        log.info("worker.start", worker=name, mode="reasoning")
        msgs = [SystemMessage(content=prompt)] + state["messages"]
        ai = await llm.ainvoke(msgs)
        ai.name = name
        return {"messages": [ai]}

    worker_node.__name__ = f"{name}_node"
    return worker_node


def build_hybrid_worker(
    name: str,
    prompt: str,
    preprocess: Callable,
    model_role: str = "code",
) -> Callable:
    """Hybrid worker: calls tools directly in Python, then 1 LLM call.

    preprocess(state) -> str: returns tool results as context text.
    The LLM gets: [SystemMessage(prompt), HumanMessage(incident + tool_context)].
    """
    llm = get_llm(model_role)

    async def worker_node(state: dict) -> dict:
        log.info("worker.start", worker=name, mode="hybrid")
        context = await preprocess(state)
        user_msg = state["messages"][-1]
        combined = HumanMessage(content=f"{user_msg.content}\n\n--- TOOL RESULTS ---\n{context}")
        msgs = [SystemMessage(content=prompt), combined]
        ai = await llm.ainvoke(msgs)
        ai.name = name
        return {"messages": [ai]}

    worker_node.__name__ = f"{name}_node"
    return worker_node
