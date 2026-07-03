import json
import os

from . import config


def _load(path, default):
    if not os.path.exists(path):
        return default
    with open(path, "r", encoding="utf-8") as f:
        content = f.read().strip()
        return json.loads(content) if content else default


def _save(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_watches():
    return _load(config.WATCHES_FILE, [])


def save_watches(watches):
    _save(config.WATCHES_FILE, watches)


def load_seen():
    return _load(config.SEEN_FILE, {})


def save_seen(seen):
    _save(config.SEEN_FILE, seen)


def load_offset():
    data = _load(config.OFFSET_FILE, {"update_id": 0})
    return data.get("update_id", 0)


def save_offset(update_id):
    _save(config.OFFSET_FILE, {"update_id": update_id})


def next_watch_id(watches):
    return max((w["id"] for w in watches), default=0) + 1
