import json

import aiosqlite
import pytest

from agentposix.core.checksum import verify_checksum
from agentposix.enums import ASOStatus, FreezeTriggerReasonEnum, ParadigmEnum
from agentposix.exceptions import ChecksumMismatchError, InvalidASOError
from agentposix.models.aso import AgentStateObject
from agentposix.models.environment import EnvironmentSnapshot
from agentposix.models.execution_pointer import ExecutionPointer
from agentposix.models.message import ConversationHistory
from agentposix.models.metadata import FreezeMetadata, IdentityBlock, ModelConfig
from agentposix.models.side_effect import SideEffectRegistry
from agentposix.storage.sqlite import AsyncSqliteBackend


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


@pytest.mark.asyncio
async def test_sqlite_backend_create_read_update_delete_and_exists(tmp_path):
    backend = AsyncSqliteBackend(str(tmp_path / "agentposix.db"))
    aso = make_aso("session-1", summary="initial")

    await backend.write_aso(aso)

    assert await backend.exists("session-1") is True
    stored = await backend.read_aso("session-1")
    assert stored.human_summary == "initial"
    assert stored.identity.session_id == "session-1"
    assert stored.checksum

    aso.human_summary = "updated"
    await backend.write_aso(aso)

    updated = await backend.read_aso("session-1")
    assert updated.human_summary == "updated"

    await backend.delete_aso("session-1")
    assert await backend.exists("session-1") is False
    with pytest.raises(FileNotFoundError, match="No ASO found for session session-1"):
        await backend.read_aso("session-1")


@pytest.mark.asyncio
async def test_sqlite_backend_lists_sessions_in_stable_order(tmp_path):
    backend = AsyncSqliteBackend(str(tmp_path / "agentposix.db"))

    await backend.write_aso(make_aso("session-b"))
    await backend.write_aso(make_aso("session-a"))

    assert await backend.list_sessions() == ["session-a", "session-b"]


@pytest.mark.asyncio
async def test_sqlite_backend_missing_session_behavior(tmp_path):
    backend = AsyncSqliteBackend(str(tmp_path / "agentposix.db"))

    assert await backend.exists("missing") is False
    assert await backend.list_sessions() == []
    await backend.delete_aso("missing")
    with pytest.raises(FileNotFoundError, match="No ASO found for session missing"):
        await backend.read_aso("missing")


async def insert_raw_payload(backend: AsyncSqliteBackend, session_id: str, payload: str) -> None:
    await backend._init_db()
    async with aiosqlite.connect(backend.db_path) as db:
        await db.execute(
            "INSERT INTO checkpoints (session_id, payload) VALUES (?, ?) "
            "ON CONFLICT(session_id) DO UPDATE SET payload=excluded.payload",
            (session_id, payload),
        )
        await db.commit()


@pytest.mark.asyncio
async def test_sqlite_backend_rejects_partial_json_with_actionable_error(tmp_path):
    backend = AsyncSqliteBackend(str(tmp_path / "agentposix.db"))
    await insert_raw_payload(backend, "session-1", '{"identity": ')

    with pytest.raises(InvalidASOError, match="Invalid ASO JSON for session session-1"):
        await backend.read_aso("session-1")


@pytest.mark.asyncio
async def test_sqlite_backend_rejects_unexpected_payload_shape(tmp_path):
    backend = AsyncSqliteBackend(str(tmp_path / "agentposix.db"))
    await insert_raw_payload(backend, "session-1", '{"unexpected": "payload"}')

    with pytest.raises(
        InvalidASOError,
        match="Invalid ASO payload for session session-1: schema validation failed",
    ):
        await backend.read_aso("session-1")


@pytest.mark.asyncio
async def test_sqlite_backend_invalid_checksum_is_deterministic(tmp_path):
    backend = AsyncSqliteBackend(str(tmp_path / "agentposix.db"))
    aso = make_aso("session-1", summary="stable")
    await backend.write_aso(aso)
    payload = json.loads((await backend.read_aso("session-1")).model_dump_json())
    payload["human_summary"] = "tampered"
    await insert_raw_payload(
        backend,
        "session-1",
        json.dumps(payload),
    )

    stored = await backend.read_aso("session-1")
    with pytest.raises(
        ChecksumMismatchError,
        match="ASO checksum verification failed for session session-1",
    ):
        verify_checksum(stored)
