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
from src.brouter import generate_brouter_urls, update_stop_positions_from_url

# Script directory and output paths
script_dir = os.path.dirname(os.path.realpath(__file__))
feed_path = Path(script_dir) / "columbia_county_gtfs"


def load_nogos_from_csv():
    """
    Load nogos from nogos.csv and convert to dictionary format expected by brouter functions.
    
    Returns:
        Dict mapping shape_id to list of (lon, lat, radius) tuples
    """
    nogos_csv_path = Path(script_dir) / "nogos.csv"
    
    # Return empty dict if file doesn't exist or is empty
    if not nogos_csv_path.exists():
        return {}
    
    try:
        df = pd.read_csv(nogos_csv_path)
        
        # Return empty dict if CSV is empty or missing required columns
        if df.empty or not all(col in df.columns for col in ['shape_id', 'stop_lat', 'stop_lon', 'radius']):
            return {}
        
        nogos_dict = {}
        for _, row in df.iterrows():
            shape_id = row["shape_id"]
            if shape_id not in nogos_dict:
                nogos_dict[shape_id] = []
            nogos_dict[shape_id].append((row["stop_lon"], row["stop_lat"], int(row["radius"])))
        
        return nogos_dict
        
    except Exception as e:
        print(f"⚠️ Warning: Could not load nogos.csv: {e}")
        return {}


def load_guides_from_csv():
    """
    Load guide points from guides.csv.
    
    Returns:
        Dict mapping shape_id to list of (lon, lat, position) tuples, where position
        is the index in the stop sequence where the guide point should be inserted
    """
    guides_csv_path = Path(script_dir) / "guides.csv"
    
    # Return empty dict if file doesn't exist or is empty
    if not guides_csv_path.exists():
        return {}
    
    try:
        df = pd.read_csv(guides_csv_path)
        
        # Return empty dict if CSV is empty or missing required columns
        if df.empty or not all(col in df.columns for col in ['shape_id', 'stop_lat', 'stop_lon', 'position']):
            return {}
        
        guides_dict = {}
        for _, row in df.iterrows():
            shape_id = row["shape_id"]
            if shape_id not in guides_dict:
                guides_dict[shape_id] = []
            # Include order if available, otherwise default to 0
            order = int(row["order"]) if "order" in row and pd.notna(row["order"]) else 0
            guides_dict[shape_id].append((row["stop_lon"], row["stop_lat"], int(row["position"]), order))
        
        # Sort guides by order to ensure they're processed in waypoint sequence
        for shape_id in guides_dict:
            guides_dict[shape_id].sort(key=lambda x: x[3])  # Sort by order (4th element)
        
        return guides_dict
        
    except Exception as e:
        print(f"⚠️ Warning: Could not load guides.csv: {e}")
        return {}


def load_straights_from_csv(straights_csv_path=None):
    """
    Load straight line segment indices from straights.csv file.
    
    Returns:
        Dict mapping shape_id to list of integers (waypoint indices)
    """
    if straights_csv_path is None:
        straights_csv_path = Path(script_dir) / "straights.csv"
    
    if not straights_csv_path.exists():
        return {}
    
    try:
        df = pd.read_csv(straights_csv_path)
        straights_dict = {}
        
        for _, row in df.iterrows():
            shape_id = row['shape_id']
            indices_str = row['indices']
            
            # Parse comma-separated indices
            indices = []
            for index_str in indices_str.split(','):
                try:
                    indices.append(int(index_str.strip()))
                except ValueError:
                    continue
            
            straights_dict[shape_id] = indices
        
        return straights_dict
        
    except Exception as e:
        print(f"Warning: Could not load straights from {straights_csv_path}: {e}")
        return {}


def generate_brouter_urls_cli():
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
    nogos_dict = load_nogos_from_csv()
    guides_dict = load_guides_from_csv()
    straights_dict = load_straights_from_csv()
    for route_id, url in generate_brouter_urls(TRIPS, STOPS, nogos_dict, guides_dict, straights_dict):
        print(f"{route_id}: {url}")


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

    # Save updated CSV with generated stop_ids
    df.to_csv(stops_csv, index=False)
    print(f"✅ Updated {stops_csv} with stop_ids")


