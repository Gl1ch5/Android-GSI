#!/usr/bin/env python3
"""Очередь загрузки в файле queue.json на отдельной ветке `status`.
Сайт читает его через raw.githubusercontent.com — без GitHub API и его лимитов.

  queue_status.py init            (ITEMS=<json из плана>)  — новая очередь, всё «queued»
  queue_status.py set <file> <in_progress|success|failure>
"""
import datetime
import json
import os
import random
import subprocess
import sys
import tempfile
import time

BRANCH = "status"
KEEP_DONE = 40


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")


def git(*a, cwd=None, check=True):
    return subprocess.run(["git", *a], cwd=cwd, check=check, capture_output=True, text=True)


def update(fn):
    for attempt in range(10):
        tmp = tempfile.mkdtemp()
        try:
            has = git("fetch", "-q", "origin", f"{BRANCH}:refs/remotes/origin/{BRANCH}", check=False).returncode == 0
            if has:
                git("worktree", "add", "-q", "--detach", tmp, f"origin/{BRANCH}")
            else:
                git("worktree", "add", "-q", "--detach", tmp)
                git("checkout", "-q", "--orphan", "tmp-status", cwd=tmp)
                git("rm", "-rqf", ".", cwd=tmp, check=False)
            path = os.path.join(tmp, "queue.json")
            q = json.load(open(path)) if os.path.exists(path) else {"items": []}
            fn(q)
            q["updated"] = now()
            with open(path, "w") as f:
                json.dump(q, f, ensure_ascii=False, indent=1)
            git("add", "queue.json", cwd=tmp)
            git("commit", "-qm", "queue", cwd=tmp, check=False)
            if git("push", "-q", "origin", f"HEAD:refs/heads/{BRANCH}", cwd=tmp, check=False).returncode == 0:
                return
        finally:
            git("worktree", "remove", "--force", tmp, check=False)
        time.sleep(random.uniform(1, 4) * (attempt + 1))
    print("queue_status: не удалось обновить очередь", file=sys.stderr)


def main():
    cmd = sys.argv[1]
    if cmd == "init":
        items = json.loads(os.environ.get("ITEMS") or "[]")
        run = os.environ.get("GITHUB_RUN_ID", "")

        def fn(q):
            done = [i for i in q.get("items", []) if i["status"] in ("success", "failure")][:KEEP_DONE]
            new = [{"file": i["file"], "name": i.get("name", ""), "status": "queued", "run": run} for i in items]
            names = {i["file"] for i in new}
            q["items"] = new + [i for i in done if i["file"] not in names]
            q["run"] = run
        update(fn)
    elif cmd == "set":
        fname, status = sys.argv[2], sys.argv[3]

        def fn(q):
            items = q.setdefault("items", [])
            it = next((i for i in items if i["file"] == fname), None)
            if not it:
                it = {"file": fname, "name": ""}
                items.insert(0, it)
            it["status"] = status
            it["started" if status == "in_progress" else "finished"] = now()
            if status in ("success", "failure"):  # готовые — наверх списка завершённых
                items.remove(it)
                active = [i for i in items if i["status"] in ("queued", "in_progress")]
                done = [i for i in items if i["status"] not in ("queued", "in_progress")]
                q["items"] = active + [it] + done[:KEEP_DONE - 1]
        update(fn)


if __name__ == "__main__":
    main()
