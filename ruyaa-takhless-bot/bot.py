import os, time, asyncio
from dotenv import load_dotenv
import aiosqlite

from aiogram import Bot, Dispatcher, F, types
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.types import (
    InlineKeyboardMarkup, InlineKeyboardButton,
    BotCommand, BotCommandScopeDefault
)
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext

# ===== Config =====
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_IDS = {int(x) for x in (os.getenv("ADMIN_IDS","").split(",")) if x.strip().isdigit()}
DB_PATH = "bot.db"
WHATSAPP_LINK = "https://wa.me/963940632191"

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN missing in .env")

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

# ===== DB =====
async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""CREATE TABLE IF NOT EXISTS subscribers(
            chat_id INTEGER PRIMARY KEY,
            first_name TEXT,
            ts INTEGER
        )""")
        await db.execute("""CREATE TABLE IF NOT EXISTS requests(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id INTEGER,
            doc_type TEXT,
            delivery_country TEXT,
            delivery_mode TEXT,
            ts INTEGER,
            status TEXT
        )""")
        await db.commit()

# ===== Bot Commands in UI (optional) =====
async def set_bot_commands():
    cmds = [
        BotCommand(command="start", description="بدء سريع"),
        BotCommand(command="help", description="مساعدة"),
        BotCommand(command="services", description="الخدمات"),
        BotCommand(command="request", description="إنشاء طلب"),
        BotCommand(command="status", description="متابعة طلب"),
        BotCommand(command="contact", description="التواصل"),
        BotCommand(command="subscribe", description="اشتراك"),
        BotCommand(command="unsubscribe", description="إلغاء الاشتراك"),
        BotCommand(command="privacy", description="الخصوصية"),
    ]
    await bot.set_my_commands(cmds, scope=BotCommandScopeDefault())

# ===== Content =====
SERVICES_TXT = (
    "• الأحوال المدنية: إخراج قيد، بيان عائلي، ولادة، زواج، طلاق، وفاة، تصحيح قيود\n"
    "• القضائية/الإدارية: لا حكم عليه، عدم عمل، إقرارات موثقة، تقارير طبية/مصرفية\n"
    "• العقارية: بيان ملكية، عقد بيع موثق، رخص بناء/مخططات\n"
    "• التجارة والصناعة: سجل تجاري، سجل صناعي، رخص صناعية/صحية، حماية علامة\n"
    "• التصديقات/الترجمة: تصديقات وزارات، ترجمة محلفة، تصديق سفارة\n"
)

def main_menu_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="الخدمات", callback_data="menu_services"),
         InlineKeyboardButton(text="إنشاء طلب", callback_data="menu_request")],
        [InlineKeyboardButton(text="متابعة طلب", callback_data="menu_status"),
         InlineKeyboardButton(text="تواصل واتساب", url=WHATSAPP_LINK)],
        [InlineKeyboardButton(text="اشتراك بالتحديثات", callback_data="menu_subscribe")]
    ])

# ===== Guardrail helpers =====
def short(txt: str) -> str:
    return txt.strip()

# ===== FSM for intake =====
class Intake(StatesGroup):
    doc_type = State()
    delivery_country = State()
    delivery_mode = State()

# ===== Handlers =====
@dp.message(Command("start"))
async def start_cmd(m: types.Message):
    await m.answer(short("أهلين! شو الخدمة اللي بدك تنجزها؟"), reply_markup=main_menu_kb())

@dp.message(Command("help"))
async def help_cmd(m: types.Message):
    await m.answer(short("ردود قصيرة. للخدمات: /services — لطلب جديد: /request — واتساب بالرابط."))

@dp.message(Command("services"))
async def services_cmd(m: types.Message):
    await m.answer(SERVICES_TXT)

@dp.message(Command("contact"))
async def contact_cmd(m: types.Message):
    await m.answer(short(f"منراسل عالواتساب:\n{WHATSAPP_LINK}"))

@dp.message(Command("privacy"))
async def privacy_cmd(m: types.Message):
    await m.answer(short("خصوصيتك محفوظة. بناخد أقل بيانات لازمة وبنستخدمها بس لتنفيذ الطلب."))

@dp.message(Command("subscribe"))
async def subscribe_cmd(m: types.Message):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("INSERT OR REPLACE INTO subscribers(chat_id, first_name, ts) VALUES(?,?,?)",
                         (m.chat.id, m.from_user.first_name or "", int(time.time())))
        await db.commit()
    await m.answer(short("تم الاشتراك. بتوصلك تحديثات قصيرة."))

@dp.message(Command("unsubscribe"))
async def unsubscribe_cmd(m: types.Message):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM subscribers WHERE chat_id= ?", (m.chat.id,))
        await db.commit()
    await m.answer(short("تم الإلغاء."))

# Admin broadcast
@dp.message(Command("broadcast"))
async def broadcast_cmd(m: types.Message):
    if m.from_user.id not in ADMIN_IDS:
        return
    payload = m.text.split(" ", 1)
    if len(payload) < 2 or not payload[1].strip():
        await m.answer("اكتب: /broadcast نص")
        return
    msg = payload[1].strip()
    sent, fail = 0, 0
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT chat_id FROM subscribers") as cur:
            rows = await cur.fetchall()
    for (chat_id,) in rows:
        try:
            await bot.send_message(chat_id, msg)
            sent += 1
        except Exception:
            fail += 1
    await m.answer(f"تم الإرسال: {sent} | فشل: {fail}")

# Intake flow
@dp.message(Command("request"))
async def request_cmd(m: types.Message, state: FSMContext):
    await state.set_state(Intake.doc_type)
    await m.answer(short("نوع الوثيقة؟ (مثال: إخراج قيد، لا حكم عليه، بيان ملكية...)"))

@dp.message(Intake.doc_type, F.text.len() > 1)
async def intake_doc(m: types.Message, state: FSMContext):
    await state.update_data(doc_type=m.text.strip())
    await state.set_state(Intake.delivery_country)
    await m.answer(short("بلد التسليم؟"))

@dp.message(Intake.delivery_country, F.text.len() > 1)
async def intake_country(m: types.Message, state: FSMContext):
    await state.update_data(delivery_country=m.text.strip())
    await state.set_state(Intake.delivery_mode)
    await m.answer(short("طريقة التسليم؟ (digital أو original)"))

@dp.message(Intake.delivery_mode, F.text.regexp(r"^(digital|original)$"))
async def intake_done(m: types.Message, state: FSMContext):
    data = await state.get_data()
    doc_type = data["doc_type"]
    country = data["delivery_country"]
    mode = m.text.strip()
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO requests(chat_id, doc_type, delivery_country, delivery_mode, ts, status) "
            "VALUES (?,?,?,?,?,?)",
            (m.chat.id, doc_type, country, mode, int(time.time()), "new")
        )
        await db.commit()
        cur = await db.execute("SELECT last_insert_rowid()")
        req_id = (await cur.fetchone())[0]
    await state.clear()
    await m.answer(short(f"تم فتح طلبك رقم #{req_id}. الوقت والتكلفة بيتأكدوا بعد المراجعة."))

@dp.message(Command("status"))
async def status_cmd(m: types.Message):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT id, doc_type, status FROM requests WHERE chat_id=? ORDER BY id DESC LIMIT 3",
            (m.chat.id,)
        ) as cur:
            rows = await cur.fetchall()
    if not rows:
        await m.answer(short("ما في طلبات. فيك تبدأ بـ /request"))
    else:
        lines = [f"#{r[0]} • {r[1]} • {r[2]}" for r in rows]
        await m.answer("آخر الطلبات:\n" + "\n".join(lines))

# Menu callbacks
@dp.callback_query(F.data == "menu_services")
async def cb_services(c: types.CallbackQuery):
    await c.message.answer(SERVICES_TXT); await c.answer()

@dp.callback_query(F.data == "menu_request")
async def cb_request(c: types.CallbackQuery, state: FSMContext):
    await state.set_state(Intake.doc_type)
    await c.message.answer("نوع الوثيقة؟"); await c.answer()

@dp.callback_query(F.data == "menu_status")
async def cb_status(c: types.CallbackQuery):
    await status_cmd(c.message); await c.answer()

@dp.callback_query(F.data == "menu_subscribe")
async def cb_subscribe(c: types.CallbackQuery):
    await subscribe_cmd(c.message); await c.answer()

# ===== Run =====
async def main():
    await init_db()
    await set_bot_commands()
    print("Bot started.")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