def update_stop_positions(brouter_url, trip_id):
    """
    Update stop positions from a modified BRouter URL.
    
    Args:
        brouter_url: Modified BRouter URL with new coordinates
        trip_id: ID of the trip to compare against
    """
    stops_csv_path = Path(script_dir) / "stops.csv"
    nogos_csv_path = Path(script_dir) / "nogos.csv"
    guides_csv_path = Path(script_dir) / "guides.csv"
    straights_csv_path = Path(script_dir) / "straights.csv"
    nogos_dict = load_nogos_from_csv()
    guides_dict = load_guides_from_csv()
    result = update_stop_positions_from_url(brouter_url, trip_id, TRIPS, stops_csv_path, nogos_csv_path, guides_csv_path, straights_csv_path, nogos_dict, guides_dict)
    
    if "error" in result:
        print(f"❌ Error: {result['error']}")
        if "url_coords" in result and "trip_stops" in result:
            print(f"   BRouter URL has {result['url_coords']} coordinates")
            print(f"   Trip '{trip_id}' has {result['trip_stops']} stops")
        return
    
    print(f"📍 Updating stop positions for trip '{result['trip_id']}':")
    print(f"   Found {result['total_stops']} coordinates in BRouter URL")
    print()
    
    for update in result['updates']:
        if "error" in update:
            print(f"⚠️  {update['stop_id']}: {update['error']}")
            continue
        
        stop_id = update['stop_id']
        stop_name = update['stop_name']
        distance_m = update['distance_m']
        old_lon, old_lat = update['old_coords']
        new_lon, new_lat = update['new_coords']
        
        if update['moved']:
            print(f"📌 {stop_name} ({stop_id}): Updated position (moved {distance_m:.1f}m)")
            print(f"   Old: ({old_lon:.6f}, {old_lat:.6f})")
            print(f"   New: ({new_lon:.6f}, {new_lat:.6f})")
        else:
            print(f"✅ {stop_name} ({stop_id}): No significant change ({distance_m:.1f}m)")
    
    print()
    if result['stops_moved'] > 0:
        print(f"📊 Summary: {result['stops_moved']}/{result['total_stops']} stops updated")
        print(f"   Average distance: {result['avg_distance_m']:.1f}m")
        print(f"   Total distance: {result['total_distance_m']:.1f}m")
        print(f"✅ Updated {stops_csv_path}")
    else:
        print("✅ No stops were significantly moved")
    
    # Handle nogos information
    nogos_info = result.get('nogos_info', {})
    if nogos_info.get('nogos_csv_created'):
        print(f"📄 Created {nogos_csv_path}")
    
    if nogos_info.get('nogos_updated'):
        shape_id = nogos_info['shape_id']
        nogos_count = nogos_info['nogos_count']
        print(f"🚫 Updated {nogos_count} nogos for shape '{shape_id}':")
        for i, (lon, lat, radius) in enumerate(nogos_info['nogos'], 1):
            print(f"   {i}. {lat:.6f}, {lon:.6f} (radius: {radius}m)")
        print(f"✅ Updated {nogos_csv_path}")
    elif nogos_info.get('nogos_error'):
        print(f"⚠️  Nogos warning: {nogos_info['nogos_error']}")
    elif 'nogos_info' in result:
        print("ℹ️  No nogos found in BRouter URL")
    
    # Handle guide points information
    guides_info = result.get('guides_info', {})
    if guides_info.get('guides_csv_created'):
        print(f"📄 Created {guides_csv_path}")
    
    if guides_info.get('guides_updated'):
        shape_id = guides_info['shape_id']
        guides_count = guides_info['guides_count']
        print(f"🧭 Updated {guides_count} guide points for shape '{shape_id}':")
        for i, (lon, lat, position) in enumerate(guides_info['guides'], 1):
            print(f"   {i}. {lat:.6f}, {lon:.6f} (position: {position})")
        print(f"✅ Updated {guides_csv_path}")
    elif guides_info.get('guides_error'):
        print(f"⚠️  Guides warning: {guides_info['guides_error']}")
    elif 'guides_info' in result:
        print("ℹ️  No guide points found in BRouter URL")
    
    # Handle straight line segments information
    straights_info = result.get('straights_info', {})
    if straights_info.get('straights_csv_created'):
        print(f"📄 Created {straights_csv_path}")
    
    if straights_info.get('straights_updated'):
        shape_id = straights_info['shape_id']
        indices = straights_info['indices']
        indices_str = ','.join(map(str, indices))
        print(f"📏 Updated straight line segments for shape '{shape_id}': [{indices_str}]")
        print(f"✅ Updated {straights_csv_path}")
    elif straights_info.get('straights_error'):
        print(f"⚠️  Straights warning: {straights_info['straights_error']}")
    elif 'straights_info' in result:
        print("ℹ️  No straight line segments found in BRouter URL")



if __name__ == "__main__":
    # Set up command-line argument parser with subcommands
    parser = argparse.ArgumentParser(
        description="Columbia County GTFS Feed Generator - Generate transit data feeds and route planning tools"
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Generate GTFS zip file
    gtfs_parser = subparsers.add_parser("gen-gtfs", help="Generate GTFS zip")

    # Generate stops Python code and update stops.csv
    stops_parser = subparsers.add_parser("gen-stops", help="Generate stops Python code and update stops.csv")

    # Generate BRouter URLs for trips
    brouter_parser = subparsers.add_parser("gen-brouter-urls", help="Generate BRouter URLs for trips")

    # Update stop positions from modified BRouter URL
    update_parser = subparsers.add_parser("update-stop-positions", help="Update stop positions from modified BRouter URL")
    update_parser.add_argument(
        "--brouter-url",
        type=str,
        required=True,
        help="Modified BRouter URL with new coordinates",
    )
    update_parser.add_argument(
        "--trip-id",
        type=str,
        required=True,
        help="Trip ID to compare against",
    )

    args = parser.parse_args()

    # Execute the requested command
    if args.command == "gen-gtfs":
        generate_gtfs()
    elif args.command == "gen-stops":
        generate_stops()
    elif args.command == "gen-brouter-urls":
        generate_brouter_urls_cli()
    elif args.command == "update-stop-positions":
        update_stop_positions(args.brouter_url, args.trip_id)
    else:
        # No command specified, show help
        parser.print_help()
