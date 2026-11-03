#!/usr/bin/env python3
"""Telegram-каналы через собственный HTTP API (grzxk tg API).
Секрет: TG_PROXY_TOKEN. Опционально TG_PROXY_URL (по умолчанию https://grzxk.ru/tgapi)."""
import json
import os
import subprocess
import urllib.parse
import urllib.request

BASE = os.environ.get("TG_PROXY_URL", "https://grzxk.ru/tgapi").rstrip("/")


def _req(method, path, body=None, params=None):
    url = BASE + path + ("?" + urllib.parse.urlencode(params) if params else "")
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method, headers={
        "Authorization": f"Bearer {os.environ['TG_PROXY_TOKEN']}",
        "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.load(r)


def _walk(o):
    """Все вложенные dict'ы ответа — формат сообщений заранее неизвестен, ищем поля по имени."""
    if isinstance(o, dict):
        yield o
        for v in o.values():
            yield from _walk(v)
    elif isinstance(o, list):
        for v in o:
            yield from _walk(v)


def _messages(resp):
    if isinstance(resp, list):
        return resp
    for k in ("messages", "items", "result", "data"):
        if isinstance(resp, dict) and isinstance(resp.get(k), list):
            return resp[k]
    return []


def _file_info(msg):
    for d in _walk(msg):
        name = d.get("file_name") or d.get("filename") or d.get("name")
        if isinstance(name, str) and "." in name and (d.get("size") or d.get("file_size") or "mime_type" in d):
            return name, int(d.get("size") or d.get("file_size") or 0)
    return None, 0


def list_files(channel, regex, limit=200):
    import re
    rx = re.compile(regex, re.I)
    try:
        _req("POST", "/v1/chats/join", {"peer": channel})
    except Exception as e:  # уже в канале или канал публичный
        print(f"[tg] join {channel}: {e}")
    resp = _req("GET", f"/v1/messages/{urllib.parse.quote(channel)}", params={"limit": limit})
    msgs = _messages(resp)
    if msgs and os.environ.get("TG_DEBUG"):
        print("[tg] пример сообщения:", json.dumps(msgs[0], ensure_ascii=False)[:1500])
    out = []
    for m in msgs:
        name, size = _file_info(m)
        if name and rx.search(name):
            mid = m.get("id") or m.get("msg_id") or m.get("message_id")
            date = str(m.get("date") or "")[:10]
            out.append((int(mid), name, size, date))
    print(f"[tg] {channel}: сообщений {len(msgs)}, подходящих файлов {len(out)}")
    return out


def download(channel, msg_id, dest):
    url = f"{BASE}/v1/media/{urllib.parse.quote(channel)}/{msg_id}"
    subprocess.run(["curl", "-fL", "--retry", "3", "-o", str(dest),
                    "-H", f"Authorization: Bearer {os.environ['TG_PROXY_TOKEN']}", url], check=True)
