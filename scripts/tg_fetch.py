#!/usr/bin/env python3
"""Telegram-источник: список свежих файлов в канале и их скачивание (через аккаунт пользователя, Telethon).
Нужны секреты TG_API_ID, TG_API_HASH, TG_SESSION (строка сессии, см. scripts/tg_login.py)."""
import os, re, asyncio
from telethon import TelegramClient
from telethon.sessions import StringSession


def _client():
    return TelegramClient(StringSession(os.environ["TG_SESSION"]),
                          int(os.environ["TG_API_ID"]), os.environ["TG_API_HASH"])


def list_files(channel, regex, limit=200):
    rx = re.compile(regex, re.I)

    async def go():
        out = []
        async with _client() as c:
            async for m in c.iter_messages(channel, limit=limit):
                if m.file and m.file.name and rx.search(m.file.name):
                    out.append((m.id, m.file.name, m.file.size or 0, m.date.strftime("%Y-%m-%d")))
        return out
    return asyncio.run(go())


def download(channel, msg_id, dest):
    async def go():
        async with _client() as c:
            m = await c.get_messages(channel, ids=msg_id)
            last = [0]

            def prog(done, total):
                pct = done * 100 // max(total, 1)
                if pct >= last[0] + 10:
                    last[0] = pct; print(f"  tg: {pct}%", flush=True)
            await c.download_media(m, file=str(dest), progress_callback=prog)
    asyncio.run(go())
