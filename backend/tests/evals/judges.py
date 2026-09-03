"""LLM-as-judge — scores an answer against the case's `expects` field.
Adapted from arquitectura_multiagente/harness/evals/judges.py.
"""

from __future__ import annotations

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from src.config import config

_JUDGE_SYS = (
    "You are a strict but fair evaluator. Given a user question, the expected content of "
    "a good answer, and the actual answer, decide if the actual answer satisfies the "
    "expectation. Reply on the FIRST line with exactly PASS or FAIL, then a second line "
    "with a one-sentence reason."
)


def _get_judge_llm():
    if config.PANGU_API_KEY:
        return ChatOpenAI(
            model=config.HUAWEI_MODEL,
            base_url=config.PANGU_BASE_URL.rstrip("/") + "/v1",
            api_key=config.PANGU_API_KEY,
            temperature=0.0,
            timeout=30,
        )
    if config.OPENAI_FALLBACK_KEY:
        return ChatOpenAI(
            model=config.OPENAI_MODEL,
            base_url=config.OPENAI_BASE_URL,
            api_key=config.OPENAI_FALLBACK_KEY,
            temperature=0.0,
            timeout=30,
        )
    return None


def judge(question: str, expects: str, answer: str) -> tuple[bool, str]:
    llm = _get_judge_llm()
    if llm is None:
        # Fallback: simple keyword matching
        expects_lower = expects.lower()
        answer_lower = answer.lower()
        key_terms = [w for w in expects_lower.split() if len(w) > 4]
        matches = sum(1 for t in key_terms if t in answer_lower)
        passed = matches >= len(key_terms) * 0.3 if key_terms else False
        reason = f"Keyword fallback: {matches}/{len(key_terms)} terms matched"
        return passed, reason

    prompt = (
        f"QUESTION:\n{question}\n\nEXPECTED CONTENT:\n{expects}\n\nACTUAL ANSWER:\n{answer}"
    )
    try:
        resp = llm.invoke([SystemMessage(content=_JUDGE_SYS), HumanMessage(content=prompt)])
        text = (resp.content or "").strip()
    except Exception as e:
        return False, f"judge error: {e}"

    first = text.splitlines()[0].strip().upper() if text else ""
    passed = first.startswith("PASS")
    reason = text.split("\n", 1)[1].strip() if "\n" in text else text
    return passed, reason
