from agentposix.enums import ASOStatus
from agentposix.exceptions import StateTransitionError
from agentposix.models.aso import AgentStateObject


ALLOWED_STATE_TRANSITIONS: dict[ASOStatus, set[ASOStatus]] = {
    ASOStatus.INITIALIZING: {
        ASOStatus.RUNNING,
        ASOStatus.CHECKPOINTING,
        ASOStatus.CHECKPOINTED,
        ASOStatus.FAILED,
        ASOStatus.TERMINATED,
    },
    ASOStatus.RUNNING: {
        ASOStatus.CHECKPOINTING,
        ASOStatus.CHECKPOINTED,
        ASOStatus.FAILED,
        ASOStatus.TERMINATED,
    },
    ASOStatus.CHECKPOINTING: {
        ASOStatus.CHECKPOINTED,
        ASOStatus.FAILED,
        ASOStatus.TERMINATED,
    },
    ASOStatus.CHECKPOINTED: {
        ASOStatus.RESUMING,
        ASOStatus.TERMINATED,
    },
    ASOStatus.RESUMING: {
        ASOStatus.RUNNING,
        ASOStatus.CHECKPOINTING,
        ASOStatus.CHECKPOINTED,
        ASOStatus.FAILED,
        ASOStatus.TERMINATED,
    },
    ASOStatus.TERMINATED: set(),
    ASOStatus.FAILED: set(),
}


def validate_state_transition(current: ASOStatus, target: ASOStatus) -> None:
    if current == target:
        raise StateTransitionError(
            f"Invalid ASO state transition: {current.value} -> {target.value}"
        )

    allowed_targets = ALLOWED_STATE_TRANSITIONS[current]
    if target not in allowed_targets:
        raise StateTransitionError(
            f"Invalid ASO state transition: {current.value} -> {target.value}"
        )


def transition_state(aso: AgentStateObject, target: ASOStatus) -> AgentStateObject:
    validate_state_transition(aso.status, target)
    aso.status = target
    return aso
