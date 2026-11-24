"""Build the Rodalies punctuality file used in the probabilities lab (instructor tool,
students do not need it).

Inputs (public, CC BY 4.0):
  * Trenes a tiempo monthly CSVs  https://trenes.h1756.es/datos/puntualidad-YYYY-MM.csv
    (origin: Renfe Operadora, data.renfe.com; derived: Trenes a tiempo)
  * Renfe Cercanias GTFS          https://ssl.renfe.com/ftransit/Fichero_CER_FOMENTO/fomento_transit.zip

The punctuality CSVs have no line column, so the line of each train number is taken from
the GTFS: route ids starting with "51" are the Rodalies de Barcelona nucleus and
trip block_id = service id (5 chars) + train number (5 digits).

Usage: python build_rodalies_data.py gtfs_folder out.csv last_day puntualidad-2026-10.csv puntualidad-2026-11.csv ...
(last_day, YYYY-MM-DD, drops later days: the most recent day of a monthly file is incomplete)
"""
import sys
import pandas as pd

gtfs, out, last_day, *punct = sys.argv[1:]
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

df = pd.concat([pd.read_csv(f, dtype={"train_number": str}) for f in punct])
df = df[(df.feed == "cer") & (df.day <= last_day)]
df = df[df.train_number.isin(lines.index)].copy()
df.insert(2, "line", df.train_number.map(lines))
df = df.drop(columns="feed").sort_values(["day", "train_number"])
df.to_csv(out, index=False)
print(len(df), "rows,", df.day.nunique(), "days,", df.day.min(), "to", df.day.max(), "|", df.line.nunique(), "line labels")
