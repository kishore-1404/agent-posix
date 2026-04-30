from pathlib import Path

from agentposix.core.checksum import compute_checksum
from agentposix.enums import ASOStatus, FreezeTriggerReasonEnum, ParadigmEnum
from agentposix.models.aso import AgentStateObject
from agentposix.models.environment import EnvironmentSnapshot
from agentposix.models.execution_pointer import ExecutionPointer
from agentposix.models.message import ConversationHistory
from agentposix.models.metadata import FreezeMetadata, IdentityBlock, ModelConfig
from agentposix.models.side_effect import SideEffectRegistry
from agentposix.storage.filesystem import FilesystemBackend


def make_aso(session_id: str, summary: str = "") -> AgentStateObject:
    return AgentStateObject(
        identity=IdentityBlock(aso_id=f"aso-{session_id}", session_id=session_id),
        status=ASOStatus.CHECKPOINTED,
        created_at="2026-05-01T00:00:00Z",
        human_summary=summary,
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


def test_filesystem_backend_recreates_parent_directory(tmp_path):
    base_dir = tmp_path / "nested" / "checkpoints"
    backend = FilesystemBackend(str(base_dir))
    aso = make_aso("session-1")

    base_dir.rmdir()

    backend.write_aso(aso)

    assert base_dir.exists()
    stored = backend.read_aso("session-1")
    assert stored.identity.session_id == "session-1"


def test_filesystem_backend_persists_checksum_without_mutating_input(tmp_path):
    backend = FilesystemBackend(str(tmp_path))
    aso = make_aso("session-1", summary="stable")
    original_checksum = aso.checksum

    backend.write_aso(aso)

    assert aso.checksum == original_checksum
    stored = backend.read_aso("session-1")
    assert stored.checksum == compute_checksum(stored)


def test_filesystem_backend_lists_deletes_and_checks_existence(tmp_path):
    backend = FilesystemBackend(str(tmp_path))
    backend.write_aso(make_aso("session-b"))
    backend.write_aso(make_aso("session-a"))

    assert sorted(backend.list_sessions()) == ["session-a", "session-b"]
    assert backend.exists("session-a") is True

    backend.delete_aso("session-a")

    assert backend.exists("session-a") is False
    assert sorted(backend.list_sessions()) == ["session-b"]
