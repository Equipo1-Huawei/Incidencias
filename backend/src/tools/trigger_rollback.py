"""Trigger a rollback — this is a GATED action. It does NOT execute immediately.
Instead it returns a proposal that the remediator writes to pending_approval.
The actual execution only happens after a human approves via POST /approve.
"""

from langchain_core.tools import tool


@tool
def trigger_rollback(service: str, deploy_id: str = "") -> str:
    """Propose a rollback for the given service to the previous deployment.
    This action requires human approval before execution — it is safe to call
    to generate the proposal, but it will NOT execute until approved.
    """
    return (
        f"PROPOSED ACTION (requires approval): rollback service '{service}' "
        f"to previous deployment{f' (before {deploy_id})' if deploy_id else ''}. "
        f"Impact: service will restart with prior version, ~2s downtime. "
        f"This action is reversible."
    )


@tool
def restart_service(service: str) -> str:
    """Propose a restart of the given service. Requires human approval.
    """
    return (
        f"PROPOSED ACTION (requires approval): restart service '{service}'. "
        f"Impact: ~1.8s downtime, in-flight requests will be retried. "
        f"This action is reversible."
    )
