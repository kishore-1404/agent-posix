from abc import ABC, abstractmethod
from typing import List

from agentposix.models.aso import AgentStateObject


class StorageBackend(ABC):
    @abstractmethod
    def write_aso(self, aso: AgentStateObject) -> None:
        pass

    @abstractmethod
    def read_aso(self, session_id: str) -> AgentStateObject:
        pass

    @abstractmethod
    def list_sessions(self) -> List[str]:
        pass

    @abstractmethod
    def delete_aso(self, session_id: str) -> None:
        pass

    @abstractmethod
    def exists(self, session_id: str) -> bool:
        pass
