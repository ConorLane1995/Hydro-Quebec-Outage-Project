# IMPORTS
import requests
import gzip 
import json
import time
import logging
from pathlib import Path
from datetime import datetime, timezone

logging.Formatter.converter = time.gmtime
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%SZ",
    handlers=[logging.FileHandler("collector.log"),logging.StreamHandler()],
)

# CONSTANTS
BASE_URL = "https://pannes.hydroquebec.com/pannes/donnees/v3_0/"
HEADERS = {"User-Agent": "mtl-outage-research/0.1 (conor.lane1995@gmail.com)"}
RAW_DIR = Path(__file__).parent / "records"
TIMEOUT = 20
POLL_SECONDS = 600


# Fetch the version, feed is a string either "bis" or "aip"
def fetch_version(feed):
    url = f"{BASE_URL}{feed}version.json"
    response = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
    response.raise_for_status()
    version = response.json()
    return version

def raw_path(feed, version):
    if not (len(version) == 14 and version.isdigit()):
        raise ValueError(f"unexpected version format: {version!r}")

    year = version[0:4]
    month = version[4:6]
    day = version[6:8]
    return RAW_DIR / feed / year / month / day / f"{version}.json.gz"

def poll_feed(feed):
    version = fetch_version(feed)
    path = raw_path(feed,version)

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
    while True:
        for feed in ["bis", "aip"]:
            try:
                status, version = poll_feed(feed)
                logging.info(f"feed={feed} status={status} version={version}")
            except (requests.RequestException, ValueError) as e:
                logging.warning(f"feed={feed} status=failed error={e!r}")
        time.sleep(POLL_SECONDS)