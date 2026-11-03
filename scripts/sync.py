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
    m = re.search(r"lineage-(\d\d)", text, re.I)
    if m:
        return str(int(m.group(1)) - 7)
    m = re.search(r"(?:android|a)[-_ ]?(1[3-9])\b", text, re.I) or re.search(r"\b(1[3-9])(?:\.\d)?\b", text)
    return m.group(1) if m else "?"


def releases_for(src):
    """Возвращает список (tag, published_date, [(name, url, size)]) от новых к старым."""
    kind = src.get("type", "github")
    if kind == "github":
        rels = gh(f"https://api.github.com/repos/{src['repo']}/releases?per_page={RELEASES_BACK}")
        return [(r["tag_name"], (r.get("published_at") or "")[:10],
                 [(aname, aurl, a["size"]) for a in r["assets"]],
                 r.get("name") or "") for r in rels[:RELEASES_BACK]]
    if kind == "sourceforge":
        import xml.etree.ElementTree as ET
        from email.utils import parsedate_to_datetime
        url = f"https://sourceforge.net/projects/{src['project']}/rss?path={src.get('path', '/')}"
        with urllib.request.urlopen(url, timeout=60) as r:
            root = ET.fromstring(r.read())
        skip = re.compile(src.get("skip_regex", r"/(History|Testing|Old|Archive)/"), re.I)
        seen, items = set(), []
        for it in root.iter("item"):
            path = it.findtext("title")
            if path in seen or skip.search(path):
                continue
            seen.add(path)
            d = parsedate_to_datetime(it.findtext("pubDate").replace(" UT", " GMT"))
            items.append((d, path, it.findtext("link")))
        items.sort(reverse=True)
        out = {}
        for d, path, link in items:
            folder = path.rsplit("/", 1)[0].strip("/") or "root"
            out.setdefault(folder, (folder, d.strftime("%Y-%m-%d"), [], ""))
            out[folder][2].append((path.rsplit("/", 1)[1], link, 0))
        return list(out.values())[:max(RELEASES_BACK, 3)]
    if kind == "telegram":
        import tg_fetch
        files = tg_fetch.list_files(src["channel"], src.get("asset_regex", r"\.(img|xz|gz|zip|7z)$"),
                                    src.get("scan_messages", 200))
        return [(f"tg{mid}", date, [(name, f"tg://{src['channel']}/{mid}", size)], "")
                for mid, name, size, date in files[:max(RELEASES_BACK, 3)]]
    if kind == "url":  # прямые ссылки, добавленные вручную
        return [(f["tag"], f.get("date", ""), [(f["file"], f["url"], 0)], "") for f in src["files"]]
    raise ValueError(f"неизвестный type: {kind}")


def main():
    sources = json.loads((ROOT / "sources.json").read_text())
    state = json.loads(STATE.read_text()) if STATE.exists() else {}
    WORK.mkdir(parents=True, exist_ok=True)

    for src in sources:
        sid = src.get("repo") or src.get("project") or src["name"]
        try:
            releases = releases_for(src)
        except Exception as e:
            print(f"[{src['name']}] пропуск, ошибка API: {e}")
            continue
        rx = re.compile(src.get("asset_regex", "."), re.I)
        for tag, date, assets, title in releases:
            for aname, aurl, _ in assets:
                if not rx.search(aname):
                    continue
                key = f"{sid}/{tag}/{aname}"
                if key in state:
                    print(f"[{src['name']}] {a['name']} уже загружен"); continue
                try:
                    local = WORK / aname
                    if aurl.startswith("tg://"):
                        import tg_fetch
                        ch, mid = aurl[5:].rsplit("/", 1)
                        print(f"+ telegram {ch}/{mid}", flush=True)
                        tg_fetch.download(ch, int(mid), local)
                    else:
                        run("curl", "-fL", "--retry", "3", "-o", str(local), aurl)
                    img = to_img(local)
                    dest = f"{REMOTE}/{sid.replace('/', '_')}/{tag.replace('/', '_')}"
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
                              "android": detect_android(f"{tag} {title} {aname}"),
                              "size_mb": round(size / 2**20), "link": link,
                              "date": date}
                STATE.write_text(json.dumps(state, indent=2, ensure_ascii=False) + "\n")

    render(state)


def render(state):
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
