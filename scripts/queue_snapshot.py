#!/usr/bin/env python3
"""Снимок очереди из GitHub Actions → queue.json (ветка status). Запускается по расписанию каждые 5 минут,
поэтому очередь на сайте верна, даже если сами загрузки её не обновили."""
import json, os, sys, urllib.request
sys.path.insert(0, os.path.dirname(__file__))
import queue_status

REPO = os.environ["GITHUB_REPOSITORY"]
TOKEN = os.environ["GITHUB_TOKEN"]


def api(path):
    req = urllib.request.Request(f"https://api.github.com/repos/{REPO}/{path}",
                                 headers={"Authorization": f"Bearer {TOKEN}", "Accept": "application/vnd.github+json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)


def jobs_of(run_id):
    out, page = [], 1
    while True:
        d = api(f"actions/runs/{run_id}/jobs?per_page=100&page={page}")
        out += d["jobs"]
        if len(out) >= d["total_count"] or not d["jobs"]:
            return out
        page += 1


items = []
for wf in ("sync-gsi.yml", "build-mystic.yml"):
    runs = api(f"actions/workflows/{wf}/runs?per_page=5")["workflow_runs"]
    active = [r for r in runs if r["status"] != "completed"] or runs[:1]
    for r in active[:2]:
        for j in jobs_of(r["id"]):
            if j["name"] in ("plan", "sync", "build"):
                continue
            st = {"in_progress": "in_progress", "completed": "success" if j["conclusion"] == "success" else "failure"}.get(j["status"], "queued")
            if j["status"] == "completed" and j["conclusion"] in ("cancelled", "skipped"):
                continue
            it = {"file": j["name"], "name": "", "status": st}
            if j.get("started_at"):
                it["started"] = j["started_at"]
            if j.get("completed_at") and st in ("success", "failure"):
                it["finished"] = j["completed_at"]
            items.append(it)

order = {"in_progress": 0, "queued": 1, "success": 2, "failure": 2}
items.sort(key=lambda i: order[i["status"]])
done = sorted([i for i in items if order[i["status"]] == 2], key=lambda i: i.get("finished", ""), reverse=True)[:40]
items = [i for i in items if order[i["status"]] < 2] + done
queue_status.update(lambda q: q.update(items=items))
print("queue:", len(items))
