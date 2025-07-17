#!/usr/bin/env python3
"""
Columbia County GTFS Feed Generator

This script generates GTFS (General Transit Feed Specification) data for
Columbia County Public Transportation in New York. Provides CLI commands
for generating complete GTFS feeds, managing stops, and creating BRouter
URLs for route planning.
"""

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

# Script directory and output paths
script_dir = os.path.dirname(os.path.realpath(__file__))
feed_path = Path(script_dir) / "columbia_county_gtfs"


def generate_brouter_urls():
    """
    Generate BRouter URLs for route planning and visualization.
    
    Creates clickable URLs for the BRouter web interface that display
    transit routes with stop sequences. Used for creating and validating
    GeoJSON route shapes before adding them to the shapes/ directory.
    
    The generated URLs can be used to:
    - Visualize existing route patterns
    - Plan new routes interactively
    - Export route geometries as GeoJSON files
    """
    # Create lookup dictionary mapping stop IDs to (longitude, latitude) coordinates
    stop_lookup = {s["stop_id"]: (s["stop_lon"], s["stop_lat"]) for s in STOPS}

    # BRouter web interface URL components
    base = "https://brouter.de/brouter-web/#map=11/42.4655/-73.6002/standard&lonlats="
    suffix = "&profile=car-fast"

    # Track seen URLs to avoid duplicates for trips with same shape
    seen = set()

    # Process each trip to generate route URLs
    for trip in TRIPS:
        stop_times = trip["stop_times"]
        if not stop_times:
            continue

        # Sort stop_times by arrival time to ensure proper sequence
        sorted_stop_times = sorted(stop_times, key=lambda x: x[0])

        # Build coordinate list from stop sequence
        coords = []
        for time_str, stop_id in sorted_stop_times:
            if stop_id in stop_lookup:
                coords.append(stop_lookup[stop_id])
            else:
                print(f"⚠️ Unknown stop_id: {stop_id}")

        if not coords:
            continue

        # Format coordinates for BRouter URL (longitude,latitude pairs separated by semicolons)
        lonlats = ";".join(f"{lon},{lat}" for lon, lat in coords)
        url = f"{base}{lonlats}{suffix}"

        # Use shape_id and URL as key to avoid duplicate URLs for same route shape
        key = (trip.get("shape_id"), url)
        if key in seen:
            continue
        seen.add(key)

        # Output the route identifier and corresponding BRouter URL
        print(f"{trip.get('shape_id') or trip['trip_id']}: {url}")


def generate_gtfs():
    """
    Generate complete GTFS feed as a zip archive.
    
    Creates all required GTFS files from the data structures defined in
    src/gen_gtfs.py and packages them into a standard GTFS zip archive.
    The output file columbia_county_gtfs.zip can be consumed by transit
    apps and trip planning software.
    
    Generated files include:
    - agency.txt: Transit agency information
    - routes.txt: Route definitions
    - stops.txt: Stop locations and details
    - trips.txt: Trip definitions
    - stop_times.txt: Stop sequences and schedules
    - calendar.txt: Service patterns
    - calendar_dates.txt: Service exceptions
    - feed_info.txt: Feed metadata
    - shapes.txt: Route geometries from GeoJSON files
    """
    # Define GTFS file structure and data mappings
    FILES = {
        "agency.txt": [AGENCY],
        "stops.txt": STOPS,
        "routes.txt": ROUTES,
        "trips.txt": [
            # Remove stop_times from trip data (goes in separate stop_times.txt file)
            {k: v for k, v in trip.items() if k != "stop_times"} for trip in TRIPS
        ],
        "stop_times.txt": [
            # Flatten nested list comprehension to create stop_times records
            item
            for sublist in [
                [
                    {
                        "trip_id": trip["trip_id"],
                        "arrival_time": f"{stop[0]}:00",  # Format time as HH:MM:00
                        "departure_time": f"{stop[2] if len(stop) == 3 else stop[0]}:00",  # Use departure time if provided, else arrival
                        "stop_id": stop[1],
                        "stop_sequence": i,  # Sequential order of stops on trip
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
            # Generate shape points from GeoJSON files for route geometries
            {
                "shape_id": shape_id,
                "shape_pt_lat": lat,
                "shape_pt_lon": lon,
                "shape_pt_sequence": seq,  # Sequential order of points along shape
            }
            # Get unique shape_ids from trips that have shapes defined
            for shape_id in sorted({t["shape_id"] for t in TRIPS if "shape_id" in t})
            # Load coordinates from corresponding GeoJSON file and enumerate with sequence numbers
            for seq, (lon, lat, *_) in enumerate(
                linestring_from_geojson(f"{script_dir}/shapes/{shape_id}.geojson"),
                start=1,  # GTFS sequences start at 1, not 0
            )
        ],
    }

    # Create GTFS files in temporary directory, then zip them
    with tempfile.TemporaryDirectory() as tmpdirname:
        # Convert each data structure to CSV format
        for filename, data in FILES.items():
            pd.DataFrame(data).to_csv(Path(tmpdirname) / filename, index=False)
        # Create zip archive containing all GTFS files
        shutil.make_archive(str(feed_path), "zip", tmpdirname)
        print(f"✅ GTFS archive created at: {feed_path}.zip")


def generate_stops():
    """
    Generate stop definitions from CSV file and create Python code output.
    
    Reads stops.csv containing stop names and coordinates, generates unique
    UUIDs for stops that don't have IDs, and outputs Python code for the
    STOPS data structure. Also updates the CSV file with generated stop_ids.
    
    The CSV file should contain columns: name, lat, lon, stop_id (optional)
    Missing stop_ids are automatically generated as "STOP-{uuid4}"
    """
    stops_csv = Path(script_dir) / "stops.csv"
    df = pd.read_csv(stops_csv)

    # Add stop_id column if it doesn't exist
    if "stop_id" not in df.columns:
        df["stop_id"] = ""

    def make_id(existing_id):
        """Generate stop ID if one doesn't exist, otherwise keep existing."""
        return (
            existing_id
            if pd.notna(existing_id) and existing_id.strip()
            else f"STOP-{uuid.uuid4()}"  # Generate unique UUID-based ID
        )

    # Apply ID generation to all stops
    df["stop_id"] = df["stop_id"].apply(make_id)

    # Output Python code for STOPS data structure
    print("STOPS = [")
    for _, row in df.iterrows():
        print("    {")
        print(f'        "stop_id": "{row["stop_id"]}",')
        print(f'        "stop_name": "{row["name"]}",')
        print(f'        "stop_lat": {row["lat"]},')
        print(f'        "stop_lon": {row["lon"]},')
        print("    },")
    print("]")

    # Save updated CSV with generated stop_ids
    df.to_csv(stops_csv, index=False)
    print(f"✅ Updated {stops_csv} with stop_ids")


if __name__ == "__main__":
    # Set up command-line argument parser
    parser = argparse.ArgumentParser(
        description="Columbia County GTFS Feed Generator - Generate transit data feeds and route planning tools"
    )
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

    # Execute the requested command
    if args.gen_gtfs:
        generate_gtfs()
    elif args.generate_stops:
        generate_stops()
    elif args.gen_brouter_urls:
        generate_brouter_urls()
    else:
        # No command specified, show help
        parser.print_help()
