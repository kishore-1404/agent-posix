import pytest
from pydantic import ValidationError

from agentposix.enums import ASOStatus, FreezeTriggerReasonEnum, ParadigmEnum
from agentposix.models.aso import AgentStateObject
from agentposix.models.environment import EnvironmentSnapshot, SubAgentReference
from agentposix.models.execution_pointer import ExecutionPointer
from agentposix.models.message import ConversationHistory, Message, ToolCall, ToolDefinition
from agentposix.models.metadata import FreezeMetadata, IdentityBlock, ModelConfig
from agentposix.models.side_effect import SideEffectEntry, SideEffectRegistry


def make_valid_aso_payload() -> dict:
    return {
        "identity": {"aso_id": "aso-1", "session_id": "session-1"},
        "created_at": "2026-05-01T00:00:00Z",
        "model_config_block": {"provider": "anthropic", "model_id": "claude-test"},
        "conversation": {},
        "execution_pointer": {},
        "side_effects": {},
        "environment": {
            "cwd": "/tmp",
            "python_version": "3.12.9",
            "platform": "linux",
        },
        "metadata": {
            "framework_name": "langgraph",
            "framework_version": "1.0.0",
            "trigger_reason": "EXPLICIT_CALL",
        },
    }


def test_metadata_models_apply_expected_defaults():
    model_config = ModelConfig(provider="anthropic", model_id="claude-test")
    metadata = FreezeMetadata(
        framework_name="langgraph",
        framework_version="1.0.0",
        trigger_reason=FreezeTriggerReasonEnum.EXPLICIT_CALL,
    )
    identity = IdentityBlock(aso_id="aso-1", session_id="session-1")

    assert model_config.temperature == 0.0
    assert metadata.agentposix_version == "0.1.0"
    assert identity.parent_session_id is None


def test_message_models_apply_expected_defaults():
    tool_call = ToolCall(id="call-1", function={"name": "search", "arguments": {}})
    message = Message(role="assistant", tool_calls=[tool_call])
    history = ConversationHistory()
    tool_definition = ToolDefinition(name="search")

    assert tool_call.type == "function"
    assert message.content is None
    assert history.messages == []
    assert history.message_count == 0
    assert tool_definition.input_schema == {}
    assert tool_definition.idempotent is False


def test_execution_and_environment_models_apply_expected_defaults():
    pointer = ExecutionPointer()
    environment = EnvironmentSnapshot(cwd="/tmp", python_version="3.12.9", platform="linux")

    assert pointer.paradigm is ParadigmEnum.CUSTOM
    assert pointer.completed_node_ids == []
    assert pointer.pending_node_ids == []
    assert pointer.loop_iteration_count == 0
    assert environment.env_vars == {}
    assert environment.file_checksums == {}
    assert environment.git_commit_hash == ""


def test_side_effect_models_apply_expected_defaults():
    registry = SideEffectRegistry()
    entry = SideEffectEntry(
        idempotency_key="a" * 64,
        tool_name="charge_card",
        tool_args={"amount": 100},
        executed_at="2026-05-01T00:00:00Z",
    )

    assert registry.entries == []
    assert entry.result_summary is None
    assert entry.is_reversible is False
    assert entry.replay_safe is False


def test_side_effect_entry_rejects_bad_idempotency_key():
    with pytest.raises(ValidationError, match="Idempotency key"):
        SideEffectEntry(
            idempotency_key="not-a-sha256",
            tool_name="charge_card",
            tool_args={},
            executed_at="2026-05-01T00:00:00Z",
        )


def test_sub_agent_reference_rejects_invalid_status_enum():
    with pytest.raises(ValidationError, match="status"):
        SubAgentReference(
            session_id="child-session",
            status="PAUSED",
            aso_file_path="/tmp/child.json",
        )


def test_execution_pointer_rejects_invalid_paradigm_enum():
    with pytest.raises(ValidationError, match="paradigm"):
        ExecutionPointer(paradigm="PIPELINE")


def test_agent_state_object_requires_required_blocks():
    payload = make_valid_aso_payload()
    del payload["metadata"]
    del payload["environment"]

    with pytest.raises(ValidationError) as exc_info:
        AgentStateObject(**payload)

    error_fields = {error["loc"][0] for error in exc_info.value.errors()}
    assert {"metadata", "environment"} <= error_fields


def test_agent_state_object_accepts_valid_minimal_payload():
    aso = AgentStateObject(**make_valid_aso_payload())

    assert aso.spec_version == "1.0.0"
    assert aso.status is ASOStatus.INITIALIZING
    assert aso.human_summary == ""
    assert aso.tool_registry == []
    assert aso.sub_agents == []
    assert aso.extensions == {}
    assert aso.checksum == ""
