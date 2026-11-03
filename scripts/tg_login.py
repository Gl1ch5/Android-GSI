#!/usr/bin/env python3
"""Запустите ОДИН РАЗ на своём ПК: pip install telethon && python tg_login.py
Выведет строку сессии — положите её в секрет TG_SESSION. Никому её не показывайте:
она даёт полный доступ к вашему Telegram-аккаунту. Лучше использовать отдельный аккаунт."""
from telethon.sync import TelegramClient
from telethon.sessions import StringSession

api_id = int(input("api_id (с my.telegram.org): "))
api_hash = input("api_hash: ")
with TelegramClient(StringSession(), api_id, api_hash) as c:
    print("\nTG_SESSION =\n" + c.session.save())
