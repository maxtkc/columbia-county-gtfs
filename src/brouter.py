#!/usr/bin/env python3
"""
BRouter URL utilities for Columbia County GTFS

This module provides functions for working with BRouter URLs for route planning
and visualization, including extracting coordinates and comparing stop locations.
"""

from urllib.parse import urlparse, parse_qs
from geopy.distance import geodesic


def extract_nogos_from_brouter_url(url):
    """
    Extract nogos parameter from BRouter URL.
    
    Args:
        url: BRouter URL containing nogos parameter
        
    Returns:
        List of (longitude, latitude, radius) tuples, or empty list if parsing fails
    """
    try:
        # Parse the URL into components
        parsed = urlparse(url)
        
        # Handle fragment-based URLs (BRouter uses hash fragments)
        if parsed.fragment:
            # Extract query parameters from the fragment
            fragment_parts = parsed.fragment.split('&')
            query_params = {}
            for part in fragment_parts:
                if '=' in part:
                    key, value = part.split('=', 1)
                    query_params[key] = value
            
            nogos_value = query_params.get('nogos')
        else:
            # Handle query-based URLs
            query_params = parse_qs(parsed.query)
            nogos_list = query_params.get('nogos', [])
            nogos_value = nogos_list[0] if nogos_list else None
        
        if not nogos_value:
            return []
        
        # Parse nogos triplets
        nogo_triplets = nogos_value.split(';')
        nogos = []
        
        for triplet in nogo_triplets:
            if triplet.count(',') == 2:
                try:
                    lon_str, lat_str, radius_str = triplet.split(',')
                    lon = float(lon_str)
                    lat = float(lat_str)
                    radius = int(float(radius_str))
                    nogos.append((lon, lat, radius))
                except ValueError:
                    # Skip invalid nogos triplets
                    continue
        
        return nogos
        
    except Exception:
        # Return empty list if any parsing fails
        return []


def extract_coords_from_brouter_url(url):
    """
    Extract coordinates from BRouter URL using proper URL parsing.
    
    Args:
        url: BRouter URL containing lonlats parameter
        
    Returns:
        List of (longitude, latitude) tuples, or empty list if parsing fails
    """
    try:
        # Parse the URL into components
        parsed = urlparse(url)
        
        # Handle fragment-based URLs (BRouter uses hash fragments)
        if parsed.fragment:
            # Extract query parameters from the fragment
            fragment_parts = parsed.fragment.split('&')
            query_params = {}
            for part in fragment_parts:
                if '=' in part:
                    key, value = part.split('=', 1)
                    query_params[key] = value
            
            lonlats_value = query_params.get('lonlats')
        else:
            # Handle query-based URLs
            query_params = parse_qs(parsed.query)
            lonlats_list = query_params.get('lonlats', [])
            lonlats_value = lonlats_list[0] if lonlats_list else None
        
        if not lonlats_value:
            return []
        
        # Parse coordinate pairs
        coord_pairs = lonlats_value.split(';')
        coords = []
        
        for pair in coord_pairs:
            if ',' in pair:
                try:
                    lon_str, lat_str = pair.split(',', 1)
                    lon = float(lon_str)
                    lat = float(lat_str)
                    coords.append((lon, lat))
                except ValueError:
                    # Skip invalid coordinate pairs
                    continue
        
        return coords
        
    except Exception:
        # Return empty list if any parsing fails
        return []


def generate_brouter_urls(trips, stops, nogos=None):
    """
    Generate BRouter URLs for route planning and visualization.
    
    Args:
        trips: List of trip dictionaries with stop_times
        stops: List of stop dictionaries with coordinates
        nogos: Dict mapping shape_id to list of (lon, lat, radius) tuples for no-go areas
        
    Returns:
        Generator yielding (shape_id/trip_id, url) tuples
    """
    # Create lookup dictionary mapping stop IDs to coordinates
    stop_lookup = {s["stop_id"]: (s["stop_lon"], s["stop_lat"]) for s in stops}

    # BRouter web interface URL components
    base = "https://brouter.de/brouter-web/#map=11/42.4655/-73.6002/standard&lonlats="
    suffix = "&profile=car-fast"

    # Track seen URLs to avoid duplicates for trips with same shape
    seen = set()

    # Process each trip to generate route URLs
    for trip in trips:
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
        
        # Add nogos parameter if specified for this shape_id
        shape_id = trip.get("shape_id")
        nogos_param = ""
        if nogos and shape_id and shape_id in nogos:
            nogos_list = []
            for lon, lat, radius in nogos[shape_id]:
                nogos_list.append(f"{lon},{lat},{radius}")
            if nogos_list:
                nogos_param = f"&nogos={';'.join(nogos_list)}"
        
        url = f"{base}{lonlats}{suffix}{nogos_param}"

        # Use shape_id and URL as key to avoid duplicate URLs for same route shape
        key = (trip.get("shape_id"), url)
        if key in seen:
            continue
        seen.add(key)

        # Output the route identifier and corresponding BRouter URL
        yield (trip.get('shape_id') or trip['trip_id'], url)


