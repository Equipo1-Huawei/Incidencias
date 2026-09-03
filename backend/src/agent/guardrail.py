"""Agente B: Safety Guardrail Validator.

Audita los comandos generados por el Agente A para asegurar que
ninguna accion sea destructiva (formateos, borrado de datos, escaneos agresivos, etc.).
"""
import re
from typing import Dict, Any, List
from src.logging_config import get_logger

logger = get_logger(__name__)

DESTRUCTIVE_PATTERNS: List[re.Pattern] = [
    re.compile(r"\brm\s+-rf\b", re.IGNORECASE),
    re.compile(r"\bmkfs\b", re.IGNORECASE),
    re.compile(r"\bdd\s+if=", re.IGNORECASE),
    re.compile(r"\bDROP\s+TABLE\b", re.IGNORECASE),
    re.compile(r"\bDROP\s+DATABASE\b", re.IGNORECASE),
    re.compile(r"\bTRUNCATE\b", re.IGNORECASE),
    re.compile(r"\bDELETE\s+FROM\b.*\bWHERE\b.*\b1\s*=\s*1\b", re.IGNORECASE),
    re.compile(r":\(\)\s*\{\s*:\|:\&\s*\};:", re.IGNORECASE),
    re.compile(r"\bshutdown\b", re.IGNORECASE),
    re.compile(r"\breboot\b", re.IGNORECASE),
    re.compile(r"\bhalt\b", re.IGNORECASE),
    re.compile(r"\bkill(?:all)?\s+-9\b", re.IGNORECASE),
    re.compile(r">\s*/dev/sda", re.IGNORECASE),
    re.compile(r"\bchmod\s+777\b", re.IGNORECASE),
    re.compile(r"\bcurl\b.*\|\s*sh", re.IGNORECASE),
    re.compile(r"\bwget\b.*\|\s*sh", re.IGNORECASE),
]

OFFENSIVE_TOOL_PATTERNS: List[re.Pattern] = [
    re.compile(r"\bnmap\b", re.IGNORECASE),
    re.compile(r"\bsqlmap\b", re.IGNORECASE),
    re.compile(r"\bhydra\b", re.IGNORECASE),
    re.compile(r"\bmetasploit\b", re.IGNORECASE),
    re.compile(r"\bhashcat\b", re.IGNORECASE),
    re.compile(r"\bjohn\b.*--wordlist", re.IGNORECASE),
]

ALLOWED_DEFENSIVE_KEYWORDS = [
    "iptables", "docker restart", "docker logs", "docker stats",
    "chmod 600", "nginx -s reload", "nc -zv", "curl",
    "aws ec2", "huaweicloud", "security group", "waf",
]


def validate_commands(commands: str) -> Dict[str, Any]:
    """Valida que los comandos sean puramente defensivos y no destructivos.

    Returns:
        Dict with keys: approved (bool), reason (str), blocked_patterns (list)
    """
    if not commands or not commands.strip():
        return {
            "approved": True,
            "reason": "No commands to validate.",
            "blocked_patterns": [],
            "agent": "Safety Guardrail Validator"
        }

    blocked = []

    for pattern in DESTRUCTIVE_PATTERNS:
        match = pattern.search(commands)
        if match:
            blocked.append(f"DESTRUCTIVE: {pattern.pattern}")

    for pattern in OFFENSIVE_TOOL_PATTERNS:
        match = pattern.search(commands)
        if match:
            blocked.append(f"OFFENSIVE_TOOL: {pattern.pattern}")

    if blocked:
        reason = f"Blocked {len(blocked)} dangerous pattern(s): {'; '.join(blocked)}"
        logger.warning("guardrail.blocked", patterns=blocked, commands_preview=commands[:200])
        return {
            "approved": False,
            "reason": reason,
            "blocked_patterns": blocked,
            "agent": "Safety Guardrail Validator"
        }

    logger.info("guardrail.approved", commands_preview=commands[:200])
    return {
        "approved": True,
        "reason": "Dual-Agent Safety Guardrail: VERIFIED & APPROVED. Zero destructive or invasive commands detected.",
        "blocked_patterns": [],
        "agent": "Safety Guardrail Validator"
    }


def sanitize_commands(commands: str) -> str:
    """Si el guardrail rechaza, retorna comandos seguros alternativos."""
    validation = validate_commands(commands)
    if validation["approved"]:
        return commands
    logger.info("guardrail.sanitized", original_preview=commands[:100])
    return "# [GUARDRAIL BLOCKED] Original commands contained destructive patterns.\n# Safe fallback: inspect logs only\ndocker logs triage-nextjs --tail 100"
