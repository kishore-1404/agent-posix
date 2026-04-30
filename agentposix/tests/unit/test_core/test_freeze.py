from agentposix.core.checksum import compute_checksum
from agentposix.core.freeze import freeze
from agentposix.enums import ASOStatus, FreezeTriggerReasonEnum, ParadigmEnum
from agentposix.models.aso import AgentStateObject
from agentposix.models.environment import EnvironmentSnapshot
from agentposix.models.execution_pointer import ExecutionPointer
from agentposix.models.message import ConversationHistory
from agentposix.models.metadata import FreezeMetadata, IdentityBlock, ModelConfig
from agentposix.models.side_effect import SideEffectRegistry
from agentposix.storage.base import StorageBackend


def make_aso(status: ASOStatus = ASOStatus.RUNNING) -> AgentStateObject:
    return AgentStateObject(
        identity=IdentityBlock(aso_id="aso-1", session_id="session-1"),
        status=status,
        created_at="2026-05-01T00:00:00Z",
        model_config_block=ModelConfig(provider="anthropic", model_id="claude-test"),
        conversation=ConversationHistory(),
        execution_pointer=ExecutionPointer(paradigm=ParadigmEnum.CUSTOM),
        side_effects=SideEffectRegistry(),
        environment=EnvironmentSnapshot(cwd="/tmp", python_version="3.12.9", platform="linux"),
        metadata=FreezeMetadata(
            framework_name="raw",
            framework_version="1.0.0",
            trigger_reason=FreezeTriggerReasonEnum.EXPLICIT_CALL,
        ),
    )


class CapturingStorage(StorageBackend):
    def __init__(self):
        self.written_aso = None

    def write_aso(self, aso: AgentStateObject) -> None:
        self.written_aso = aso

    def read_aso(self, session_id: str) -> AgentStateObject:
        raise NotImplementedError

    def list_sessions(self) -> list[str]:
        raise NotImplementedError

    def delete_aso(self, session_id: str) -> None:
        raise NotImplementedError

    def exists(self, session_id: str) -> bool:
        raise NotImplementedError


class FailingStorage(CapturingStorage):
    def write_aso(self, aso: AgentStateObject) -> None:
        self.written_aso = aso
        raise OSError("simulated persistence failure")


def test_freeze_updates_state_after_successful_write():
    aso = make_aso()
    storage = CapturingStorage()

    result = freeze(aso, storage, summary="checkpoint complete")

    assert result is aso
    assert aso.status is ASOStatus.CHECKPOINTED
    assert aso.human_summary == "checkpoint complete"
    assert aso.frozen_at is not None
    assert aso.checksum == compute_checksum(aso)
    assert storage.written_aso is not aso
    assert storage.written_aso.status is ASOStatus.CHECKPOINTED
    assert storage.written_aso.checksum == compute_checksum(storage.written_aso)


def test_freeze_leaves_input_unchanged_when_storage_write_fails():
    aso = make_aso()
    original_checksum = aso.checksum
    original_status = aso.status
    original_summary = aso.human_summary
    storage = FailingStorage()

    try:
        freeze(aso, storage, summary="should not persist")
    except OSError as exc:
        assert str(exc) == "simulated persistence failure"
    else:
        raise AssertionError("freeze should propagate storage failures")

    assert aso.status is original_status
    assert aso.human_summary == original_summary
    assert aso.frozen_at is None
    assert aso.checksum == original_checksum
    assert storage.written_aso.status is ASOStatus.CHECKPOINTED
    assert storage.written_aso.human_summary == "should not persist"
    assert storage.written_aso.checksum == compute_checksum(storage.written_aso)
