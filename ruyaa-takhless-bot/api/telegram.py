from fastapi import FastAPI, Request
from aiogram.types import Update
from bot import bot as tg_bot, dp, set_bot_commands
from storage import init as storage_init

app = FastAPI()

@app.on_event("startup")
async def on_startup():
    await storage_init()          # uses REDIS_URL or DB_PATH=/tmp/bot.db
    await set_bot_commands()

async def _handle(request: Request):
    raw = await request.body()
    update = Update.model_validate_json(raw)
    await dp.feed_update(tg_bot, update)
    return {"ok": True}

# Accept all possible paths Vercel might forward
@app.post("/")
async def root(request: Request):            return await _handle(request)

@app.post("/api/telegram")
async def api_no_slash(request: Request):    return await _handle(request)

@app.post("/api/telegram/")
async def api_with_slash(request: Request):  return await _handle(request)
