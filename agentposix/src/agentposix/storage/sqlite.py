import aiosqlite
import json

from agentposix.core.checksum import compute_checksum
from agentposix.models.aso import AgentStateObject


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
        persisted_aso = aso.model_copy(deep=True)
        if not persisted_aso.checksum:
            persisted_aso.checksum = compute_checksum(persisted_aso)
        payload = json.dumps(persisted_aso.model_dump(mode="json"))
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "INSERT INTO checkpoints (session_id, payload) VALUES (?, ?) "
                "ON CONFLICT(session_id) DO UPDATE SET payload=excluded.payload",
                (persisted_aso.identity.session_id, payload),
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
                    raise FileNotFoundError(f"No ASO found for session {session_id}")
                return AgentStateObject.model_validate_json(row[0])

    async def list_sessions(self) -> list[str]:
        await self._init_db()
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT session_id FROM checkpoints ORDER BY session_id"
            ) as cursor:
                rows = await cursor.fetchall()
        return [row[0] for row in rows]

    async def delete_aso(self, session_id: str) -> None:
        await self._init_db()
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "DELETE FROM checkpoints WHERE session_id = ?",
                (session_id,),
            )
            await db.commit()

    async def exists(self, session_id: str) -> bool:
        await self._init_db()
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT 1 FROM checkpoints WHERE session_id = ?",
                (session_id,),
            ) as cursor:
                row = await cursor.fetchone()
        return row is not None
