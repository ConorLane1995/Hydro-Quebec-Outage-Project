import requests
from collections import Counter
import json

headers = {"User-Agent": "mtl-outage-research/0.1 (conor.lane1995@gmail.com)"}
url = "https://pannes.hydroquebec.com/pannes/donnees/v3_0/bisversion.json"
response = requests.get(url, headers=headers, timeout=20)
response.raise_for_status()
version = response.json()
print(version, type(version))


markers_url = f"https://pannes.hydroquebec.com/pannes/donnees/v3_0/bismarkers{version}.json"
markers_response = requests.get(markers_url, headers=headers, timeout=20)
markers_response.raise_for_status()
data = markers_response.json()
print(data.keys(),len(data["pannes"]))


types = [record[3] for record in data["pannes"]]
# print(Counter(types))

print("P",Counter([record[6] for record in data["pannes"] if record[3] == "P"]))
print("I",Counter([record[6] for record in data["pannes"] if record[3] == "I"]))

mtl = []
for record in data["pannes"]:
    lon, lat = json.loads(record[4])
    if 45.41 <= lat <= 45.70 and -73.98 <= lon <= -73.48:
        mtl.append(record)

print(len(mtl))

print(Counter([record[3] for record in mtl]))


# forever:
#     for each feed (bis, aip):
#         try:
#             get the version
#             if we already saved a file for this version → note "unchanged", move on
#             otherwise → fetch the markers, save the raw bytes gzipped, note "saved"
#         except any network/HTTP error:
#             note the failure, move on
#         log one line: UTC time, feed, outcome, version
#     sleep 10 minutes

