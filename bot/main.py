import datetime
import time

from . import commands, config, storage, tcdd_client, telegram_client


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
        seferler = tcdd_client.search_seferler(
            watch["kalkis_ad"], watch["kalkis_id"],
            watch["varis_ad"], watch["varis_id"],
            watch["tarih"],
        )
    except Exception as e:
        print(f"[{watch_id}] sefer sorgusu basarisiz: {e}")
        return []

    if watch.get("saat"):
        filtered = []
        for sefer in seferler:
            try:
                sefer_time = datetime.datetime.strptime(
                    sefer["binisTarih"], "%b %d, %Y %I:%M:%S %p"
                )
            except (KeyError, ValueError):
                continue
            if sefer_time.strftime("%H:%M") == watch["saat"]:
                filtered.append(sefer)
        seferler = filtered

    seferler = seferler[: config.MAX_SEFER_PER_WATCH]

    for sefer in seferler:
        sefer_id = sefer.get("seferId")
        tren_adi = sefer.get("trenAdi", "?")
        binis_tarih = sefer.get("binisTarih", "?")
        for vagon_tipi in sefer.get("vagonTipleriBosYerUcret", []):
            for vagon in vagon_tipi.get("vagonListesi", []):
                vagon_sira_no = vagon.get("vagonSiraNo")
                time.sleep(config.REQUEST_DELAY_SECONDS)
                try:
                    seat_numbers = tcdd_client.get_available_seats(
                        sefer_id, vagon_sira_no, watch["kalkis_ad"], watch["varis_ad"]
                    )
                except Exception as e:
                    print(f"[{watch_id}] koltuk sorgusu basarisiz: {e}")
                    continue
                for koltuk_no in seat_numbers:
                    key = f"{sefer_id}:{vagon_sira_no}:{koltuk_no}"
                    if key in seen_keys:
                        continue
                    seen_keys.add(key)
                    new_findings.append({
                        "tren_adi": tren_adi,
                        "binis_tarih": binis_tarih,
                        "vagon_sira_no": vagon_sira_no,
                        "koltuk_no": koltuk_no,
                    })

    seen[watch_id] = list(seen_keys)
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
            f"- {f['tren_adi']} | {f['binis_tarih']} | Vagon {f['vagon_sira_no']} | "
            f"Koltuk {f['koltuk_no']}"
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
