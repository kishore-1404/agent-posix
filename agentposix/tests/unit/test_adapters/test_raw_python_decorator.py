import pytest

from agentposix.adapters.raw_python.decorator import checkpoint_boundary
from agentposix.enums import ASOStatus, FreezeTriggerReasonEnum, ParadigmEnum
from agentposix.exceptions import SideEffectReplayError
from agentposix.models.aso import AgentStateObject
from agentposix.models.environment import EnvironmentSnapshot
from agentposix.models.execution_pointer import ExecutionPointer
from agentposix.models.message import ConversationHistory
from agentposix.models.metadata import FreezeMetadata, IdentityBlock, ModelConfig
from agentposix.models.side_effect import SideEffectRegistry
from agentposix.storage.filesystem import FilesystemBackend


def make_aso(session_id: str = "session-1") -> AgentStateObject:
    return AgentStateObject(
        identity=IdentityBlock(aso_id=f"aso-{session_id}", session_id=session_id),
        created_at="2026-05-24T00:00:00Z",
        model_config_block=ModelConfig(provider="test", model_id="test"),
        conversation=ConversationHistory(),
        execution_pointer=ExecutionPointer(paradigm=ParadigmEnum.CUSTOM),
        side_effects=SideEffectRegistry(),
        environment=EnvironmentSnapshot(cwd="/", python_version="3.12", platform="linux"),
        metadata=FreezeMetadata(
            framework_name="raw",
            framework_version="1",
            trigger_reason=FreezeTriggerReasonEnum.EXPLICIT_CALL,
        ),
    )


def test_checkpoint_boundary_includes_positional_args_in_idempotency_key(tmp_path):
    aso = make_aso()
    storage = FilesystemBackend(str(tmp_path))
    call_count = 0

    @checkpoint_boundary(aso, storage, "charge_card")
    def charge_card(amount: int, currency: str = "USD") -> dict[str, object]:
        nonlocal call_count
        call_count += 1
        return {"status": "success", "amount": amount, "currency": currency}

    first = charge_card(100, currency="USD")
    second = charge_card(100, currency="USD")

    assert first == second
    assert call_count == 1
    assert len(aso.side_effects.entries) == 1
    assert aso.side_effects.entries[0].tool_args == {
        "args": [100],
        "kwargs": {"currency": "USD"},
    }


def test_checkpoint_boundary_distinguishes_different_positional_args(tmp_path):
    aso = make_aso()
    storage = FilesystemBackend(str(tmp_path))
    call_count = 0

    @checkpoint_boundary(aso, storage, "charge_card")
    def charge_card(amount: int) -> dict[str, object]:
        nonlocal call_count
        call_count += 1
        return {"status": "success", "amount": amount}

    assert charge_card(100)["amount"] == 100
    aso.status = ASOStatus.RUNNING

    assert charge_card(200)["amount"] == 200
    assert call_count == 2
    assert len(aso.side_effects.entries) == 2
    assert aso.side_effects.entries[0].idempotency_key != (
        aso.side_effects.entries[1].idempotency_key
    )


def test_checkpoint_boundary_does_not_reexecute_non_json_result(tmp_path):
    aso = make_aso()
    storage = FilesystemBackend(str(tmp_path))
    call_count = 0

    class NonJsonResult:
        pass

    @checkpoint_boundary(aso, storage, "create_resource")
    def create_resource() -> NonJsonResult:
        nonlocal call_count
        call_count += 1
        return NonJsonResult()

    result = create_resource()

    assert isinstance(result, NonJsonResult)
    assert call_count == 1
    with pytest.raises(
        SideEffectReplayError,
        match="result is not JSON-replayable",
    ):
        create_resource()
    assert call_count == 1