def update_stop_positions_from_url(brouter_url, trip_id, trips, stops_csv_path, nogos_csv_path=None, nogos=None):
    """
    Update stop positions in stops.csv from a modified BRouter URL.
    Also extracts nogos from the URL and saves them to nogos.csv if path provided.
    
    Args:
        brouter_url: Modified BRouter URL with new coordinates
        trip_id: ID of the trip to compare against
        trips: List of trip dictionaries
        stops_csv_path: Path to stops.csv file
        nogos_csv_path: Path to nogos.csv file (optional)
        nogos: Dict mapping shape_id to list of (lon, lat, radius) tuples for no-go areas
        
    Returns:
        Dict with update results or error information
    """
    import pandas as pd
    from geopy.distance import geodesic
    from urllib.parse import urlparse
    
    # Validate URL format
    try:
        parsed = urlparse(brouter_url)
        if not parsed.scheme or not parsed.netloc:
            return {"error": "Invalid URL format - missing scheme or domain"}
        if 'brouter' not in parsed.netloc.lower():
            return {"error": "URL does not appear to be a BRouter URL"}
    except Exception as e:
        return {"error": f"URL validation failed: {e}"}
    
    # Extract coordinates from URL
    new_coords = extract_coords_from_brouter_url(brouter_url)
    if not new_coords:
        return {"error": "Could not extract coordinates from BRouter URL - check that the URL contains a 'lonlats' parameter"}
    
    # Find the trip
    trip = next((t for t in trips if t['trip_id'] == trip_id), None)
    if not trip:
        available_trips = [t['trip_id'] for t in trips]
        return {"error": f"Trip '{trip_id}' not found. Available trips: {', '.join(available_trips)}"}
    
    # Load stops.csv
    try:
        df = pd.read_csv(stops_csv_path)
    except FileNotFoundError:
        return {"error": f"stops.csv file not found at path: {stops_csv_path}"}
    except Exception as e:
        return {"error": f"Could not read stops.csv: {e}"}
    
    # Validate required columns exist
    required_columns = ['stop_id', 'stop_lat', 'stop_lon', 'stop_name']
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        return {"error": f"stops.csv missing required columns: {', '.join(missing_columns)}"}
    
    # Get original stop sequence
    sorted_stop_times = sorted(trip["stop_times"], key=lambda x: x[0])
    
    # Validate lengths match
    if len(new_coords) != len(sorted_stop_times):
        return {
            "error": "Coordinate count mismatch",
            "url_coords": len(new_coords),
            "trip_stops": len(sorted_stop_times)
        }
    
    # Compare and update coordinates
    updates = []
    total_moved = 0
    total_distance = 0.0
    
    for i, (new_lon, new_lat) in enumerate(new_coords):
        stop_id = sorted_stop_times[i][1]
        
        # Find stop in CSV
        stop_row = df[df['stop_id'] == stop_id]
        if stop_row.empty:
            updates.append({
                "stop_id": stop_id,
                "error": "Stop not found in stops.csv"
            })
            continue
        
        stop_name = stop_row.iloc[0]['stop_name']
        old_lon = stop_row.iloc[0]['stop_lon']
        old_lat = stop_row.iloc[0]['stop_lat']
        
        # Calculate distance
        old_pos = (old_lat, old_lon)
        new_pos = (new_lat, new_lon)
        distance_m = geodesic(old_pos, new_pos).meters
        
        moved = distance_m > 1.0  # Only count moves > 1 meter
        if moved:
            total_moved += 1
            total_distance += distance_m
            
            # Update the DataFrame
            df.loc[df['stop_id'] == stop_id, 'stop_lat'] = new_lat
            df.loc[df['stop_id'] == stop_id, 'stop_lon'] = new_lon
        
        updates.append({
            "stop_id": stop_id,
            "stop_name": stop_name,
            "old_coords": (old_lon, old_lat),
            "new_coords": (new_lon, new_lat),
            "distance_m": distance_m,
            "moved": moved
        })
    
    # Save updated CSV
    try:
        df.to_csv(stops_csv_path, index=False)
    except Exception as e:
        return {"error": f"Could not save stops.csv: {e}"}
    
    # Extract and save nogos if nogos_csv_path provided
    nogos_info = {}
    if nogos_csv_path:
        nogos_from_url = extract_nogos_from_brouter_url(brouter_url)
        if nogos_from_url and trip.get("shape_id"):
            shape_id = trip["shape_id"]
            
            # Create nogos.csv if it doesn't exist
            if not nogos_csv_path.exists():
                nogos_df = pd.DataFrame(columns=['shape_id', 'stop_lat', 'stop_lon', 'radius'])
                nogos_df.to_csv(nogos_csv_path, index=False)
                nogos_info["nogos_csv_created"] = True
            
            try:
                # Load existing nogos
                nogos_df = pd.read_csv(nogos_csv_path)
                
                # Remove existing nogos for this shape_id
                nogos_df = nogos_df[nogos_df['shape_id'] != shape_id]
                
                # Add new nogos
                new_nogos = []
                for lon, lat, radius in nogos_from_url:
                    new_nogos.append({
                        'shape_id': shape_id,
                        'stop_lat': lat,
                        'stop_lon': lon,
                        'radius': radius
                    })
                
                if new_nogos:
                    new_nogos_df = pd.DataFrame(new_nogos)
                    nogos_df = pd.concat([nogos_df, new_nogos_df], ignore_index=True)
                    nogos_df.to_csv(nogos_csv_path, index=False)
                    
                    nogos_info.update({
                        "nogos_updated": True,
                        "nogos_count": len(new_nogos),
                        "shape_id": shape_id,
                        "nogos": nogos_from_url
                    })
                
            except Exception as e:
                nogos_info["nogos_error"] = f"Could not update nogos.csv: {e}"
    
    return {
        "trip_id": trip_id,
        "total_stops": len(updates),
        "stops_moved": total_moved,
        "total_distance_m": total_distance,
        "avg_distance_m": total_distance / total_moved if total_moved > 0 else 0,
        "updates": updates,
        "csv_updated": True,
        "nogos_info": nogos_info
    }


