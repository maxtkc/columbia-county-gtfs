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


def extract_pois_from_brouter_url(url):
    """
    Extract POIs (points of interest) from BRouter URL.
    
    Args:
        url: BRouter URL containing pois parameter
        
    Returns:
        List of (longitude, latitude, label) tuples, or empty list if parsing fails
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
            
            pois_value = query_params.get('pois')
        else:
            # Handle query-based URLs
            query_params = parse_qs(parsed.query)
            pois_list = query_params.get('pois', [])
            pois_value = pois_list[0] if pois_list else None
        
        if not pois_value:
            return []
        
        # Parse POI triplets
        poi_triplets = pois_value.split(';')
        pois = []
        
        for triplet in poi_triplets:
            if triplet.count(',') >= 2:
                try:
                    parts = triplet.split(',')
                    lon = float(parts[0])
                    lat = float(parts[1])
                    # Label is everything after the second comma
                    label = ','.join(parts[2:]) if len(parts) > 2 else ""
                    pois.append((lon, lat, label))
                except ValueError:
                    # Skip invalid POI triplets
                    continue
        
        return pois
        
    except Exception:
        # Return empty list if any parsing fails
        return []


def extract_straight_from_brouter_url(url):
    """
    Extract straight line segment indices from BRouter URL.
    
    Args:
        url: BRouter URL containing straight parameter
        
    Returns:
        List of integers representing waypoint indices that should be straight lines, or empty list if parsing fails
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
            
            straight_value = query_params.get('straight')
        else:
            # Handle query-based URLs
            query_params = parse_qs(parsed.query)
            straight_list = query_params.get('straight', [])
            straight_value = straight_list[0] if straight_list else None
        
        if not straight_value:
            return []
        
        # Parse comma-separated indices
        indices = []
        for index_str in straight_value.split(','):
            try:
                index = int(index_str.strip())
                indices.append(index)
            except ValueError:
                # Skip invalid indices
                continue
        
        return indices
        
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


