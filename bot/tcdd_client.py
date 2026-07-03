import json
import os

from . import config

_TR_MAP = str.maketrans({
    "İ": "i", "I": "i", "ı": "i",
    "Ş": "s", "ş": "s",
    "Ç": "c", "ç": "c",
    "Ö": "o", "ö": "o",
    "Ü": "u", "ü": "u",
    "Ğ": "g", "ğ": "g",
})


def normalize(text):
    return text.translate(_TR_MAP).lower()


def load_stations():
    if not os.path.exists(config.STATIONS_FILE):
        return {}
    with open(config.STATIONS_FILE, "r", encoding="utf-8") as f:
        content = f.read().strip()
        return json.loads(content) if content else {}


def ensure_stations():
    return load_stations()


def find_stations(query, stations):
    q = normalize(query.strip())
    if not q:
        return []
    matches = [(ad, sid) for ad, sid in stations.items() if q in normalize(ad)]
    matches.sort(key=lambda pair: len(pair[0]))
    return matches
