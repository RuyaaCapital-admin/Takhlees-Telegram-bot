# Ruyaa-Takhless Telegram Bot (Arabic)

**Purpose:** Arabic (Syrian tone) customer-service bot for Syrian official documents: extraction, attestation, sworn translation, and delivery.  
**Key features:** short replies, intake flow (3 fields), request tracking, subscriptions + admin broadcast, WhatsApp deep link.

## Quick Start (Polling)
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# put BOT_TOKEN and ADMIN_IDS in .env
python bot.py
```


Open Telegram, send /start to your bot.

Environment

BOT_TOKEN — from @BotFather

ADMIN_IDS — comma-separated Telegram user IDs (e.g., 123,456)

Commands to set in @BotFather → Edit Commands
start - بدء سريع
help - مساعدة
services - الخدمات
request - إنشاء طلب
status - متابعة طلب
contact - التواصل
subscribe - اشتراك
unsubscribe - إلغاء الاشتراك
privacy - الخصوصية

Deploy options

VPS + systemd: see ops/systemd-ruyaa-bot.service.

Docker: build ops/Dockerfile.

Platform dynos (Render/Railway): use ops/Procfile with start command python bot.py.

Knowledge Base

Arabic files in kb/ guide answers, guardrails, and service data. Unknowns remain null/review_required. The bot does not auto-read them; you can load/use them later or just keep them as a reference for operators and future NLU.

Security / Guardrails

No secrets, license numbers, partner names, or internal tools mentioned by the bot.

If unsure: reply “المعلومة غير متوفرة” and escalate.
