import aiosqlite
import asyncio
import json

from src.agentposix.core.checksum import compute_checksum
from src.agentposix.models.aso import AgentStateObject
from src.agentposix.storage.base import StorageBackend


class AsyncSqliteBackend:
    def __init__(self, db_path: str = ".agentposix.db"):
        self.db_path = db_path

    async def _init_db(self):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("PRAGMA journal_mode=WAL;")
            await db.execute(
                "CREATE TABLE IF NOT EXISTS checkpoints "
                "(session_id TEXT PRIMARY KEY, payload JSON)"
            )
            await db.commit()

    async def write_aso(self, aso: AgentStateObject) -> None:
        await self._init_db()
        aso.checksum = compute_checksum(aso)
        payload = json.dumps(aso.model_dump(mode="json"))
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "INSERT INTO checkpoints (session_id, payload) VALUES (?, ?) "
                "ON CONFLICT(session_id) DO UPDATE SET payload=excluded.payload",
                (aso.identity.session_id, payload),
            )
            await db.commit()

    async def read_aso(self, session_id: str) -> AgentStateObject:
        await self._init_db()
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT payload FROM checkpoints WHERE session_id = ?",
                (session_id,),
            ) as cursor:
                row = await cursor.fetchone()
                if not row:
                    raise KeyError(f"Session {session_id} not found.")
                return AgentStateObject.model_validate_json(row[0])
