import json
import os
from pathlib import Path
from typing import List

from agentposix.core.checksum import compute_checksum
from agentposix.models.aso import AgentStateObject
from agentposix.storage.base import StorageBackend


class FilesystemBackend(StorageBackend):
    def __init__(self, base_dir: str = ".agentposix"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _get_path(self, session_id: str) -> Path:
        return self.base_dir / f"{session_id}.aso.json"

    def write_aso(self, aso: AgentStateObject) -> None:
        target_path = self._get_path(aso.identity.session_id)
        tmp_path = target_path.with_suffix(".tmp")
        aso.checksum = compute_checksum(aso)
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(aso.model_dump(mode="json"), f, indent=2)
        os.replace(tmp_path, target_path)

    def read_aso(self, session_id: str) -> AgentStateObject:
        path = self._get_path(session_id)
        if not path.exists():
            raise FileNotFoundError(f"No ASO found for {session_id}")
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return AgentStateObject.model_validate(data)

    def list_sessions(self) -> List[str]:
        return [p.name.replace(".aso.json", "") for p in self.base_dir.glob("*.aso.json")]

    def delete_aso(self, session_id: str) -> None:
        path = self._get_path(session_id)
        if path.exists():
            path.unlink()

    def exists(self, session_id: str) -> bool:
        return self._get_path(session_id).exists()
