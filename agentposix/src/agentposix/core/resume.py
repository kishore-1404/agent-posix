from datetime import datetime, timezone

from agentposix.core.lifecycle import transition_state
from agentposix.core.checksum import verify_checksum
from agentposix.enums import ASOStatus
from agentposix.models.aso import AgentStateObject
from agentposix.storage.base import StorageBackend


def resume(session_id: str, storage: StorageBackend) -> AgentStateObject:
    """
    Execute the Agent POSIX Resume Protocol.

    Behavior:
    - Missing sessions raise `FileNotFoundError` with a stable session-specific message.
    - Checksum mismatches raise `ChecksumMismatchError`.
    - Sessions not in a resumable lifecycle state raise `StateTransitionError`.
    """
    if not storage.exists(session_id):
        raise FileNotFoundError(f"No ASO found for session {session_id}")

    aso = storage.read_aso(session_id)

    # Integrity validation
    verify_checksum(aso)

    # Transition state
    transition_state(aso, ASOStatus.RESUMING)
    aso.resumed_at = datetime.now(timezone.utc).isoformat()

    return aso
