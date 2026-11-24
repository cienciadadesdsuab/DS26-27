"""Build bicing_snapshot.csv from the public Bicing GBFS feeds (instructor tool).

Source: Bicing (Barcelona) GBFS feeds, licence CC BY
  https://barcelona.publicbikesystem.net/customer/gbfs/v2/en/station_status.json
  https://barcelona.publicbikesystem.net/customer/gbfs/v2/en/station_information.json

Usage: python build_bicing_snapshot.py station_status.json station_information.json out.csv
"""
import json
import sys
from datetime import datetime, timezone

import pandas as pd

status_file, info_file, out = sys.argv[1:4]
status = json.load(open(status_file))
info = json.load(open(info_file))

st = pd.DataFrame(status["data"]["stations"])[
    ["station_id", "status", "num_bikes_available", "num_docks_available"]]
inf = pd.DataFrame(info["data"]["stations"])[
    ["station_id", "name", "lat", "lon", "capacity", "cross_street"]]
df = st.merge(inf, on="station_id")
df["district"] = df["cross_street"].str.split("/").str[0]
df = df.drop(columns="cross_street")
df["snapshot_utc"] = datetime.fromtimestamp(status["last_updated"], timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
df = df.rename(columns={"num_bikes_available": "bikes_available", "num_docks_available": "docks_available"})
df.to_csv(out, index=False)
print(len(df), "stations, snapshot", df["snapshot_utc"].iloc[0], "UTC")
