import datetime
import logging
import logging.handlers
import os

from . import commands, config, storage, tcdd_browser, tcdd_client, telegram_client

logger = logging.getLogger(__name__)


def setup_logging():
    os.makedirs(config.DATA_DIR, exist_ok=True)
    handler = logging.handlers.RotatingFileHandler(
        config.LOG_FILE, maxBytes=1_000_000, backupCount=1, encoding="utf-8"
    )
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    root.addHandler(handler)


def process_telegram_commands(watches, stations):
    offset = storage.load_offset()
    updates = telegram_client.get_updates(offset + 1 if offset else None)
    last_update_id = offset
    for update in updates:
        last_update_id = update["update_id"]
        message = update.get("message")
        if not message:
            continue
        result = commands.handle_message(message, watches, stations)
        if result is None:
            continue
        chat_id, reply = result
        try:
            telegram_client.send_message(chat_id, reply)
        except Exception as e:
            logger.error("Telegram mesaji gonderilemedi: %s", e)
    if last_update_id != offset:
        storage.save_offset(last_update_id)


def expire_old_watches(watches, seen):
    today = datetime.date.today().isoformat()
    active = []
    for w in watches:
        if w["tarih"] < today:
            seen.pop(str(w["id"]), None)
        else:
            active.append(w)
    return active


def check_watch(watch, seen):
    watch_id = str(watch["id"])
    seen_keys = set(seen.get(watch_id, []))
    new_findings = []

    try:
        results = tcdd_browser.search_available_seats(
            watch["kalkis_ad"], watch["varis_ad"], watch["tarih"], watch.get("saat")
        )
    except Exception as e:
        logger.error("[%s] tarayici sorgusu basarisiz: %s", watch_id, e)
        return []

    current_keys = set()
    for r in results:
        key = f"{r['train_no']}:{r['wagon_label']}:{r['departure_time']}"
        current_keys.add(key)
        if key not in seen_keys:
            new_findings.append(r)

    seen[watch_id] = list(current_keys)
    return new_findings


def notify(watch, findings):
    if not findings:
        return
    lines = [
        f"Bos yer bulundu! {watch['kalkis_ad']} -> {watch['varis_ad']} ({watch['tarih']})",
        "",
    ]
    for f in findings[:20]:
        lines.append(
            f"- {f['train_name']} (Tren {f['train_no']}) | {f['departure_time']} -> "
            f"{f['arrival_time']} | {f['wagon_label']} | {f['seats_display']} koltuk | "
            f"{f['price']}"
        )
    if len(findings) > 20:
        lines.append(f"... ve {len(findings) - 20} yer daha")
    lines.append("")
    lines.append(
        "Hemen ebilet.tcddtasimacilik.gov.tr adresinden satin alabilirsin, "
        "yerler hizli doluyor."
    )
    try:
        telegram_client.send_message(watch["chat_id"], "\n".join(lines))
    except Exception as e:
        logger.error("Bildirim gonderilemedi: %s", e)


def main():
    logger.info("Calisma basladi")
    try:
        stations = tcdd_client.ensure_stations()
        watches = storage.load_watches()
        seen = storage.load_seen()

        process_telegram_commands(watches, stations)
        watches = expire_old_watches(watches, seen)

        for watch in watches:
            findings = check_watch(watch, seen)
            notify(watch, findings)

        storage.save_watches(watches)
        storage.save_seen(seen)
    except Exception:
        logger.exception("Calisma hata ile sonlandi")
        raise
    else:
        logger.info("Calisma tamamlandi (%d takip kontrol edildi)", len(watches))


if __name__ == "__main__":
    setup_logging()
    main()
