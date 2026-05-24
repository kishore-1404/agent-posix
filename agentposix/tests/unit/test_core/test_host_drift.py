from agentposix.core import host_drift
from agentposix.core.checksum import compute_checksum
from agentposix.core.freeze import freeze
from agentposix.core.resume import resume
from agentposix.enums import ASOStatus, FreezeTriggerReasonEnum, ParadigmEnum
from agentposix.exceptions import HostDriftError
from agentposix.models.aso import AgentStateObject
from agentposix.models.environment import EnvironmentSnapshot
from agentposix.models.execution_pointer import ExecutionPointer
from agentposix.models.message import ConversationHistory
from agentposix.models.metadata import FreezeMetadata, IdentityBlock, ModelConfig
from agentposix.models.side_effect import SideEffectRegistry
from agentposix.storage.base import StorageBackend


def make_aso(environment: EnvironmentSnapshot | None = None) -> AgentStateObject:
    return AgentStateObject(
        identity=IdentityBlock(aso_id="aso-1", session_id="session-1"),
        status=ASOStatus.RUNNING,
        created_at="2026-05-01T00:00:00Z",
        model_config_block=ModelConfig(provider="anthropic", model_id="claude-test"),
        conversation=ConversationHistory(),
        execution_pointer=ExecutionPointer(paradigm=ParadigmEnum.CUSTOM),
        side_effects=SideEffectRegistry(),
        environment=environment
        or EnvironmentSnapshot(cwd="/tmp", python_version="3.12.9", platform="linux"),
        metadata=FreezeMetadata(
            framework_name="raw",
            framework_version="1.0.0",
            trigger_reason=FreezeTriggerReasonEnum.EXPLICIT_CALL,
        ),
    )


class InMemoryStorage(StorageBackend):
    def __init__(self):
        self.aso: AgentStateObject | None = None

    def write_aso(self, aso: AgentStateObject) -> None:
        self.aso = aso

    def read_aso(self, session_id: str) -> AgentStateObject:
        if self.aso is None or self.aso.identity.session_id != session_id:
            raise FileNotFoundError(f"No ASO found for session {session_id}")
        return self.aso

    def list_sessions(self) -> list[str]:
        if self.aso is None:
            return []
        return [self.aso.identity.session_id]

    def delete_aso(self, session_id: str) -> None:
        self.aso = None

    def exists(self, session_id: str) -> bool:
        return self.aso is not None and self.aso.identity.session_id == session_id


def test_freeze_captures_tracked_environment_state(tmp_path, monkeypatch):
    tracked_file = tmp_path / "tracked.txt"
    tracked_file.write_text("initial", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("AGENTPOSIX_MODE", "prod")

    aso = make_aso(
        EnvironmentSnapshot(
            cwd="/stale",
            python_version="0",
            platform="unknown",
            env_vars={"AGENTPOSIX_MODE": ""},
            file_checksums={str(tracked_file): ""},
        )
    )
    storage = InMemoryStorage()

    freeze(aso, storage)

    assert aso.environment.cwd == str(tmp_path)
    assert aso.environment.env_vars["AGENTPOSIX_MODE"] == "prod"
    assert aso.environment.file_checksums[str(tracked_file)] == host_drift._current_file_checksum(
        str(tracked_file)
    )


def test_resume_rejects_tracked_file_drift(tmp_path, monkeypatch):
    tracked_file = tmp_path / "tracked.txt"
    tracked_file.write_text("initial", encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    storage = InMemoryStorage()
    aso = make_aso(
        EnvironmentSnapshot(
            cwd=str(tmp_path),
            python_version=host_drift._current_python_version(),
            platform=host_drift._current_platform(),
            file_checksums={
                str(tracked_file): host_drift._current_file_checksum(str(tracked_file))
            },
        )
    )
    aso.status = ASOStatus.CHECKPOINTED
    aso.checksum = compute_checksum(aso)
    storage.aso = aso

    tracked_file.write_text("modified", encoding="utf-8")

    try:
        resume("session-1", storage)
    except HostDriftError as exc:
        assert str(tracked_file) in str(exc)
    else:
        raise AssertionError("resume should reject tracked file drift")


def test_resume_surfaces_environment_variable_drift_as_advisory(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("AGENTPOSIX_MODE", "staging")

    aso = make_aso(
        EnvironmentSnapshot(
            cwd=str(tmp_path),
            python_version=host_drift._current_python_version(),
            platform=host_drift._current_platform(),
            env_vars={"AGENTPOSIX_MODE": "prod"},
        )
    )
    aso.status = ASOStatus.CHECKPOINTED
    aso.checksum = compute_checksum(aso)
    storage = InMemoryStorage()
    storage.aso = aso

    resumed = resume("session-1", storage)

    assert resumed.status is ASOStatus.RESUMING
    assert resumed.extensions["resume_advisories"] == [
        "environment variable changed: AGENTPOSIX_MODE"
    ]
