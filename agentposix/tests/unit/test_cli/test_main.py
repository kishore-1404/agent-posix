import json
import os
import sys

from click.testing import CliRunner

from agentposix.cli.main import app
from agentposix.enums import ASOStatus, FreezeTriggerReasonEnum, ParadigmEnum
from agentposix.models.aso import AgentStateObject
from agentposix.models.environment import EnvironmentSnapshot
from agentposix.models.execution_pointer import ExecutionPointer
from agentposix.models.message import ConversationHistory
from agentposix.models.metadata import FreezeMetadata, IdentityBlock, ModelConfig
from agentposix.models.side_effect import SideEffectRegistry
from agentposix.storage.filesystem import FilesystemBackend


def make_checkpointed_aso(session_id: str) -> AgentStateObject:
    return AgentStateObject(
        identity=IdentityBlock(aso_id=f"aso-{session_id}", session_id=session_id),
        status=ASOStatus.CHECKPOINTED,
        created_at="2026-05-25T00:00:00Z",
        frozen_at="2026-05-25T00:01:00Z",
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


def make_initializing_aso(session_id: str) -> AgentStateObject:
    aso = make_checkpointed_aso(session_id)
    aso.status = ASOStatus.INITIALIZING
    aso.frozen_at = None
    return aso


def test_resume_cli_prints_status_timestamps_and_checksum(tmp_path):
    backend = FilesystemBackend(str(tmp_path))
    backend.write_aso(make_checkpointed_aso("session-1"))
    runner = CliRunner()

    result = runner.invoke(app, ["resume", "session-1", "--path", str(tmp_path)])

    assert result.exit_code == 0
    assert "Resumed ASO: session-1" in result.output
    assert "Status: RESUMING" in result.output
    assert "Frozen At: 2026-05-25T00:01:00Z" in result.output
    assert "Resumed At:" in result.output
    assert "Checksum: valid" in result.output


def test_resume_cli_reports_missing_session(tmp_path):
    runner = CliRunner()

    result = runner.invoke(app, ["resume", "missing", "--path", str(tmp_path)])

    assert result.exit_code == 1
    assert "Error resuming ASO:" in result.output
    assert "No ASO found for session missing" in result.output


def test_freeze_cli_persists_aso_from_json_input(tmp_path):
    input_path = tmp_path / "input.aso.json"
    storage_path = tmp_path / "storage"
    aso = make_initializing_aso("session-1")
    input_path.write_text(
        json.dumps(aso.model_dump(mode="json")),
        encoding="utf-8",
    )
    runner = CliRunner()

    result = runner.invoke(
        app,
        [
            "freeze",
            "--input",
            str(input_path),
            "--path",
            str(storage_path),
            "--summary",
            "manual checkpoint",
        ],
    )

    assert result.exit_code == 0
    assert "Frozen ASO: session-1" in result.output
    assert "Status: CHECKPOINTED" in result.output
    assert "Frozen At:" in result.output
    assert "Checksum:" in result.output
    assert "Summary: manual checkpoint" in result.output

    stored = FilesystemBackend(str(storage_path)).read_aso("session-1")
    assert stored.status == ASOStatus.CHECKPOINTED
    assert stored.human_summary == "manual checkpoint"
    assert stored.checksum


def test_freeze_cli_reports_invalid_json_input(tmp_path):
    input_path = tmp_path / "input.aso.json"
    input_path.write_text("{", encoding="utf-8")
    runner = CliRunner()

    result = runner.invoke(app, ["freeze", "--input", str(input_path)])

    assert result.exit_code == 1
    assert "Error freezing ASO:" in result.output
