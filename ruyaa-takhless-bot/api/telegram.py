from fastapi import FastAPI, Request
from aiogram.types import Update
from bot import bot as tg_bot, dp, set_bot_commands
from storage import init as storage_init

app = FastAPI()

@app.on_event("startup")
async def on_startup():
    await storage_init()          # uses REDIS_URL or DB_PATH=/tmp/bot.db
    await set_bot_commands()

async def _process(request: Request):
    raw = await request.body()
    if not raw:
        return {"ok": True}
    try:
        update = Update.model_validate_json(raw)
        await dp.feed_update(tg_bot, update)   # safe: no raise if no handler
    except Exception as e:
        # swallow all to avoid 500s on Vercel
        print("webhook_error:", repr(e))
    return {"ok": True}

# accept any path Vercel might hit
@app.post("/")
async def root(request: Request):                return await _process(request)
@app.post("/api/telegram")
async def api1(request: Request):                return await _process(request)
@app.post("/api/telegram/")
async def api2(request: Request):                return await _process(request)
@app.post("/{path:path}")
async def catch_all(request: Request, path: str):return await _process(request)
