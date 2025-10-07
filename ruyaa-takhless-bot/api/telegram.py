from fastapi import FastAPI, Request
from aiogram.types import Update
from bot import bot as tg_bot, dp, set_bot_commands   # no hyphens in module names
from storage import init as storage_init              # Redis or SQLite fallback

app = FastAPI()

@app.on_event("startup")
async def on_startup():
    await storage_init()
    await set_bot_commands()

@app.post("/")
async def telegram_webhook(request: Request):
    raw = await request.body()
    update = Update.model_validate_json(raw)
    await dp.feed_update(tg_bot, update)
    return {"ok": True}
