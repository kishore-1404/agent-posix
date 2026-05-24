import signal

import pytest

from agentposix.enums import ASOStatus, FreezeTriggerReasonEnum, ParadigmEnum
from agentposix.models.aso import AgentStateObject
from agentposix.models.environment import EnvironmentSnapshot
from agentposix.models.execution_pointer import ExecutionPointer
from agentposix.models.message import ConversationHistory
from agentposix.models.metadata import FreezeMetadata, IdentityBlock, ModelConfig
from agentposix.models.side_effect import SideEffectRegistry
from agentposix.signals.handler import FreezeSignalHandler
from agentposix.storage.base import StorageBackend


def make_aso() -> AgentStateObject:
    return AgentStateObject(
        identity=IdentityBlock(aso_id="aso-1", session_id="session-1"),
        status=ASOStatus.RUNNING,
        created_at="2026-05-25T00:00:00Z",
        model_config_block=ModelConfig(provider="test", model_id="test"),
        conversation=ConversationHistory(),
        execution_pointer=ExecutionPointer(paradigm=ParadigmEnum.CUSTOM),
        side_effects=SideEffectRegistry(),
        environment=EnvironmentSnapshot(cwd="/tmp", python_version="3.12", platform="linux"),
        metadata=FreezeMetadata(
            framework_name="raw",
            framework_version="1",
            trigger_reason=FreezeTriggerReasonEnum.EXPLICIT_CALL,
        ),
    )


class DummyStorage(StorageBackend):
    def write_aso(self, aso: AgentStateObject) -> None:
        pass

    def read_aso(self, session_id: str) -> AgentStateObject:
        raise NotImplementedError

    def list_sessions(self) -> list[str]:
        return []

    def delete_aso(self, session_id: str) -> None:
        pass

    def exists(self, session_id: str) -> bool:
        return False


def test_signal_handler_registers_and_restores_original_handlers(monkeypatch):
    original_handlers = {
        signal.SIGINT: object(),
        signal.SIGTERM: object(),
    }
    installed_handlers = {}

    monkeypatch.setattr(signal, "getsignal", lambda signum: original_handlers[signum])

    def fake_signal(signum, handler):
        installed_handlers[signum] = handler

    monkeypatch.setattr(signal, "signal", fake_signal)
    handler = FreezeSignalHandler(make_aso(), DummyStorage())

    handler.register()

    assert installed_handlers[signal.SIGINT] == handler._handle_signal
    assert installed_handlers[signal.SIGTERM] == handler._handle_signal

    handler.deregister()

    assert installed_handlers[signal.SIGINT] == original_handlers[signal.SIGINT]
    assert installed_handlers[signal.SIGTERM] == original_handlers[signal.SIGTERM]


def test_signal_handler_freezes_deregisters_and_exits(monkeypatch):
    aso = make_aso()
    storage = DummyStorage()
    freeze_calls = []
    deregister_calls = []

    def fake_freeze(call_aso, call_storage, summary=""):
        freeze_calls.append((call_aso, call_storage, summary))
        return call_aso

    def fake_exit(code=0):
        raise SystemExit(code)

    monkeypatch.setattr(signal, "getsignal", lambda signum: object())
    monkeypatch.setattr("agentposix.signals.handler.freeze", fake_freeze)
    monkeypatch.setattr("agentposix.signals.handler.sys.exit", fake_exit)

    handler = FreezeSignalHandler(aso, storage)
    monkeypatch.setattr(handler, "deregister", lambda: deregister_calls.append(True))

    with pytest.raises(SystemExit) as exc_info:
        handler._handle_signal(signal.SIGTERM, None)

    assert exc_info.value.code == 0
    assert freeze_calls == [(aso, storage, "Frozen via SIGTERM")]
    assert deregister_calls == [True]
