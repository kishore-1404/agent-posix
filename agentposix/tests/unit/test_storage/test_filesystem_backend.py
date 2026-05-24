import json

import pytest

from agentposix.core.checksum import compute_checksum, verify_checksum
from agentposix.enums import ASOStatus, FreezeTriggerReasonEnum, ParadigmEnum
from agentposix.exceptions import ChecksumMismatchError, InvalidASOError
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


def test_filesystem_backend_rejects_partial_json_with_actionable_error(tmp_path):
    backend = FilesystemBackend(str(tmp_path))
    backend._get_path("session-1").write_text('{"identity": ', encoding="utf-8")

    with pytest.raises(InvalidASOError, match="Invalid ASO JSON for session session-1"):
        backend.read_aso("session-1")


def test_filesystem_backend_rejects_unexpected_payload_shape(tmp_path):
    backend = FilesystemBackend(str(tmp_path))
    backend._get_path("session-1").write_text(
        json.dumps({"unexpected": "payload"}),
        encoding="utf-8",
    )

    with pytest.raises(
        InvalidASOError,
        match="Invalid ASO payload for session session-1: schema validation failed",
    ):
        backend.read_aso("session-1")


def test_filesystem_backend_reports_unreadable_payload_path(tmp_path):
    backend = FilesystemBackend(str(tmp_path))
    backend._get_path("session-1").mkdir()

    with pytest.raises(InvalidASOError, match="Unable to read ASO for session session-1"):
        backend.read_aso("session-1")


def test_filesystem_backend_invalid_checksum_is_deterministic(tmp_path):
    backend = FilesystemBackend(str(tmp_path))
    aso = make_aso("session-1", summary="stable")
    backend.write_aso(aso)

    path = backend._get_path("session-1")
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["human_summary"] = "tampered"
    path.write_text(json.dumps(payload), encoding="utf-8")

    stored = backend.read_aso("session-1")
    with pytest.raises(
        ChecksumMismatchError,
        match="ASO checksum verification failed for session session-1",
    ):
        verify_checksum(stored)
