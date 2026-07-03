import requests

from . import config


def get_updates(offset=None):
    params = {"timeout": 0}
    if offset is not None:
        params["offset"] = offset
    resp = requests.get(
        f"{config.TELEGRAM_API_URL}/getUpdates", params=params, timeout=config.HTTP_TIMEOUT
    )
    resp.raise_for_status()
    return resp.json().get("result", [])


def send_message(chat_id, text):
    resp = requests.post(
        f"{config.TELEGRAM_API_URL}/sendMessage",
        json={"chat_id": chat_id, "text": text, "disable_web_page_preview": True},
        timeout=config.HTTP_TIMEOUT,
    )
    resp.raise_for_status()
    return resp.json()
