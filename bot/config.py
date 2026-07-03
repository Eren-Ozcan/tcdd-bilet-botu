import os

TCDD_BASE_URL = "https://api-yebsp.tcddtasimacilik.gov.tr"
TCDD_AUTH_HEADER = "Basic ZGl0cmF2b3llYnNwOmRpdHJhMzQhdm8u"
SEFER_SORGULA_URL = f"{TCDD_BASE_URL}/sefer/seferSorgula"
VAGON_SEAT_URL = f"{TCDD_BASE_URL}/vagon/vagonHaritasindanYerSecimi"
ISTASYON_YUKLE_URL = f"{TCDD_BASE_URL}/istasyon/istasyonYukle"

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"

_ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(_ROOT_DIR, "data")
STATIONS_FILE = os.path.join(DATA_DIR, "stations.json")
WATCHES_FILE = os.path.join(DATA_DIR, "watches.json")
SEEN_FILE = os.path.join(DATA_DIR, "seen.json")
OFFSET_FILE = os.path.join(DATA_DIR, "offset.json")

# Bir takip basina kontrol edilecek en fazla sefer sayisi (asiri istek atmamak icin)
MAX_SEFER_PER_WATCH = 6
# Ardisik TCDD istekleri arasinda bekleme suresi (saniye)
REQUEST_DELAY_SECONDS = 1.0
HTTP_TIMEOUT = 15
