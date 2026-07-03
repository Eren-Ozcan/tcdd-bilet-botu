import datetime

from . import storage, tcdd_client

HELP_TEXT = (
    "TCDD Bilet Takip Botu\n\n"
    "Komutlar:\n"
    "/izle Kalkis;Varis;YYYY-AA-GG;SS:DD  - Yeni takip ekle (saat opsiyonel)\n"
    "  Ornek: /izle Ankara;Istanbul;2026-07-10\n"
    "  Ornek: /izle Ankara;Istanbul;2026-07-10;09:00\n"
    "/liste  - Aktif takiplerini goster\n"
    "/iptal <id>  - Belirtilen takibi sil\n"
    "/yardim  - Bu mesaji goster\n\n"
    "Bos yer bulundugunda buradan haber verilir. Bilet almak icin "
    "ebilet.tcddtasimacilik.gov.tr adresine gitmen gerekiyor, yerler cok "
    "hizli doluyor, bildirimi gorur gormez islem yap."
)


def handle_message(message, watches, stations):
    chat_id = message["chat"]["id"]
    text = (message.get("text") or "").strip()
    if not text:
        return None

    command, _, rest = text.partition(" ")
    command = command.split("@")[0].lower()
    rest = rest.strip()

    if command in ("/start", "/yardim", "/help"):
        return chat_id, HELP_TEXT
    if command == "/izle":
        return chat_id, _handle_izle(rest, chat_id, watches, stations)
    if command == "/liste":
        return chat_id, _handle_liste(chat_id, watches)
    if command == "/iptal":
        return chat_id, _handle_iptal(rest, chat_id, watches)
    if command.startswith("/"):
        return chat_id, "Anlamadim. Komutlar icin /yardim yazin."
    return None


def _handle_izle(rest, chat_id, watches, stations):
    parts = [p.strip() for p in rest.split(";")]
    if len(parts) < 3 or not all(parts[:3]):
        return (
            "Format hatali. Ornek:\n/izle Ankara;Istanbul;2026-07-10\n"
            "Saat belirtmek icin: /izle Ankara;Istanbul;2026-07-10;09:00"
        )

    kalkis_query, varis_query, tarih = parts[0], parts[1], parts[2]
    saat = parts[3] if len(parts) > 3 and parts[3] else None

    try:
        datetime.datetime.strptime(tarih, "%Y-%m-%d")
    except ValueError:
        return "Tarih formati hatali. YYYY-AA-GG seklinde girin, ornek: 2026-07-10"

    if saat:
        try:
            datetime.datetime.strptime(saat, "%H:%M")
        except ValueError:
            return "Saat formati hatali. SS:DD seklinde girin, ornek: 09:00"

    kalkis_matches = tcdd_client.find_stations(kalkis_query, stations)
    varis_matches = tcdd_client.find_stations(varis_query, stations)

    if not kalkis_matches:
        return f"'{kalkis_query}' icin istasyon bulunamadi."
    if not varis_matches:
        return f"'{varis_query}' icin istasyon bulunamadi."
    if len(kalkis_matches) > 1:
        names = ", ".join(ad for ad, _ in kalkis_matches[:8])
        return f"'{kalkis_query}' icin birden fazla istasyon bulundu, daha net yaz: {names}"
    if len(varis_matches) > 1:
        names = ", ".join(ad for ad, _ in varis_matches[:8])
        return f"'{varis_query}' icin birden fazla istasyon bulundu, daha net yaz: {names}"

    kalkis_ad, kalkis_id = kalkis_matches[0]
    varis_ad, varis_id = varis_matches[0]

    watch = {
        "id": storage.next_watch_id(watches),
        "chat_id": chat_id,
        "kalkis_ad": kalkis_ad,
        "kalkis_id": kalkis_id,
        "varis_ad": varis_ad,
        "varis_id": varis_id,
        "tarih": tarih,
        "saat": saat,
        "created_at": datetime.datetime.utcnow().isoformat(),
    }
    watches.append(watch)
    saat_txt = f" saat {saat}" if saat else ""
    return f"Takip eklendi (#{watch['id']}): {kalkis_ad} -> {varis_ad}, {tarih}{saat_txt}"


def _handle_liste(chat_id, watches):
    mine = [w for w in watches if w["chat_id"] == chat_id]
    if not mine:
        return "Aktif takibin yok. /izle ile ekleyebilirsin."
    lines = ["Aktif takiplerin:"]
    for w in mine:
        saat_txt = f" saat {w['saat']}" if w.get("saat") else ""
        lines.append(f"#{w['id']}: {w['kalkis_ad']} -> {w['varis_ad']}, {w['tarih']}{saat_txt}")
    return "\n".join(lines)


def _handle_iptal(rest, chat_id, watches):
    if not rest.isdigit():
        return "Kullanim: /iptal <id>  (id icin /liste yazabilirsin)"
    watch_id = int(rest)
    for i, w in enumerate(watches):
        if w["id"] == watch_id and w["chat_id"] == chat_id:
            watches.pop(i)
            return f"Takip #{watch_id} silindi."
    return f"#{watch_id} numarali takip bulunamadi."
