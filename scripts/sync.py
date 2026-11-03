#!/usr/bin/env python3
"""Скачивает свежие GSI из GitHub Releases, грузит на Google Drive (rclone) и обновляет README."""
import json, os, re, subprocess, urllib.request, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
STATE = ROOT / "state.json"
README = ROOT / "README.md"
REMOTE = os.environ.get("RCLONE_REMOTE", "gdrive:GSI")
TOKEN = os.environ.get("GITHUB_TOKEN")
WORK = pathlib.Path(os.environ.get("WORK_DIR", "/tmp/gsi"))
START, END = "<!-- GSI-LIST:START -->", "<!-- GSI-LIST:END -->"


def gh(url):
    req = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json"})
    if TOKEN:
        req.add_header("Authorization", f"Bearer {TOKEN}")
    with urllib.request.urlopen(req) as r:
        return json.load(r)


def run(*cmd):
    print("+", " ".join(cmd), flush=True)
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        print(r.stdout, r.stderr, sep="\n", flush=True)
        raise SystemExit(f"Команда упала: {cmd[0]} (код {r.returncode})")
    return r.stdout.strip()


def main():
    sources = json.loads((ROOT / "sources.json").read_text())
    state = json.loads(STATE.read_text()) if STATE.exists() else {}
    WORK.mkdir(parents=True, exist_ok=True)

    for src in sources:
        try:
            rel = gh(f"https://api.github.com/repos/{src['repo']}/releases/latest")
        except Exception as e:
            print(f"[{src['name']}] ошибка API: {e}")
            continue
        tag = rel["tag_name"]
        rx = re.compile(src["asset_regex"])
        assets = [a for a in rel["assets"] if rx.search(a["name"])]
        if not assets:
            print(f"[{src['name']}] нет подходящих файлов в {tag}")
            continue
        for a in assets:
            key = f"{src['repo']}/{a['name']}"
            if key in state and state[key]["tag"] == tag:
                print(f"[{src['name']}] {a['name']} уже загружен")
                continue
            local = WORK / a["name"]
            run("curl", "-fL", "--retry", "3", "-o", str(local), a["browser_download_url"])
            dest = f"{REMOTE}/{src['repo'].replace('/', '_')}/{tag}"
            run("rclone", "copy", str(local), dest)
            link = run("rclone", "link", f"{dest}/{a['name']}")
            local.unlink()
            state[key] = {"name": src["name"], "tag": tag, "file": a["name"],
                          "size_mb": round(a["size"] / 2**20), "link": link,
                          "date": rel.get("published_at", "")[:10]}

    STATE.write_text(json.dumps(state, indent=2, ensure_ascii=False) + "\n")

    rows = ["| Сборка | Версия | Файл | Размер | Дата | Google Drive |", "|---|---|---|---|---|---|"]
    for v in sorted(state.values(), key=lambda v: v["date"], reverse=True):
        rows.append(f"| {v['name']} | `{v['tag']}` | `{v['file']}` | {v['size_mb']} MB | {v['date']} | [Скачать]({v['link']}) |")
    text = README.read_text()
    text = re.sub(re.escape(START) + ".*?" + re.escape(END),
                  START + "\n" + "\n".join(rows) + "\n" + END, text, flags=re.S)
    README.write_text(text)


if __name__ == "__main__":
    main()
