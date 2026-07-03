import os

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"

_ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(_ROOT_DIR, "data")
STATIONS_FILE = os.path.join(DATA_DIR, "stations.json")
WATCHES_FILE = os.path.join(DATA_DIR, "watches.json")
SEEN_FILE = os.path.join(DATA_DIR, "seen.json")
OFFSET_FILE = os.path.join(DATA_DIR, "offset.json")

HTTP_TIMEOUT = 15