def generate_brouter_urls(trips, stops, nogos=None, guides=None, straights=None):
    """
    Generate BRouter URLs for route planning and visualization.
    
    Args:
        trips: List of trip dictionaries with stop_times
        stops: List of stop dictionaries with coordinates
        nogos: Dict mapping shape_id to list of (lon, lat, radius) tuples for no-go areas
        guides: Dict mapping shape_id to list of (lon, lat, position) tuples for guide points
        straights: Dict mapping shape_id to list of waypoint indices for straight line segments
        
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

        # Insert guide points at specified positions
        shape_id = trip.get("shape_id")
        guide_pois = []
        if guides and shape_id and shape_id in guides:
            # Sort guides by position to insert them in correct order
            sorted_guides = sorted(guides[shape_id], key=lambda x: x[2])
            
            # Insert guides from end to beginning to maintain correct indices
            for lon, lat, position in reversed(sorted_guides):
                if 0 <= position <= len(coords):
                    coords.insert(position, (lon, lat))
                    guide_pois.append((lon, lat, "GUIDE"))

        # Format coordinates for BRouter URL (longitude,latitude pairs separated by semicolons)
        lonlats = ";".join(f"{lon},{lat}" for lon, lat in coords)
        
        # Add nogos parameter if specified for this shape_id
        nogos_param = ""
        if nogos and shape_id and shape_id in nogos:
            nogos_list = []
            for lon, lat, radius in nogos[shape_id]:
                nogos_list.append(f"{lon},{lat},{radius}")
            if nogos_list:
                nogos_param = f"&nogos={';'.join(nogos_list)}"
        
        # Add POIs parameter for guide points
        pois_param = ""
        if guide_pois:
            poi_list = []
            for lon, lat, label in guide_pois:
                poi_list.append(f"{lon},{lat},{label}")
            if poi_list:
                pois_param = f"&pois={';'.join(poi_list)}"
        
        # Add straight parameter if specified for this shape_id
        straight_param = ""
        if straights and shape_id and shape_id in straights:
            straight_indices = straights[shape_id]
            if straight_indices:
                straight_param = f"&straight={','.join(map(str, straight_indices))}"
        
        url = f"{base}{lonlats}{suffix}{nogos_param}{pois_param}{straight_param}"

        # Use shape_id and URL as key to avoid duplicate URLs for same route shape
        key = (trip.get("shape_id"), url)
        if key in seen:
            continue
        seen.add(key)

        # Output the route identifier and corresponding BRouter URL
        yield (trip.get('shape_id') or trip['trip_id'], url)


def update_stop_positions_from_url(brouter_url, trip_id, trips, stops_csv_path, nogos_csv_path=None, guides_csv_path=None, nogos=None, guides=None):
    """
    Update stop positions in stops.csv from a modified BRouter URL.
    Also extracts nogos and guide points from the URL and saves them to respective CSV files if paths provided.
    
    Args:
        brouter_url: Modified BRouter URL with new coordinates
        trip_id: ID of the trip to compare against
        trips: List of trip dictionaries
        stops_csv_path: Path to stops.csv file
        nogos_csv_path: Path to nogos.csv file (optional)
        guides_csv_path: Path to guides.csv file (optional)
        nogos: Dict mapping shape_id to list of (lon, lat, radius) tuples for no-go areas
        guides: Dict mapping shape_id to list of (lon, lat, position) tuples for guide points
        
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
    
    # Extract straight line indices from URL
    straight_indices = extract_straight_from_brouter_url(brouter_url)
    
    # Extract POIs from URL to identify guide points
    pois = extract_pois_from_brouter_url(brouter_url)
    guide_pois = [(lon, lat) for lon, lat, label in pois if label == "GUIDE"]
    
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
    
    # Filter out guide points from coordinates by finding closest matches to GUIDE POIs
    stop_coords = []
    detected_guides = []
    guide_indices = set()
    
    # For each GUIDE POI, find the closest route coordinate
    for guide_lon, guide_lat in guide_pois:
        closest_distance = float('inf')
        closest_index = -1
        
        for i, (lon, lat) in enumerate(new_coords):
            if i in guide_indices:  # Skip already assigned guides
                continue
                
            distance_m = geodesic((lat, lon), (guide_lat, guide_lon)).meters
            if distance_m < closest_distance and distance_m <= 100:  # 100m max threshold
                closest_distance = distance_m
                closest_index = i
        
        if closest_index >= 0:
            guide_indices.add(closest_index)
            lon, lat = new_coords[closest_index]
            detected_guides.append((lon, lat, closest_index))
    
    # Build stop_coords excluding guide indices
    for i, (lon, lat) in enumerate(new_coords):
        if i not in guide_indices:
            stop_coords.append((lon, lat))
    
    # Validate lengths match after removing guides
    if len(stop_coords) != len(sorted_stop_times):
        return {
            "error": "Coordinate count mismatch after removing guide points",
            "url_coords": len(new_coords),
            "stop_coords": len(stop_coords),
            "trip_stops": len(sorted_stop_times),
            "detected_guides": len(detected_guides)
        }
    
    # Compare and update coordinates
    updates = []
    total_moved = 0
    total_distance = 0.0
    
    for i, (new_lon, new_lat) in enumerate(stop_coords):
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
    
    # Extract and save guide points if guides_csv_path provided
    guides_info = {}
    if guides_csv_path and detected_guides and trip.get("shape_id"):
        shape_id = trip["shape_id"]
        
        # Create guides.csv if it doesn't exist
        if not guides_csv_path.exists():
            guides_df = pd.DataFrame(columns=['shape_id', 'stop_lat', 'stop_lon', 'position'])
            guides_df.to_csv(guides_csv_path, index=False)
            guides_info["guides_csv_created"] = True
        
        try:
            # Load existing guides
            guides_df = pd.read_csv(guides_csv_path)
            
            # Remove existing guides for this shape_id
            guides_df = guides_df[guides_df['shape_id'] != shape_id]
            
            # Add new guides with their positions in the coordinate sequence
            new_guides = []
            for lon, lat, original_position in detected_guides:
                # Calculate position relative to stops (before guides were inserted)
                position_in_stops = sum(1 for _, _, pos in detected_guides if pos < original_position)
                position = original_position - position_in_stops
                
                new_guides.append({
                    'shape_id': shape_id,
                    'stop_lat': lat,
                    'stop_lon': lon,
                    'position': position
                })
            
            if new_guides:
                new_guides_df = pd.DataFrame(new_guides)
                guides_df = pd.concat([guides_df, new_guides_df], ignore_index=True)
                guides_df.to_csv(guides_csv_path, index=False)
                
                guides_info.update({
                    "guides_updated": True,
                    "guides_count": len(new_guides),
                    "shape_id": shape_id,
                    "guides": [(g['stop_lon'], g['stop_lat'], g['position']) for g in new_guides]
                })
            
        except Exception as e:
            guides_info["guides_error"] = f"Could not update guides.csv: {e}"
    
    return {
        "trip_id": trip_id,
        "total_stops": len(updates),
        "stops_moved": total_moved,
        "total_distance_m": total_distance,
        "avg_distance_m": total_distance / total_moved if total_moved > 0 else 0,
        "updates": updates,
        "csv_updated": True,
        "straight_indices": straight_indices,
        "nogos_info": nogos_info,
        "guides_info": guides_info
    }


