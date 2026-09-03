"""Worker registry. Add or remove workers here — the supervisor adapts automatically."""
from __future__ import annotations

from src.agent.workers import triage, threat_intel, forensics, containment, communicator, reporter

WORKERS: dict = {
    "triage": triage.build(),
    "threat_intel": threat_intel.build(),
    "forensics": forensics.build(),
    "containment": containment.build(),
    "communicator": communicator.build(),
    "reporter": reporter.build(),
}

__all__ = ["WORKERS"]
