"""SQLite persistence layer using aiosqlite."""

import os
from datetime import datetime, timezone
from typing import Any, Optional

import aiosqlite


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _today() -> str:
    return datetime.now(timezone.utc).date().isoformat()


class Database:
    def __init__(self, path: str):
        self.path = path
        self._conn: Optional[aiosqlite.Connection] = None

    async def initialize(self) -> None:
        directory = os.path.dirname(self.path)
        if directory:
            os.makedirs(directory, exist_ok=True)
        self._conn = await aiosqlite.connect(self.path)
        self._conn.row_factory = aiosqlite.Row
        await self._conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                first_seen TEXT NOT NULL,
                last_seen TEXT NOT NULL,
                total_requests INTEGER NOT NULL DEFAULT 0,
                daily_date TEXT,
                daily_requests INTEGER NOT NULL DEFAULT 0,
                daily_limit_override INTEGER,
                premium INTEGER NOT NULL DEFAULT 0,
                banned INTEGER NOT NULL DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS request_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                tool TEXT,
                success INTEGER NOT NULL,
                error TEXT,
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS errors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                message TEXT,
                created_at TEXT NOT NULL
            );
            """
        )
        await self._conn.commit()

    async def close(self) -> None:
        if self._conn is not None:
            await self._conn.close()
            self._conn = None

    # ---- user operations -------------------------------------------------

    async def upsert_user(self, user_id: int, username: Optional[str], first_name: Optional[str]) -> None:
        assert self._conn
        now = _now()
        await self._conn.execute(
            """
            INSERT INTO users (user_id, username, first_name, first_seen, last_seen, daily_date)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                username=excluded.username,
                first_name=excluded.first_name,
                last_seen=excluded.last_seen
            """,
            (user_id, username, first_name, now, now, _today()),
        )
        await self._conn.commit()

    async def get_user(self, user_id: int) -> Optional[dict]:
        assert self._conn
        async with self._conn.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)) as cur:
            row = await cur.fetchone()
        return dict(row) if row else None

    async def touch_usage(self, user_id: int, tool: str, success: bool, error: Optional[str] = None) -> None:
        assert self._conn
        today = _today()
        await self._conn.execute(
            """
            UPDATE users SET
                total_requests = total_requests + 1,
                daily_requests = CASE WHEN daily_date = ? THEN daily_requests + 1 ELSE 1 END,
                daily_date = ?,
                last_seen = ?
            WHERE user_id = ?
            """,
            (today, today, _now(), user_id),
        )
        await self._conn.execute(
            "INSERT INTO request_log (user_id, tool, success, error, created_at) VALUES (?, ?, ?, ?, ?)",
            (user_id, tool, 1 if success else 0, error, _now()),
        )
        await self._conn.commit()

    async def get_usage(self, user_id: int) -> dict:
        user = await self.get_user(user_id)
        if not user:
            return {"used_today": 0, "premium": False, "banned": False, "override": None}
        today = _today()
        used = user["daily_requests"] if user["daily_date"] == today else 0
        return {
            "used_today": used,
            "premium": bool(user["premium"]),
            "banned": bool(user["banned"]),
            "override": user["daily_limit_override"],
        }

    async def set_premium(self, user_id: int, premium: bool) -> bool:
        assert self._conn
        cur = await self._conn.execute(
            "UPDATE users SET premium = ? WHERE user_id = ?", (1 if premium else 0, user_id)
        )
        await self._conn.commit()
        return cur.rowcount > 0

    async def set_banned(self, user_id: int, banned: bool) -> bool:
        assert self._conn
        cur = await self._conn.execute(
            "UPDATE users SET banned = ? WHERE user_id = ?", (1 if banned else 0, user_id)
        )
        await self._conn.commit()
        return cur.rowcount > 0

    async def set_daily_limit(self, user_id: int, limit: int) -> bool:
        assert self._conn
        cur = await self._conn.execute(
            "UPDATE users SET daily_limit_override = ? WHERE user_id = ?", (limit, user_id)
        )
        await self._conn.commit()
        return cur.rowcount > 0

    # ---- statistics ------------------------------------------------------

    async def stats(self) -> dict:
        assert self._conn
        today = _today()

        async def scalar(query: str, params: tuple = ()) -> int:
            async with self._conn.execute(query, params) as cur:
                row = await cur.fetchone()
            return int(row[0]) if row else 0

        total_users = await scalar("SELECT COUNT(*) FROM users")
        premium_users = await scalar("SELECT COUNT(*) FROM users WHERE premium = 1")
        banned_users = await scalar("SELECT COUNT(*) FROM users WHERE banned = 1")
        total_requests = await scalar("SELECT COUNT(*) FROM request_log")
        requests_today = await scalar("SELECT COUNT(*) FROM request_log WHERE created_at >= ?", (today,))
        active_today = await scalar("SELECT COUNT(*) FROM users WHERE last_seen >= ?", (today,))
        total_errors = await scalar("SELECT COUNT(*) FROM errors")
        return {
            "total_users": total_users,
            "premium_users": premium_users,
            "banned_users": banned_users,
            "total_requests": total_requests,
            "requests_today": requests_today,
            "active_today": active_today,
            "total_errors": total_errors,
        }

    async def all_user_ids(self) -> list[int]:
        assert self._conn
        async with self._conn.execute("SELECT user_id FROM users WHERE banned = 0") as cur:
            rows = await cur.fetchall()
        return [int(r[0]) for r in rows]

    async def list_users(self, limit: int = 50) -> list[dict]:
        assert self._conn
        async with self._conn.execute(
            "SELECT user_id, username, first_name, premium, banned, total_requests, last_seen "
            "FROM users ORDER BY last_seen DESC LIMIT ?",
            (limit,),
        ) as cur:
            rows = await cur.fetchall()
        return [dict(r) for r in rows]

    async def log_error(self, user_id: Optional[int], message: str) -> None:
        assert self._conn
        await self._conn.execute(
            "INSERT INTO errors (user_id, message, created_at) VALUES (?, ?, ?)",
            (user_id, message[:2000], _now()),
        )
        await self._conn.commit()
