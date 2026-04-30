from datetime import datetime, timezone

from agentposix.core.checksum import compute_checksum
from agentposix.core.lifecycle import transition_state
from agentposix.enums import ASOStatus
from agentposix.models.aso import AgentStateObject
from agentposix.storage.base import StorageBackend


def freeze(aso: AgentStateObject, storage: StorageBackend, summary: str = "") -> AgentStateObject:
    """
    Execute the Agent POSIX Freeze Protocol.

    The persisted ASO is prepared on a deep copy first so failed storage writes do not
    leave the caller's in-memory ASO half-transitioned. The checksum is computed only
    after final checkpoint fields are populated and before the storage backend is asked
    to persist the payload.

    Atomicity guarantees:
    - On storage write failure, the caller's in-memory ASO is left unchanged.
    - Persisted checkpoint contents are immutable for the duration of a single write call.

    Atomicity limits:
    - End-to-end durability depends on the storage backend implementation.
    - This function does not provide cross-process locking or distributed transactions.
    """
    persisted_aso = aso.model_copy(deep=True)
    transition_state(persisted_aso, ASOStatus.CHECKPOINTED)
    persisted_aso.frozen_at = datetime.now(timezone.utc).isoformat()
    if summary:
        persisted_aso.human_summary = summary

    # Finalize checksum after all persisted checkpoint fields are stable.
    persisted_aso.checksum = compute_checksum(persisted_aso)

    storage.write_aso(persisted_aso)

    aso.status = persisted_aso.status
    aso.frozen_at = persisted_aso.frozen_at
    aso.human_summary = persisted_aso.human_summary
    aso.checksum = persisted_aso.checksum
    return aso
