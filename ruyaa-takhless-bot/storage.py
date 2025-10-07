import os
import json
from typing import List, Dict, Optional

REDIS_URL = os.getenv("REDIS_URL")
DB_PATH = os.getenv("DB_PATH", "bot.db")

if REDIS_URL:
    import redis.asyncio as redis
    _redis = redis.Redis.from_url(REDIS_URL, decode_responses=True)
else:
    import aiosqlite

async def init():
    if REDIS_URL:
        return
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
        CREATE TABLE IF NOT EXISTS subs (
            chat_id INTEGER PRIMARY KEY,
            first_name TEXT
        )""")
        await db.execute("""
        CREATE TABLE IF NOT EXISTS requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id INTEGER,
            doc_type TEXT,
            country TEXT,
            mode TEXT,
            status TEXT DEFAULT 'جديد'
        )""")
        await db.commit()

async def add_sub(chat_id: int, first_name: str):
    if REDIS_URL:
        await _redis.hset("subs", chat_id, first_name)
    else:
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("INSERT OR IGNORE INTO subs (chat_id, first_name) VALUES (?, ?)", (chat_id, first_name))
            await db.commit()

async def del_sub(chat_id: int):
    if REDIS_URL:
        await _redis.hdel("subs", chat_id)
    else:
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("DELETE FROM subs WHERE chat_id = ?", (chat_id,))
            await db.commit()

async def list_sub_ids() -> List[int]:
    if REDIS_URL:
        ids = await _redis.hkeys("subs")
        return [int(i) for i in ids]
    else:
        async with aiosqlite.connect(DB_PATH) as db:
            async with db.execute("SELECT chat_id FROM subs") as cursor:
                return [row[0] async for row in cursor]

async def new_request(chat_id: int, doc_type: str, country: str, mode: str) -> int:
    if REDIS_URL:
        req_id = await _redis.incr("req_seq")
        req = {"id": req_id, "doc_type": doc_type, "country": country, "mode": mode, "status": "جديد"}
        await _redis.lpush(f"req:{chat_id}", json.dumps(req))
        return req_id
    else:
        async with aiosqlite.connect(DB_PATH) as db:
            cur = await db.execute(
                "INSERT INTO requests (chat_id, doc_type, country, mode) VALUES (?, ?, ?, ?)",
                (chat_id, doc_type, country, mode)
            )
            await db.commit()
            return cur.lastrowid

async def recent_requests(chat_id: int, limit: int = 3) -> List[Dict]:
    if REDIS_URL:
        items = await _redis.lrange(f"req:{chat_id}", 0, limit - 1)
        return [json.loads(x) for x in items]
    else:
        async with aiosqlite.connect(DB_PATH) as db:
            async with db.execute(
                "SELECT id, doc_type, country, mode, status FROM requests WHERE chat_id = ? ORDER BY id DESC LIMIT ?",
                (chat_id, limit)
            ) as cursor:
                return [
                    {"id": row[0], "doc_type": row[1], "country": row[2], "mode": row[3], "status": row[4]}
                    async for row in cursor
                ]
