"""Worker registry. Add or remove workers here — the supervisor adapts automatically.
WORKERS maps a worker name to its node (a callable used as a LangGraph node).
"""

from __future__ import annotations

from src.agent.workers import triage, investigator, remediator, communicator, postmortem_writer

WORKERS: dict = {
    "triage": triage.build(),
    "investigator": investigator.build(),
    "remediator": remediator.build(),
    "communicator": communicator.build(),
    "postmortem_writer": postmortem_writer.build(),
}

__all__ = ["WORKERS"]
