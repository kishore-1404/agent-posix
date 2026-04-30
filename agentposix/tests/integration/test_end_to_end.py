import os

import pytest

from agentposix import AgentStateObject, FilesystemBackend, checkpoint_boundary
from agentposix.enums import FreezeTriggerReasonEnum, ParadigmEnum
from agentposix.models.environment import EnvironmentSnapshot
from agentposix.models.execution_pointer import ExecutionPointer
from agentposix.models.message import ConversationHistory
from agentposix.models.metadata import FreezeMetadata, IdentityBlock, ModelConfig
from agentposix.models.side_effect import SideEffectRegistry


def test_idempotency_skip_on_resume(tmp_path):
    storage = FilesystemBackend(str(tmp_path))
    aso = AgentStateObject(
        identity=IdentityBlock(aso_id="test1", session_id="test_session"),
        created_at="2026-04-30T00:00:00Z",
        model_config_block=ModelConfig(provider="test", model_id="test"),
        conversation=ConversationHistory(),
        execution_pointer=ExecutionPointer(paradigm=ParadigmEnum.CUSTOM),
        side_effects=SideEffectRegistry(),
        environment=EnvironmentSnapshot(cwd="/", python_version="3.10", platform="linux"),
        metadata=FreezeMetadata(
            framework_name="raw",
            framework_version="1",
            trigger_reason=FreezeTriggerReasonEnum.EXPLICIT_CALL,
        ),
    )

    call_count = 0

    @checkpoint_boundary(aso, storage, "charge_card")
    def charge_card(amount: int):
        nonlocal call_count
        call_count += 1
        return {"status": "success", "amount": amount}

    # Run 1
    res1 = charge_card(amount=100)
    assert res1["status"] == "success"
    assert call_count == 1
    assert len(aso.side_effects.entries) == 1

    # Run 2 (Simulating a resume where the decorator executes again)
    res2 = charge_card(amount=100)
    assert res2["status"] == "success"
    assert call_count == 1  # Execution bypassed!
    assert len(aso.side_effects.entries) == 1
