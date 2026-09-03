"""The one and only way to get an LLM in this project."""
from src.llm.router import get_llm

__all__ = ["get_llm"]
