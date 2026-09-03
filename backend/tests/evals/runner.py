"""Run every case in cases.jsonl through the graph and score with the LLM judge.
Usage:  python -m tests.evals.runner
"""

from __future__ import annotations

import json
import asyncio
from pathlib import Path

from src.agent.graph import get_triage_graph
from src.agent.state import initial_state
from src.config import config
from src.tracing.cost import cost_snapshot, reset_cost
from tests.evals.judges import judge

_CASES = Path(__file__).parent / "cases.jsonl"


def _load_cases() -> list[dict]:
    cases = []
    for line in _CASES.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            cases.append(json.loads(line))
    return cases


def _final_answer(result: dict) -> str:
    messages = result.get("messages", [])
    if messages:
        last = messages[-1]
        return getattr(last, "content", str(last))
    scratchpad = result.get("scratchpad", {})
    return " | ".join(str(v) for v in scratchpad.values()) if scratchpad else ""


async def _run_case(c: dict) -> tuple[bool, str, float]:
    reset_cost()
    state = initial_state(user_message=c["input"])
    state["incident"] = {"description": c["input"], "component": "frontend", "severity": "P2"}
    try:
        graph = get_triage_graph()
        result = await graph.ainvoke(state, config={"recursion_limit": 40})
        answer = _final_answer(result)
    except Exception as e:
        answer = f"[run error: {e}]"

    ok, reason = judge(c["input"], c["expects"], answer)
    usd = cost_snapshot()["usd"]
    return ok, reason, usd


def main() -> None:
    cases = _load_cases()
    print(f"\nRunning {len(cases)} eval case(s)\n" + "=" * 60)

    passed = 0
    total_usd = 0.0
    for c in cases:
        ok, reason, usd = asyncio.run(_run_case(c))
        total_usd += usd
        passed += int(ok)
        mark = "PASS" if ok else "FAIL"
        print(f"[{mark}] {c['id']}  (${usd:.4f})  {reason[:80]}")

    print("=" * 60)
    rate = 100 * passed / len(cases) if cases else 0
    print(f"Passed {passed}/{len(cases)}  ({rate:.0f}%)   total ${total_usd:.4f}\n")


if __name__ == "__main__":
    main()
