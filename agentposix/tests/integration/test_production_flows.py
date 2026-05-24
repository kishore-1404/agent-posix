import json
import os
import sys

import pytest
from langgraph.checkpoint.base import Checkpoint, CheckpointMetadata

from agentposix.adapters.langgraph.adapter import ASOLangGraphSaver
from agentposix.core.freeze import freeze
from agentposix.core.resume import resume
from agentposix.enums import ASOStatus, FreezeTriggerReasonEnum, ParadigmEnum
from agentposix.exceptions import ChecksumMismatchError
from agentposix.models.aso import AgentStateObject
from agentposix.models.environment import EnvironmentSnapshot
from agentposix.models.execution_pointer import ExecutionPointer
from agentposix.models.message import ConversationHistory
from agentposix.models.metadata import FreezeMetadata, IdentityBlock, ModelConfig
from agentposix.models.side_effect import SideEffectRegistry
from agentposix.storage.filesystem import FilesystemBackend
from agentposix.storage.sqlite import AsyncSqliteBackend


def make_aso(
    session_id: str = "session-1",
    status: ASOStatus = ASOStatus.RUNNING,
) -> AgentStateObject:
    return AgentStateObject(
        identity=IdentityBlock(aso_id=f"aso-{session_id}", session_id=session_id),
        status=status,
        created_at="2026-05-25T00:00:00Z",
        model_config_block=ModelConfig(provider="test", model_id="test"),
        conversation=ConversationHistory(),
        execution_pointer=ExecutionPointer(paradigm=ParadigmEnum.CUSTOM),
        side_effects=SideEffectRegistry(),
        environment=EnvironmentSnapshot(
            cwd=os.getcwd(),
            python_version=sys.version.split()[0],
            platform=sys.platform,
        ),
        metadata=FreezeMetadata(
            framework_name="raw",
            framework_version="1",
            trigger_reason=FreezeTriggerReasonEnum.EXPLICIT_CALL,
        ),
    )


def make_checkpoint() -> Checkpoint:
    return {
        "v": 2,
        "id": "checkpoint-2",
        "ts": "2026-05-25T00:00:00+00:00",
        "channel_values": {"messages": ["hello"], "route": "agent"},
        "channel_versions": {"messages": "0002", "route": "0001"},
        "versions_seen": {"agent": {"messages": "0001"}},
        "pending_sends": [],
        "updated_channels": ["messages"],
        "next": ["agent"],
    }


def make_metadata() -> CheckpointMetadata:
    return {
        "source": "loop",
        "step": 2,
        "parents": {},
        "run_id": "run-1",
        "writes": {"planner": {"route": "agent"}},
    }


def test_freeze_persist_resume_filesystem_flow(tmp_path):
    backend = FilesystemBackend(str(tmp_path))
    aso = make_aso()

    frozen = freeze(aso, backend, summary="integration checkpoint")
    restored = resume("session-1", backend)

    assert frozen.status == ASOStatus.CHECKPOINTED
    assert restored.status == ASOStatus.RESUMING
    assert restored.human_summary == "integration checkpoint"
    assert restored.checksum == frozen.checksum


def test_resume_rejects_tampered_filesystem_checkpoint(tmp_path):
    backend = FilesystemBackend(str(tmp_path))
    frozen = freeze(make_aso(), backend, summary="integration checkpoint")
    path = backend._get_path(frozen.identity.session_id)
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["human_summary"] = "tampered"
    path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ChecksumMismatchError):
        resume("session-1", backend)


@pytest.mark.asyncio
async def test_filesystem_and_sqlite_backend_parity(tmp_path):
    filesystem = FilesystemBackend(str(tmp_path / "checkpoints"))
    sqlite = AsyncSqliteBackend(str(tmp_path / "checkpoints.db"))
    aso = make_aso(status=ASOStatus.CHECKPOINTED)

    filesystem.write_aso(aso)
    await sqlite.write_aso(aso)

    filesystem_read = filesystem.read_aso("session-1")
    sqlite_read = await sqlite.read_aso("session-1")

    assert filesystem_read.model_dump(mode="json") == sqlite_read.model_dump(mode="json")
    assert filesystem.exists("session-1") is True
    assert await sqlite.exists("session-1") is True
    assert filesystem.list_sessions() == await sqlite.list_sessions()


def test_langgraph_checkpoint_round_trip_integration(tmp_path):
    saver = ASOLangGraphSaver(FilesystemBackend(str(tmp_path)))
    config = {
        "configurable": {
            "thread_id": "thread-1",
            "checkpoint_ns": "main",
            "checkpoint_id": "checkpoint-1",
        }
    }
    checkpoint = make_checkpoint()
    metadata = make_metadata()

    saved_config = saver.put(config, checkpoint, metadata, {"messages": "0002"})
    restored = saver.get_tuple(saved_config)

    assert restored is not None
    assert saved_config["configurable"]["thread_id"] == "thread-1"
    assert saved_config["configurable"]["checkpoint_id"] == "checkpoint-2"
    assert restored.checkpoint == checkpoint
    assert restored.metadata == metadata
    assert restored.parent_config == config
