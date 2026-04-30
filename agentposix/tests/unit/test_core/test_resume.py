import pytest

from agentposix.core.checksum import compute_checksum
from agentposix.core import host_drift
from agentposix.core.resume import resume
from agentposix.enums import ASOStatus, FreezeTriggerReasonEnum, ParadigmEnum
from agentposix.exceptions import ChecksumMismatchError, StateTransitionError
from agentposix.models.aso import AgentStateObject
from agentposix.models.environment import EnvironmentSnapshot
from agentposix.models.execution_pointer import ExecutionPointer
from agentposix.models.message import ConversationHistory
from agentposix.models.metadata import FreezeMetadata, IdentityBlock, ModelConfig
from agentposix.models.side_effect import SideEffectRegistry
from agentposix.storage.base import StorageBackend


def make_aso(status: ASOStatus = ASOStatus.CHECKPOINTED) -> AgentStateObject:
    aso = AgentStateObject(
        identity=IdentityBlock(aso_id="aso-1", session_id="session-1"),
        status=status,
        created_at="2026-05-01T00:00:00Z",
        model_config_block=ModelConfig(provider="anthropic", model_id="claude-test"),
        conversation=ConversationHistory(),
        execution_pointer=ExecutionPointer(paradigm=ParadigmEnum.CUSTOM),
        side_effects=SideEffectRegistry(),
        environment=EnvironmentSnapshot(
            cwd=host_drift._current_cwd(),
            python_version=host_drift._current_python_version(),
            platform=host_drift._current_platform(),
        ),
        metadata=FreezeMetadata(
            framework_name="raw",
            framework_version="1.0.0",
            trigger_reason=FreezeTriggerReasonEnum.EXPLICIT_CALL,
        ),
    )
    aso.checksum = compute_checksum(aso)
    return aso


class InMemoryStorage(StorageBackend):
    def __init__(self, aso: AgentStateObject | None):
        self.aso = aso

    def write_aso(self, aso: AgentStateObject) -> None:
        self.aso = aso

    def read_aso(self, session_id: str) -> AgentStateObject:
        if self.aso is None or self.aso.identity.session_id != session_id:
            raise FileNotFoundError(f"No ASO found for session {session_id}")
        return self.aso

    def list_sessions(self) -> list[str]:
        if self.aso is None:
            return []
        return [self.aso.identity.session_id]

    def delete_aso(self, session_id: str) -> None:
        if self.aso and self.aso.identity.session_id == session_id:
            self.aso = None

    def exists(self, session_id: str) -> bool:
        return self.aso is not None and self.aso.identity.session_id == session_id


def test_resume_transitions_checkpointed_session():
    storage = InMemoryStorage(make_aso())

    aso = resume("session-1", storage)

    assert aso.status is ASOStatus.RESUMING
    assert aso.resumed_at is not None


def test_resume_rejects_missing_session_cleanly():
    storage = InMemoryStorage(None)

    with pytest.raises(FileNotFoundError, match="No ASO found for session missing-session"):
        resume("missing-session", storage)


def test_resume_rejects_checksum_mismatch():
    aso = make_aso()
    aso.human_summary = "tampered after checksum"
    storage = InMemoryStorage(aso)

    with pytest.raises(ChecksumMismatchError, match="session-1"):
        resume("session-1", storage)


@pytest.mark.parametrize("status", [ASOStatus.RESUMING, ASOStatus.TERMINATED, ASOStatus.FAILED])
def test_resume_rejects_non_resumable_states(status: ASOStatus):
    storage = InMemoryStorage(make_aso(status=status))

    with pytest.raises(StateTransitionError, match=f"{status.value} -> RESUMING"):
        resume("session-1", storage)
