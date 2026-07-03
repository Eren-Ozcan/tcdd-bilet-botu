import datetime

from . import commands, storage, tcdd_browser, tcdd_client, telegram_client


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
            print(f"Telegram mesaji gonderilemedi: {e}")
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
        print(f"[{watch_id}] tarayici sorgusu basarisiz: {e}")
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
        print(f"Bildirim gonderilemedi: {e}")


def main():
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


if __name__ == "__main__":
    main()
