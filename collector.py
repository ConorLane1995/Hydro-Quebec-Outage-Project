# IMPORTS
import requests
import gzip 
import json
import time
import logging
from pathlib import Path
from datetime import datetime, timezone
import signal
from zoneinfo import ZoneInfo

# CONSTANTS
BASE_URL = "https://pannes.hydroquebec.com/pannes/donnees/v3_0/"
HEADERS = {"User-Agent": "mtl-outage-research/0.1 (conor.lane1995@gmail.com)"}
RAW_DIR = Path(__file__).parent / "records"
LOG_DIR = Path(__file__).parent / "logs"
TIMEOUT = 20
POLL_SECONDS = 600
MTL = ZoneInfo("America/Toronto")

logging.Formatter.converter = time.gmtime
LOG_DIR.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%SZ",
    handlers=[logging.FileHandler(LOG_DIR / "collector.log"),logging.StreamHandler()],
)

# Fetch the version, feed is a string either "bis" or "aip"
def fetch_version(feed):
    url = f"{BASE_URL}{feed}version.json"
    response = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
    response.raise_for_status()
    version = response.json()
    return version

def raw_path(feed, ts_utc):
    return RAW_DIR / feed / f"{ts_utc:%Y/%m/%d}" / f"{ts_utc:%Y%m%dT%H%M%SZ}.json.gz"

def version_to_utc(version, fetched_utc):
    naive = datetime.strptime(version, "%Y%m%d%H%M%S")
    candidates = [naive.replace(tzinfo=MTL, fold=f).astimezone(timezone.utc) for f in (0, 1)]
    valid = [c for c in candidates if c <= fetched_utc]
    return max(valid) if valid else min(candidates)

def poll_feed(feed):
    version = fetch_version(feed)
    path = raw_path(feed, version_to_utc(version, datetime.now(timezone.utc)))

    if path.exists():
        return "unchanged", version

    url = f"{BASE_URL}{feed}markers{version}.json"
    response = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
    response.raise_for_status()
    response.json()

    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_name(path.name + ".tmp")

    with gzip.open(tmp_path, "wb") as f:
        f.write(response.content)
    tmp_path.replace(path)
    return "saved", version

if __name__ == "__main__":
    logging.info(f"collector started, polling every {POLL_SECONDS}s")
    try:
        while True:
            for feed in ["bis", "aip"]:
                try:
                    status, version = poll_feed(feed)
                    logging.info(f"feed={feed} status={status} version={version}")
                except (requests.RequestException, ValueError) as e:
                    logging.warning(f"feed={feed} status=failed error={e!r}")
            time.sleep(POLL_SECONDS)
    except Exception:
        logging.exception("collector crashed")
        raise                
       