import requests
import gzip 
import json
import time
import logging
from pathlib import Path
from datetime import datetime, timezone
import signal
from zoneinfo import ZoneInfo
import hashlib

# CONSTANTS
BASE_URL = "https://donnees.montreal.ca/dataset/667342f7-f667-4c3c-9837-65e81312cd8d/resource"
HEADERS = {"User-Agent": "mtl-outage-research/0.1 (conor.lane1995@gmail.com)"}
RAW_DIR = Path(__file__).parent / "records" / "roadwork_records"
LOG_DIR = Path(__file__).parent / "roadwork_logs"
TIMEOUT = 20
POLL_SECONDS = 4 * 3600
MTL = ZoneInfo("America/Toronto")
FILES = {
    "entraves": (f"{BASE_URL}/cc41b532-f12d-40fb-9f55-eb58c9a2b12b/download/entraves-travaux-en-cours.csv", "id"),
    "impacts":  (f"{BASE_URL}/a2bc8014-488c-495d-941b-e7ae1999d1bd/download/impacts-entraves-travaux-en-cours.csv", "id_request"),
    "infos":    (f"{BASE_URL}/535c090c-2f74-4398-83ec-2771a6ce7174/download/informations-complementaires-entraves-travaux.json", None),
    }

logging.Formatter.converter = time.gmtime
LOG_DIR.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%SZ",
    handlers=[logging.FileHandler(LOG_DIR / "roadwork_collector.log"),logging.StreamHandler()],
)


def fetch(name, url, id_col):
    response = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
    response.raise_for_status()
    content = response.content

    if url.endswith(".json"):
        json.loads(content)          # raises ValueError if it isn't valid JSON
    else:
        header = content.split(b"\n", 1)[0].decode("utf-8-sig")
        if id_col not in header.split(","):
            raise ValueError(f"{name}: unexpected CSV header {header[:100]!r}")
    return content


def last_saved_hash(name):
    files = list((RAW_DIR / name).rglob("*.gz"))
    if not files:
        return None
    newest = max(files, key=lambda p: p.name)
    with gzip.open(newest, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()
    return newest

def save(name,url,content):
    ext = Path(url).suffix
    now = datetime.now(timezone.utc)
    path = RAW_DIR / name / f"{now:%Y/%m/%d}" / f"{name}_{now:%Y%m%dT%H%M%SZ}{ext}.gz"
    
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_name(path.name + ".tmp")
    with gzip.open(tmp_path, "wb") as f:
        f.write(content)
    tmp_path.replace(path)
    return path


if __name__ == "__main__":
    logging.info(f"roadwork archiver started, polling every {POLL_SECONDS}s")
    last_hash = {name: last_saved_hash(name) for name in FILES}   # restore state after a restart
    try:
        while True:
            for name, (url, id_col) in FILES.items():
                try:
                    content = fetch(name, url, id_col)
                    new_hash = hashlib.sha256(content).hexdigest()
                    if new_hash == last_hash[name]:
                        logging.info(f"file={name} status=unchanged")
                    else:
                        path = save(name, url, content)
                        last_hash[name] = new_hash
                        logging.info(f"file={name} status=saved path={path}")
                except (requests.RequestException, ValueError) as e:
                       logging.warning(f"file={name} status=failed error={e!r}")
            time.sleep(POLL_SECONDS)
    except Exception:
        logging.exception("roadwork archiver crashed")
        raise