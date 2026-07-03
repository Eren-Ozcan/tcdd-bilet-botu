"""
TCDD ebilet sitesini gercek bir tarayiciyla (Playwright/Chromium) suren
sorgu katmani.

TCDD'nin JSON API'si (api-yebsp.tcddtasimacilik.gov.tr) artik tarayici
disindaki istemcileri (curl, requests, hatta headless fetch) aginda
reddediyor - bu yuzden gercek siteyi (ebilet.tcddtasimacilik.gov.tr)
bir tarayicida acip formu doldurup sonuc HTML'ini okuyoruz, aynen
gercek bir kullanicinin yaptigi gibi.
"""

from playwright.sync_api import sync_playwright

from .tcdd_client import normalize

SITE_URL = "https://ebilet.tcddtasimacilik.gov.tr/"
NAV_TIMEOUT_MS = 30000


def _close_rental_modal(page):
    modal = page.query_selector("#rentalCarInformation")
    if modal and "show" in (modal.get_attribute("class") or ""):
        close_btn = modal.query_selector("button.close")
        if close_btn:
            close_btn.click()
            page.wait_for_timeout(500)


def _js_click(page, element):
    page.evaluate("(el) => el.click()", element)


def _select_station(page, trigger_id, station_name):
    """
    Kalkis/varis alanina tiklayip acilan tam istasyon listesinden (461
    istasyon) metin eslesmesiyle dogru olani secer. Site artik arama
    kutusunu her zaman gostermiyor, bu yuzden dogrudan liste icinde arama
    yapiyoruz.
    """
    trigger = page.wait_for_selector(f"#{trigger_id}", timeout=15000, state="visible")
    box = trigger.bounding_box()
    page.mouse.click(box["x"] + 5, box["y"] + 5)
    page.wait_for_timeout(1200)

    query = normalize(station_name)
    buttons = page.query_selector_all(".dropdown-menu.show button.dropdown-item.station")
    for b in buttons:
        loc_el = b.query_selector(".textLocation")
        text = normalize(_text(loc_el))
        if query in text:
            b.scroll_into_view_if_needed()
            _js_click(page, b)
            page.wait_for_timeout(500)
            return True
    return False


def _set_date(page, tarih):
    date_input = page.wait_for_selector(
        "input.calenderPurpleImg, .departureDate input[readonly]", timeout=15000
    )
    _js_click(page, date_input)
    page.wait_for_timeout(700)

    for _ in range(6):
        cell = page.query_selector(f'td[data-date="{tarih}"]')
        if cell:
            _js_click(page, cell)
            page.wait_for_timeout(400)
            return True
        next_btn = page.query_selector(".daterangepicker .next.available")
        if not next_btn:
            break
        _js_click(page, next_btn)
        page.wait_for_timeout(400)
    return False


def _text(el):
    if not el:
        return ""
    return " ".join((el.text_content() or "").split())


def _parse_cards(page, saat=None):
    page.wait_for_timeout(4000)
    cards = page.query_selector_all("div.card[id^='gidis']")
    results = []

    for card in cards:
        dep_el = card.query_selector("span.textDepartureArea time")
        dep_time = ""
        if dep_el:
            dep_time = dep_el.get_attribute("datetime") or _text(dep_el)

        if saat and dep_time and saat not in dep_time:
            continue

        header_price = _text(
            card.query_selector(".card-header .priceArea .price")
        ).lower()
        if header_price == "dolu":
            continue

        toggle = card.query_selector(".card-header [data-toggle='collapse']")
        if toggle:
            target_sel = toggle.get_attribute("data-target") or ""
            collapse_el = page.query_selector(target_sel) if target_sel else None
            already_open = collapse_el and "show" in (
                collapse_el.get_attribute("class") or ""
            )
            if not already_open:
                _js_click(page, toggle)
                page.wait_for_timeout(900)

        wagon_btns = card.query_selector_all("button[id*='-vagonType-']")
        available_btns = [
            b for b in wagon_btns if "disabled" not in (b.get_attribute("class") or "")
        ]
        available_btns = [
            b for b in available_btns if "tekerlekli" not in _text(b).lower()
        ]
        if not available_btns:
            continue

        arr_el = card.query_selector("span.textArrivalArea time")
        arr_time = arr_el.get_attribute("datetime") if arr_el else _text(arr_el)

        train_name = _text(
            card.query_selector(".seferDepartureArea .textDepartureArrival p.col")
        )
        header = card.query_selector(".card-header")
        train_no = (header.get_attribute("id") or "").replace("sefer", "").replace("-", "") if header else ""

        for wagon_btn in available_btns:
            wtype_el = wagon_btn.query_selector("span.mb-0")
            wagon_label = _text(wtype_el) or "?"
            price = _text(wagon_btn.query_selector(".priceArea .price"))
            seats = _text(wagon_btn.query_selector(".priceArea .emptySeat")).strip("()")

            results.append({
                "train_no": train_no or "?",
                "train_name": train_name or "?",
                "departure_time": dep_time or "?",
                "arrival_time": arr_time or "?",
                "wagon_label": wagon_label,
                "seats_display": seats or "?",
                "price": price or "?",
            })

    return results


def search_available_seats(kalkis_ad, varis_ad, tarih, saat=None):
    """
    kalkis_ad / varis_ad: TCDD istasyon adi (ekrana yazilan kisim, ID gerekmez)
    tarih: 'YYYY-MM-DD'
    saat: 'HH:MM' ya da None (verilirse sadece o saate en yakin sefer filtrelenir)

    Donen: search_seferler+get_available_seats'in eski JSON API sonucuna
    benzer, ama tarayici sayfasindan kazinmis liste of dict.
    """
    data_date = tarih  # zaten YYYY-MM-DD

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-dev-shm-usage",
            ],
        )
        try:
            page = browser.new_page(
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
                ),
                viewport={"width": 1280, "height": 900},
            )
            page.add_init_script(
                "Object.defineProperty(navigator, 'webdriver', {get: () => undefined});"
            )
            page.goto(SITE_URL, timeout=NAV_TIMEOUT_MS, wait_until="domcontentloaded")
            page.wait_for_timeout(1500)

            _close_rental_modal(page)
            _select_station(page, "fromTrainInput", kalkis_ad)
            page.wait_for_timeout(400)
            _select_station(page, "toTrainInput", varis_ad)
            page.wait_for_timeout(400)
            _set_date(page, data_date)
            page.wait_for_timeout(300)

            search_btn = page.wait_for_selector("#searchSeferButton", timeout=15000)
            _js_click(page, search_btn)

            results = _parse_cards(page, saat)
            return results
        finally:
            browser.close()
