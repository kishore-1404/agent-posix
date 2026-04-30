import pytest

from agentposix.core.lifecycle import (
    ALLOWED_STATE_TRANSITIONS,
    transition_state,
    validate_state_transition,
)
from agentposix.enums import ASOStatus, FreezeTriggerReasonEnum, ParadigmEnum
from agentposix.exceptions import StateTransitionError
from agentposix.models.aso import AgentStateObject
from agentposix.models.environment import EnvironmentSnapshot
from agentposix.models.execution_pointer import ExecutionPointer
from agentposix.models.message import ConversationHistory
from agentposix.models.metadata import FreezeMetadata, IdentityBlock, ModelConfig
from agentposix.models.side_effect import SideEffectRegistry


def make_aso(status: ASOStatus = ASOStatus.INITIALIZING) -> AgentStateObject:
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


@pytest.mark.parametrize(
    ("current", "target"),
    [
        (current, target)
        for current, targets in ALLOWED_STATE_TRANSITIONS.items()
        for target in sorted(targets, key=lambda value: value.value)
    ],
)
def test_validate_state_transition_accepts_allowed_transitions(
    current: ASOStatus, target: ASOStatus
):
    validate_state_transition(current, target)


@pytest.mark.parametrize(
    ("current", "target"),
    [
        (ASOStatus.CHECKPOINTED, ASOStatus.RUNNING),
        (ASOStatus.TERMINATED, ASOStatus.RESUMING),
        (ASOStatus.FAILED, ASOStatus.CHECKPOINTED),
        (ASOStatus.RUNNING, ASOStatus.RUNNING),
    ],
)
def test_validate_state_transition_rejects_invalid_transitions(
    current: ASOStatus, target: ASOStatus
):
    with pytest.raises(StateTransitionError, match=f"{current.value} -> {target.value}"):
        validate_state_transition(current, target)


def test_transition_state_updates_aso_status_for_allowed_transition():
    aso = make_aso(status=ASOStatus.RUNNING)

    transition_state(aso, ASOStatus.CHECKPOINTED)

    assert aso.status is ASOStatus.CHECKPOINTED


def test_transition_state_preserves_status_for_invalid_transition():
    aso = make_aso(status=ASOStatus.TERMINATED)

    with pytest.raises(StateTransitionError, match="TERMINATED -> RESUMING"):
        transition_state(aso, ASOStatus.RESUMING)

    assert aso.status is ASOStatus.TERMINATED
