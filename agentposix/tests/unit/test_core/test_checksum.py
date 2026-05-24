import pytest

from agentposix.core.checksum import compute_checksum, verify_checksum
from agentposix.enums import ASOStatus, FreezeTriggerReasonEnum, ParadigmEnum
from agentposix.exceptions import ChecksumMismatchError
from agentposix.models.aso import AgentStateObject
from agentposix.models.environment import EnvironmentSnapshot
from agentposix.models.execution_pointer import ExecutionPointer
from agentposix.models.message import ConversationHistory
from agentposix.models.metadata import FreezeMetadata, IdentityBlock, ModelConfig
from agentposix.models.side_effect import SideEffectRegistry


def make_aso() -> AgentStateObject:
    return AgentStateObject(
        identity=IdentityBlock(aso_id="aso-1", session_id="session-1"),
        status=ASOStatus.CHECKPOINTED,
        created_at="2026-05-25T00:00:00Z",
        model_config_block=ModelConfig(provider="test", model_id="test"),
        conversation=ConversationHistory(),
        execution_pointer=ExecutionPointer(paradigm=ParadigmEnum.CUSTOM),
        side_effects=SideEffectRegistry(),
        environment=EnvironmentSnapshot(cwd="/tmp", python_version="3.12", platform="linux"),
        metadata=FreezeMetadata(
            framework_name="raw",
            framework_version="1",
            trigger_reason=FreezeTriggerReasonEnum.EXPLICIT_CALL,
        ),
    )


def test_compute_checksum_is_deterministic_and_ignores_checksum_field():
    aso = make_aso()
    first = compute_checksum(aso)

    aso.checksum = "not-the-real-checksum"
    second = compute_checksum(aso)

    assert first == second
    assert len(first) == 64


def test_verify_checksum_accepts_empty_or_matching_checksum():
    aso = make_aso()

    assert verify_checksum(aso) is True

    aso.checksum = compute_checksum(aso)
    assert verify_checksum(aso) is True


def test_verify_checksum_rejects_tampered_aso():
    aso = make_aso()
    aso.checksum = compute_checksum(aso)
    aso.human_summary = "tampered"

    with pytest.raises(
        ChecksumMismatchError,
        match="ASO checksum verification failed for session session-1",
    ):
        verify_checksum(aso)
