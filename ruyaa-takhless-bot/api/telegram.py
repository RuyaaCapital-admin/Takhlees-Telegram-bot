import os
from fastapi import FastAPI, Request
from aiogram.types import Update
from ruyaa-takhless-bot.bot import bot, dp, set_bot_commands
from ruyaa-takhless-bot.storage import init as storage_init

app = FastAPI()

@app.on_event("startup")
async def on_startup():
    await storage_init()
    await set_bot_commands()

@app.post("/")
async def telegram_webhook(request: Request):
    raw = await request.body()
    update = Update.model_validate_json(raw)
    await dp.feed_update(bot, update)
    return {"ok": True}
