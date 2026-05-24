import json
import os
import threading
from json import JSONDecodeError
from pathlib import Path
from typing import List

from pydantic import ValidationError

from agentposix.core.checksum import compute_checksum
from agentposix.exceptions import InvalidASOError
from agentposix.models.aso import AgentStateObject
from agentposix.storage.base import StorageBackend


class FilesystemBackend(StorageBackend):
    """
    Filesystem-backed ASO persistence with atomic replace-on-write semantics.

    Guarantees:
    - Single-process writers are serialized per session id through an in-process lock.
    - Successful writes flush file contents to disk before the atomic replace step.
    - The target directory is fsynced after replace when the platform supports it.

    Limits:
    - Cross-process coordination is not provided.
    - Durability still depends on the host filesystem and OS semantics.
    """

    def __init__(self, base_dir: str = ".agentposix"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self._session_locks: dict[str, threading.Lock] = {}
        self._locks_guard = threading.Lock()

    def _get_path(self, session_id: str) -> Path:
        return self.base_dir / f"{session_id}.aso.json"

    def _get_session_lock(self, session_id: str) -> threading.Lock:
        with self._locks_guard:
            lock = self._session_locks.get(session_id)
            if lock is None:
                lock = threading.Lock()
                self._session_locks[session_id] = lock
            return lock

    def _fsync_directory(self, directory: Path) -> None:
        try:
            dir_fd = os.open(directory, os.O_RDONLY)
        except OSError:
            return
        try:
            os.fsync(dir_fd)
        finally:
            os.close(dir_fd)

    def _prepare_for_write(self, aso: AgentStateObject) -> AgentStateObject:
        persisted_aso = aso.model_copy(deep=True)
        if not persisted_aso.checksum:
            persisted_aso.checksum = compute_checksum(persisted_aso)
        return persisted_aso

    def write_aso(self, aso: AgentStateObject) -> None:
        persisted_aso = self._prepare_for_write(aso)
        target_path = self._get_path(aso.identity.session_id)
        tmp_path = target_path.with_suffix(".tmp")
        self.base_dir.mkdir(parents=True, exist_ok=True)
        with self._get_session_lock(aso.identity.session_id):
            try:
                with open(tmp_path, "w", encoding="utf-8") as f:
                    json.dump(persisted_aso.model_dump(mode="json"), f, indent=2)
                    f.flush()
                    os.fsync(f.fileno())
                os.replace(tmp_path, target_path)
                self._fsync_directory(self.base_dir)
            except Exception:
                if tmp_path.exists():
                    tmp_path.unlink()
                raise

    def read_aso(self, session_id: str) -> AgentStateObject:
        path = self._get_path(session_id)
        if not path.exists():
            raise FileNotFoundError(f"No ASO found for {session_id}")
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except JSONDecodeError as exc:
            raise InvalidASOError(f"Invalid ASO JSON for session {session_id}: {exc.msg}") from exc
        except OSError as exc:
            raise InvalidASOError(
                f"Unable to read ASO for session {session_id}: {exc.strerror or exc}"
            ) from exc

        try:
            return AgentStateObject.model_validate(data)
        except ValidationError as exc:
            raise InvalidASOError(
                f"Invalid ASO payload for session {session_id}: schema validation failed"
            ) from exc

    def list_sessions(self) -> List[str]:
        return [p.name.replace(".aso.json", "") for p in self.base_dir.glob("*.aso.json")]

    def delete_aso(self, session_id: str) -> None:
        path = self._get_path(session_id)
        if path.exists():
            path.unlink()

    def exists(self, session_id: str) -> bool:
        return self._get_path(session_id).exists()
