"""Build rodalies_puntualitat_2026-10.csv (instructor tool, students do not need it).

Inputs (public, CC BY 4.0):
  * Trenes a tiempo monthly CSV  https://trenes.h1756.es/datos/puntualidad-2026-10.csv
    (origin: Renfe Operadora, data.renfe.com; derived: Trenes a tiempo)
  * Renfe Cercanias GTFS         https://ssl.renfe.com/ftransit/Fichero_CER_FOMENTO/fomento_transit.zip

The punctuality CSV has no line column, so the line of each train number is taken from
the GTFS: route ids starting with "51" are the Rodalies de Barcelona nucleus and
trip block_id = service id (5 chars) + train number (5 digits).

Usage: python build_rodalies_data.py puntualidad-2026-10.csv gtfs_folder out.csv
"""
import sys
import pandas as pd

punct, gtfs, out = sys.argv[1:4]
strip = lambda d: d.apply(lambda s: s.str.strip() if s.dtype == object else s)
routes = strip(pd.read_csv(f"{gtfs}/routes.txt", dtype=str, skipinitialspace=True))
trips = strip(pd.read_csv(f"{gtfs}/trips.txt", dtype=str))
trips = trips.merge(routes[["route_id", "route_short_name"]], on="route_id")
trips["nucleus"] = trips.route_id.str[:2]
trips["train_number"] = trips.block_id.str[5:]

# keep only train numbers that exist in the Barcelona nucleus and in no other nucleus
nuclei = trips.groupby("train_number").nucleus.agg(lambda s: set(s))
bcn = nuclei[nuclei.map(lambda s: s == {"51"})].index
lines = (trips[trips.train_number.isin(bcn)]
         .groupby("train_number").route_short_name.agg(lambda s: "|".join(sorted(set(s)))))

df = pd.read_csv(punct, dtype={"train_number": str})
df = df[df.feed == "cer"]
df = df[df.train_number.isin(lines.index)].copy()
df.insert(2, "line", df.train_number.map(lines))
df = df.drop(columns="feed").sort_values(["day", "train_number"])
df.to_csv(out, index=False)
print(len(df), "rows,", df.day.nunique(), "days,", df.line.nunique(), "line labels")
