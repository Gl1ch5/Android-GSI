#!/usr/bin/env python3
"""Скачивает свежие GSI из GitHub Releases, распаковывает в чистый .img,
грузит на Google Drive (rclone) и обновляет таблицу в README."""
import json, os, re, shutil, subprocess, urllib.request, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
STATE = ROOT / "state.json"
README = ROOT / "README.md"
REMOTE = os.environ.get("RCLONE_REMOTE", "gdrive:GSI")
TOKEN = os.environ.get("GITHUB_TOKEN")
WORK = pathlib.Path(os.environ.get("WORK_DIR", "/tmp/gsi"))
RELEASES_BACK = int(os.environ.get("RELEASES_BACK", "1"))  # сколько последних релизов брать
START, END = "<!-- GSI-LIST:START -->", "<!-- GSI-LIST:END -->"


def gh(url):
    req = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json"})
    if TOKEN:
        req.add_header("Authorization", f"Bearer {TOKEN}")
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)


def run(*cmd):
    print("+", " ".join(cmd), flush=True)
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        print(r.stdout, r.stderr, sep="\n", flush=True)
        raise RuntimeError(f"Команда упала: {cmd[0]} (код {r.returncode})")
    return r.stdout.strip()


def to_img(path: pathlib.Path) -> pathlib.Path:
    """Превращает архив в один .img файл."""
    n = path.name
    if n.endswith(".img"):
        return path
    if n.endswith(".img.xz"):
        run("xz", "-d", "-T0", str(path)); return path.with_suffix("")
    if n.endswith(".img.gz"):
        run("gzip", "-d", str(path)); return path.with_suffix("")
    if n.endswith((".zip", ".7z")):
        out = WORK / "extract"
        shutil.rmtree(out, ignore_errors=True); out.mkdir()
        run("7z", "x", "-y", f"-o{out}", str(path)); path.unlink()
        for p in sorted(out.rglob("*"), key=lambda p: p.stat().st_size if p.is_file() else 0, reverse=True):
            if p.is_file() and p.suffix in (".xz", ".gz"):
                p = to_img(p)
            if p.is_file() and p.suffix == ".img":
                final = WORK / (path.name.rsplit(".", 1)[0] + ".img")
                p.rename(final); shutil.rmtree(out, ignore_errors=True)
                return final
        raise RuntimeError("в архиве нет .img")
    raise RuntimeError(f"неизвестный формат: {n}")


def detect_android(text):
    m = re.search(r"(?:android|a)[-_ ]?(1[3-9])\b", text, re.I) or re.search(r"\b(1[3-9])(?:\.\d)?\b", text)
    return m.group(1) if m else "?"


def main():
    sources = json.loads((ROOT / "sources.json").read_text())
    state = json.loads(STATE.read_text()) if STATE.exists() else {}
    WORK.mkdir(parents=True, exist_ok=True)

    for src in sources:
        try:
            releases = gh(f"https://api.github.com/repos/{src['repo']}/releases?per_page={RELEASES_BACK}")
        except Exception as e:
            print(f"[{src['name']}] пропуск, ошибка API: {e}")
            continue
        rx = re.compile(src["asset_regex"], re.I)
        for rel in releases[:RELEASES_BACK]:
            tag = rel["tag_name"]
            for a in rel["assets"]:
                if not rx.search(a["name"]):
                    continue
                key = f"{src['repo']}/{tag}/{a['name']}"
                if key in state:
                    print(f"[{src['name']}] {a['name']} уже загружен"); continue
                try:
                    local = WORK / a["name"]
                    run("curl", "-fL", "--retry", "3", "-o", str(local), a["browser_download_url"])
                    img = to_img(local)
                    dest = f"{REMOTE}/{src['repo'].replace('/', '_')}/{tag}"
                    run("rclone", "copy", str(img), dest)
                    link = run("rclone", "link", f"{dest}/{img.name}")
                    size = img.stat().st_size
                    img.unlink()
                except Exception as e:
                    print(f"[{src['name']}] {a['name']}: {e}")
                    for f in WORK.iterdir():
                        shutil.rmtree(f, ignore_errors=True) if f.is_dir() else f.unlink()
                    continue
                state[key] = {"name": src["name"], "tag": tag, "file": img.name,
                              "android": detect_android(f"{tag} {rel.get('name') or ''} {a['name']}"),
                              "size_mb": round(size / 2**20), "link": link,
                              "date": (rel.get("published_at") or "")[:10]}
                STATE.write_text(json.dumps(state, indent=2, ensure_ascii=False) + "\n")

    STATE.write_text(json.dumps(state, indent=2, ensure_ascii=False) + "\n")
    rows = ["| Сборка | Android | Версия | Файл (.img) | Размер | Дата | Google Drive |",
            "|---|---|---|---|---|---|---|"]
    for v in sorted(state.values(), key=lambda v: v["date"], reverse=True):
        rows.append(f"| {v['name']} | {v.get('android','?')} | `{v['tag']}` | `{v['file']}` | "
                    f"{v['size_mb']} MB | {v['date']} | [Скачать]({v['link']}) |")
    text = README.read_text()
    text = re.sub(re.escape(START) + ".*?" + re.escape(END),
                  lambda _: START + "\n" + "\n".join(rows) + "\n" + END, text, flags=re.S)
    README.write_text(text)


if __name__ == "__main__":
    main()
