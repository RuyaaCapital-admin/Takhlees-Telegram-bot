#!/usr/bin/env bash
# Optional: set commands via HTTP (replace BOT_TOKEN)
curl -s -X POST "https://api.telegram.org/bot${BOT_TOKEN}/setMyCommands" \
  -H "Content-Type: application/json" \
  -d '{
    "commands": [
      {"command":"start","description":"بدء سريع"},
      {"command":"help","description":"مساعدة"},
      {"command":"services","description":"الخدمات"},
      {"command":"request","description":"إنشاء طلب"},
      {"command":"status","description":"متابعة طلب"},
      {"command":"contact","description":"التواصل"},
      {"command":"subscribe","description":"اشتراك"},
      {"command":"unsubscribe","description":"إلغاء الاشتراك"},
      {"command":"privacy","description":"الخصوصية"}
    ]
}'
