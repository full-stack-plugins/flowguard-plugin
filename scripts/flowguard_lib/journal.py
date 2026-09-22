"""追加式审计日志：.flowguard/journal/events.jsonl，每行 {ts, scope, event, detail}。"""
import datetime
import json
from pathlib import Path


def _file(root):
    d = Path(root) / ".flowguard" / "journal"
    d.mkdir(parents=True, exist_ok=True)
    return d / "events.jsonl"


def append(root, scope, event, detail=None):
    rec = {
        "ts": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "scope": scope,
        "event": event,
        "detail": detail or {},
    }
    with _file(root).open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec, ensure_ascii=False) + "\n")


def read(root):
    f = _file(root)
    if not f.exists():
        return []
    return [json.loads(line) for line in f.read_text(encoding="utf-8").splitlines() if line.strip()]
