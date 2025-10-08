# ruyaa-takhless-bot/api/telegram.py
from fastapi import FastAPI, Request
from aiogram.types import Update

# Import from local package (no hyphens)
from bot import bot as tg_bot, dp, set_bot_commands, main_menu_kb
from storage import init as storage_init  # uses REDIS_URL or DB_PATH fallback

app = FastAPI()

@app.on_event("startup")
async def on_startup():
    # Init storage and bot commands once per cold start
    await storage_init()
    await set_bot_commands()

async def _process(request: Request):
    raw = await request.body()
    if not raw:
        return {"ok": True}
    try:
        upd = Update.model_validate_json(raw)

        # HARD GUARANTEE: respond to /start even if filters/handlers miss
        if getattr(upd, "message", None) and getattr(upd.message, "text", None):
            txt = upd.message.text or ""
            if txt.startswith("/start"):
                await tg_bot.send_message(
                    upd.message.chat.id,
                    "أهلين! شو الخدمة اللي بدك تنجزها؟",
                    reply_markup=main_menu_kb(),
                )

        # Feed update to aiogram dispatcher (normal routing)
        await dp.feed_update(tg_bot, upd)
    except Exception as e:
        # Never crash the serverless function; log and return 200
        print("webhook_error:", repr(e))
    return {"ok": True}

# Accept common paths (Vercel function mapping)
@app.post("/")
async def root(request: Request):                return await _process(request)

@app.post("/api/telegram")
async def api1(request: Request):                return await _process(request)

@app.post("/api/telegram/")
async def api2(request: Request):                return await _process(request)

@app.post("/{path:path}")
async def anypath(request: Request, path: str):  return await _process(request)
