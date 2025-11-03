import aiosqlite
from dataclasses import asdict
from typing import List, Optional
from giveaway import Giveaway


class AsyncDatabase:
    def __init__(self, path: str):
        self.path = path
        self.con: Optional[aiosqlite.Connection] = None

    async def connect(self):
        self.con = await aiosqlite.connect(self.path)
        self.con.row_factory = aiosqlite.Row
        await self.con.execute("PRAGMA foreign_keys = ON")
        await self._create_tables()

    async def close(self):
        if self.con:
            await self.con.close()

    async def _create_tables(self):
        await self.con.execute("""
            CREATE TABLE IF NOT EXISTS giveaways (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER NOT NULL,
                channel_id INTEGER NOT NULL,
                message_id INTEGER,
                title TEXT NOT NULL,
                prize TEXT NOT NULL,
                criteria TEXT,
                winners_count INTEGER NOT NULL,
                created_at INTEGER NOT NULL,
                ends_at INTEGER NOT NULL,
                creator_id INTEGER NOT NULL,
                host_id INTEGER,
                required_role_id INTEGER,
                ping_role INTEGER,
                recurring INTEGER,
                active INTEGER DEFAULT 1
            );
        """)
        await self.con.execute("""
            CREATE TABLE IF NOT EXISTS participants (
                giveaway_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                FOREIGN KEY(giveaway_id) REFERENCES giveaways(id) ON DELETE CASCADE
            )
        """)
        await self.con.execute("""
            CREATE TABLE IF NOT EXISTS winners (
                giveaway_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                FOREIGN KEY (giveaway_id) REFERENCES giveaways(id) ON DELETE CASCADE
            )
        """)
        await self.con.commit()

    # ---------------- Giveaways ----------------
    async def add_giveaway(self, giveaway: Giveaway):
        data = asdict(giveaway)
        if data.get("id") is None:
            data.pop("id")

        columns = ", ".join(data.keys())
        placeholders = ", ".join("?" for _ in data)
        query = f"INSERT INTO giveaways ({columns}) VALUES ({placeholders})"

        async with self.con.execute(query, tuple(data.values())) as cur:
            await self.con.commit()
            return cur.lastrowid

    async def get_giveaway(self, giveaway_id: int) -> Optional[Giveaway]:
        async with self.con.execute(
            "SELECT * FROM giveaways WHERE id = ?", (giveaway_id,)
        ) as cur:
            row = await cur.fetchone()
            return Giveaway(**dict(row)) if row else None

    async def get_giveaways(
        self,
        guild_id: Optional[int] = None,
        channel_id: Optional[int] = None,
        giveaway_id: Optional[int] = None,
        active: Optional[int] = None,
    ) -> List[Giveaway]:
        query = "SELECT * FROM giveaways"
        conditions, values = [], []

        if guild_id is not None:
            conditions.append("guild_id = ?")
            values.append(guild_id)
        if channel_id is not None:
            conditions.append("channel_id = ?")
            values.append(channel_id)
        if giveaway_id is not None:
            conditions.append("id = ?")
            values.append(giveaway_id)
        if active is not None:
            conditions.append("active = ?")
            values.append(active)

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        async with self.con.execute(query, tuple(values)) as cur:
            rows = await cur.fetchall()
            return [Giveaway(**dict(row)) for row in rows]

    async def set_message_id(self, message_id: int, giveaway_id: int):
        await self.con.execute(
            "UPDATE giveaways SET message_id=? WHERE id=?",
            (message_id, giveaway_id),
        )
        await self.con.commit()

    async def set_inactive(self, giveaway_id: int):
        await self.con.execute(
            "UPDATE giveaways SET active=0 WHERE id=?", (giveaway_id,)
        )
        await self.con.commit()

    async def delete_giveaway(self, giveaway_id: int):
        await self.con.execute("DELETE FROM giveaways WHERE id=?", (giveaway_id,))
        await self.con.commit()

    # ---------------- Participants ----------------
    async def add_participant(self, user_id: int, giveaway_id: int):
        await self.con.execute(
            "INSERT INTO participants (giveaway_id, user_id) VALUES (?, ?)",
            (giveaway_id, user_id),
        )
        await self.con.commit()

    async def rem_participant(self, user_id: int, giveaway_id: int):
        await self.con.execute(
            "DELETE FROM participants WHERE giveaway_id=? AND user_id=?",
            (giveaway_id, user_id),
        )
        await self.con.commit()

    async def get_participants(self, giveaway_id: int):
        async with self.con.execute(
            "SELECT user_id FROM participants WHERE giveaway_id=?", (giveaway_id,)
        ) as cur:
            rows = await cur.fetchall()
            return [r["user_id"] for r in rows]

    async def count_participants(self, giveaway_id: int) -> int:
        async with self.con.execute(
            "SELECT COUNT(*) AS total FROM participants WHERE giveaway_id=?",
            (giveaway_id,),
        ) as cur:
            row = await cur.fetchone()
            return row["total"] if row else 0

    # ---------------- Winners ----------------
    async def add_winners(self, giveaway_id: int, winners: list[int]):
        """Insert multiple winners for a giveaway in one go."""
        await self.con.executemany(
            "INSERT INTO winners (giveaway_id, user_id) VALUES (?, ?)",
            [(giveaway_id, uid) for uid in winners],
        )
        await self.con.commit()

    async def get_winners(self, giveaway_id: int):
        async with self.con.execute(
            "SELECT user_id FROM winners WHERE giveaway_id = ?", (giveaway_id,)
        ) as cur:
            rows = await cur.fetchall()
            return [row["user_id"] for row in rows]

    async def clear_winners(self, giveaway_id: int):
        await self.con.execute(
            "DELETE FROM winners WHERE giveaway_id = ?", (giveaway_id,)
        )
        await self.con.commit()
