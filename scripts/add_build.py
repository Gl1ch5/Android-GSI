#!/usr/bin/env python3
"""Добавляет собранный образ в state.json и README.
usage: add_build.py <name> <tag> <file> <size_bytes> <link> <android>"""
import datetime
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sync  # noqa: E402

name, tag, file, size, link, android = sys.argv[1:7]
state = json.loads(sync.STATE.read_text()) if sync.STATE.exists() else {}
state[f"mystic/{tag}/{file}"] = {"name": name, "tag": tag, "file": file, "android": android,
                                 "size_mb": round(int(size) / 2**20), "link": link,
                                 "date": datetime.date.today().isoformat()}
sync.render(state)
sync.publish(f"Add {file}")
