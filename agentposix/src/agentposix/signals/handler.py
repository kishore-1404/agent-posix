import signal
import sys
from typing import Callable

from agentposix.core.freeze import freeze
from agentposix.models.aso import AgentStateObject
from agentposix.storage.base import StorageBackend


class FreezeSignalHandler:
    def __init__(self, aso: AgentStateObject, storage: StorageBackend):
        self.aso = aso
        self.storage = storage
        self._original_sigint: Callable = signal.getsignal(signal.SIGINT)
        self._original_sigterm: Callable = signal.getsignal(signal.SIGTERM)

    def register(self):
        signal.signal(signal.SIGINT, self._handle_signal)
        signal.signal(signal.SIGTERM, self._handle_signal)

    def deregister(self):
        signal.signal(signal.SIGINT, self._original_sigint)
        signal.signal(signal.SIGTERM, self._original_sigterm)

    def _handle_signal(self, signum, frame):
        sig_name = "SIGINT" if signum == signal.SIGINT else "SIGTERM"
        freeze(self.aso, self.storage, summary=f"Frozen via {sig_name}")
        self.deregister()
        sys.exit(0)
