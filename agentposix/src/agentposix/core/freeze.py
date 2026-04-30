from datetime import datetime, timezone

from agentposix.core.checksum import compute_checksum
from agentposix.core.lifecycle import transition_state
from agentposix.enums import ASOStatus
from agentposix.models.aso import AgentStateObject
from agentposix.storage.base import StorageBackend


def freeze(aso: AgentStateObject, storage: StorageBackend, summary: str = "") -> AgentStateObject:
    """
    Executes the Agent POSIX Freeze Protocol.
    Sets the status to CHECKPOINTED, computes checksum, and writes to storage.
    """
    transition_state(aso, ASOStatus.CHECKPOINTED)
    aso.frozen_at = datetime.now(timezone.utc).isoformat()
    if summary:
        aso.human_summary = summary

    # Finalize checksum
    aso.checksum = compute_checksum(aso)

    # Atomic write to storage
    storage.write_aso(aso)
    return aso
