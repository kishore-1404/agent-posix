from datetime import datetime, timezone

from src.agentposix.core.checksum import compute_checksum
from src.agentposix.enums import ASOStatus
from src.agentposix.models.aso import AgentStateObject
from src.agentposix.storage.base import StorageBackend


def freeze(aso: AgentStateObject, storage: StorageBackend, summary: str = "") -> AgentStateObject:
    """
    Executes the Agent POSIX Freeze Protocol.
    Sets the status to CHECKPOINTED, computes checksum, and writes to storage.
    """
    aso.status = ASOStatus.CHECKPOINTED
    aso.frozen_at = datetime.now(timezone.utc).isoformat()
    if summary:
        aso.human_summary = summary

    # Finalize checksum
    aso.checksum = compute_checksum(aso)

    # Atomic write to storage
    storage.write_aso(aso)
    return aso
