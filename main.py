#!/usr/bin/env python3

import os
import shutil
import tempfile
import argparse
import uuid
from pathlib import Path

import pandas as pd

from src.gen_gtfs import (
    AGENCY,
    CALENDAR,
    CALENDAR_DATES,
    FEED_INFO,
    ROUTES,
    STOPS,
    TRIPS,
)
from src.gtfs_lib import linestring_from_geojson

script_dir = os.path.dirname(os.path.realpath(__file__))
feed_path = Path(script_dir) / "columbia_county_gtfs"


def generate_gtfs():
    FILES = {
        "agency.txt": [AGENCY],
        "stops.txt": STOPS,
        "routes.txt": ROUTES,
        "trips.txt": [
            {k: v for k, v in trip.items() if k != "stop_times"} for trip in TRIPS
        ],
        "stop_times.txt": [
            item
            for sublist in [
                [
                    {
                        "trip_id": trip["trip_id"],
                        "arrival_time": f"{time}:00",
                        "departure_time": f"{time}:00",
                        "stop_id": stop_id,
                        "stop_sequence": i,
                    }
                    for i, (time, stop_id) in enumerate(trip["stop_times"])
                ]
                for trip in TRIPS
            ]
            for item in sublist
        ],
        "calendar.txt": CALENDAR,
        "calendar_dates.txt": CALENDAR_DATES,
        "feed_info.txt": [FEED_INFO],
        "shapes.txt": [
            {
                "shape_id": shape_id,
                "shape_pt_lat": lat,
                "shape_pt_lon": lon,
                "shape_pt_sequence": seq,
            }
            for shape_id in sorted({t["shape_id"] for t in TRIPS if "shape_id" in t})
            for seq, (lon, lat, *_) in enumerate(
                linestring_from_geojson(f"{script_dir}/shapes/{shape_id}.geojson"),
                start=1,
            )
        ],
    }

    with tempfile.TemporaryDirectory() as tmpdirname:
        for filename, data in FILES.items():
            pd.DataFrame(data).to_csv(Path(tmpdirname) / filename, index=False)
        shutil.make_archive(str(feed_path), "zip", tmpdirname)
        print(f"✅ GTFS archive created at: {feed_path}.zip")


def generate_stops():
    stops_csv = Path(script_dir) / "stops.csv"
    df = pd.read_csv(stops_csv)

    if "stop_id" not in df.columns:
        df["stop_id"] = ""

    def make_id(existing_id):
        return existing_id if pd.notna(existing_id) and existing_id.strip() else f"STOP-{uuid.uuid4()}"

    df["stop_id"] = df["stop_id"].apply(make_id)

    # Output Python code
    print("STOPS = [")
    for _, row in df.iterrows():
        print("    {")
        print(f'        "stop_id": "{row["stop_id"]}",')
        print(f'        "stop_name": "{row["name"]}",')
        print(f'        "stop_desc": "{row["desc"]}",')
        print(f'        "stop_lat": {row["lat"]},')
        print(f'        "stop_lon": {row["lon"]},')
        print("    },")
    print("]")

    # Overwrite with updated stop_ids
    df.to_csv(stops_csv, index=False)
    print(f"✅ Updated {stops_csv} with stop_ids")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--gen-gtfs", action="store_true", help="Generate GTFS zip")
    parser.add_argument("--generate-stops", action="store_true", help="Generate stops Python code and update stops.csv")
    args = parser.parse_args()

    if args.gen_gtfs:
        generate_gtfs()
    elif args.generate_stops:
        generate_stops()
    else:
        parser.print_help()
