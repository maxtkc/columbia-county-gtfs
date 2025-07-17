#!/usr/bin/env python3

import argparse
import os
import shutil
import tempfile
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


def generate_brouter_urls():
    stop_lookup = {s["stop_id"]: (s["stop_lon"], s["stop_lat"]) for s in STOPS}

    base = "https://brouter.de/brouter-web/#map=11/42.4655/-73.6002/standard&lonlats="
    suffix = "&profile=car-fast"

    seen = set()

    for trip in TRIPS:
        stop_times = trip["stop_times"]
        if not stop_times:
            continue

        # Sort stop_times by time
        sorted_stop_times = sorted(stop_times, key=lambda x: x[0])

        coords = []
        for time_str, stop_id in sorted_stop_times:
            if stop_id in stop_lookup:
                coords.append(stop_lookup[stop_id])
            else:
                print(f"⚠️ Unknown stop_id: {stop_id}")

        if not coords:
            continue

        lonlats = ";".join(f"{lon},{lat}" for lon, lat in coords)
        url = f"{base}{lonlats}{suffix}"

        key = (trip.get("shape_id"), url)
        if key in seen:
            continue
        seen.add(key)

        print(f"{trip.get('shape_id') or trip['trip_id']}: {url}")


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
                        "arrival_time": f"{stop[0]}:00",
                        "departure_time": f"{stop[2] if len(stop) == 3 else stop[0]}:00",
                        "stop_id": stop[1],
                        "stop_sequence": i,
                    }
                    for i, stop in enumerate(trip["stop_times"])
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
        return (
            existing_id
            if pd.notna(existing_id) and existing_id.strip()
            else f"STOP-{uuid.uuid4()}"
        )

    df["stop_id"] = df["stop_id"].apply(make_id)

    # Output Python code
    print("STOPS = [")
    for _, row in df.iterrows():
        print("    {")
        print(f'        "stop_id": "{row["stop_id"]}",')
        print(f'        "stop_name": "{row["name"]}",')
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
    parser.add_argument(
        "--generate-stops",
        action="store_true",
        help="Generate stops Python code and update stops.csv",
    )
    parser.add_argument(
        "--gen-brouter-urls",
        action="store_true",
        help="Generate BRouter URLs for trips",
    )
    args = parser.parse_args()

    if args.gen_gtfs:
        generate_gtfs()
    elif args.generate_stops:
        generate_stops()
    elif args.gen_brouter_urls:
        generate_brouter_urls()
    else:
        parser.print_help()
