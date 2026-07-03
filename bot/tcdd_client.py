import datetime
import json
import os

import requests

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


def _headers():
    return {
        "Authorization": config.TCDD_AUTH_HEADER,
        "Content-Type": "application/json",
        "Accept": "*/*",
        "Accept-Language": "en-US,tr-TR;q=0.8,tr;q=0.5,en;q=0.3",
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
        ),
        "Origin": "https://bilet.tcdd.gov.tr",
        "Referer": "https://bilet.tcdd.gov.tr/",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "cross-site",
    }


def _post(url, body):
    resp = requests.post(url, json=body, headers=_headers(), timeout=config.HTTP_TIMEOUT)
    if not resp.ok:
        print(f"TCDD HTTP {resp.status_code} - {url}")
        print(f"Istek govdesi: {json.dumps(body, ensure_ascii=False)}")
        print(f"Yanit govdesi: {resp.text[:2000]!r}")
    resp.raise_for_status()
    return resp


def load_stations():
    if not os.path.exists(config.STATIONS_FILE):
        return {}
    with open(config.STATIONS_FILE, "r", encoding="utf-8") as f:
        content = f.read().strip()
        return json.loads(content) if content else {}


def save_stations(stations):
    os.makedirs(os.path.dirname(config.STATIONS_FILE), exist_ok=True)
    with open(config.STATIONS_FILE, "w", encoding="utf-8") as f:
        json.dump(stations, f, ensure_ascii=False, indent=2, sort_keys=True)


def fetch_stations_from_api():
    body = {"kanalKodu": "3", "dil": 1, "tarih": "Nov 10, 2011 12:00:00 AM", "satisSorgu": True}
    resp = _post(config.ISTASYON_YUKLE_URL, body)
    data = resp.json()
    return {s["istasyonAdi"]: s["istasyonId"] for s in data["istasyonBilgileriList"]}


def ensure_stations():
    stations = load_stations()
    if not stations:
        try:
            stations = fetch_stations_from_api()
            save_stations(stations)
        except Exception as e:
            print(f"Istasyon listesi API'den cekilemedi, bos liste ile devam: {e}")
    return stations


def find_stations(query, stations):
    q = normalize(query.strip())
    if not q:
        return []
    matches = [(ad, sid) for ad, sid in stations.items() if q in normalize(ad)]
    matches.sort(key=lambda pair: len(pair[0]))
    return matches


def _format_date(date_str):
    return datetime.datetime.strptime(date_str, "%Y-%m-%d").strftime("%b %d, %Y")


def search_seferler(kalkis_ad, kalkis_id, varis_ad, varis_id, tarih):
    body = {
        "kanalKodu": 3,
        "dil": 0,
        "seferSorgulamaKriterWSDVO": {
            "satisKanali": 3,
            "binisIstasyonu": kalkis_ad,
            "inisIstasyonu": varis_ad,
            "binisIstasyonId": kalkis_id,
            "inisIstasyonId": varis_id,
            "binisIstasyonu_isHaritaGosterimi": False,
            "inisIstasyonu_isHaritaGosterimi": False,
            "seyahatTuru": 1,
            "gidisTarih": f"{_format_date(tarih)} 00:00:00 AM",
            "bolgeselGelsin": False,
            "islemTipi": 0,
            "yolcuSayisi": 1,
            "aktarmalarGelsin": True,
        },
    }
    resp = _post(config.SEFER_SORGULA_URL, body)
    data = resp.json()
    if data.get("cevapBilgileri", {}).get("cevapKodu") != "000":
        return []
    return data.get("seferSorgulamaSonucList", [])


def get_available_seats(sefer_id, vagon_sira_no, kalkis_ad, varis_ad):
    body = {
        "kanalKodu": "3",
        "dil": 0,
        "seferBaslikId": sefer_id,
        "vagonSiraNo": vagon_sira_no,
        "binisIst": kalkis_ad,
        "InisIst": varis_ad,
    }
    resp = _post(config.VAGON_SEAT_URL, body)
    data = resp.json()
    if data.get("cevapBilgileri", {}).get("cevapKodu") != "000":
        return []
    seats = data.get("vagonHaritasiIcerikDVO", {}).get("koltukDurumlari", [])
    return [s["koltukNo"] for s in seats if s.get("durum") == 0]
