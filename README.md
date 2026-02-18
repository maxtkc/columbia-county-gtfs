# GTFS Feed Generator for Columbia County Transportation

This repository generates GTFS (General Transit Feed Specification) data for Columbia County Public Transportation in New York. The system creates standardized transit feed files from Python data structures defining routes, stops, schedules, and trip shapes.

## Overview

The Columbia County Public Transportation system serves various routes including:
- Shopping loop (SHOPPING)
- Hudson-Albany connections (HUD_ALB)
- Hudson-Chatham routes (HUD_CHT)
- Monday-only service routes (MOND)

For more information about the transit system, visit [CC Public
Transportation](https://publictransportation.columbiacountyny.com/).

## Installation

1. Clone this repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Generate GTFS Feed
Create the complete GTFS feed zip file:
```bash
python main.py gen-gtfs
```
This generates `columbia_county_gtfs.zip` containing all required GTFS files.

### Manage Stops

New stops can be added by adding them to the `stops.csv` file. Use `stops.csv` to edit stop names and locations. Leave the uuid blank and generate it with
```bash
python main.py gen-stops
```

### Generate Route Planning URLs
Create BRouter URLs for making geojson routes. To change the path of an existing route, re-create the geojson.
```bash
python main.py gen-brouter-urls
```

Make sure to name the geojson file the same as the `shape_id` and place it in
the `shapes` directory so it can be used.

### Update Stop Positions
Update stop coordinates from a modified BRouter URL:
```bash
python main.py --update-stop-positions --brouter-url "<modified_brouter_url>" --trip-id "<trip_id>"
```

This command:
- Extracts coordinates from a modified BRouter URL
- Maps them back to original stops by sequence order
- Updates the coordinates in `stops.csv`
- Reports which stops moved and by how much distance
- Validates that the number of coordinates matches the trip's stops
- Automatically extracts and saves nogos (no-go areas) to `nogos.csv`

**Note:** The `trip_id` can be any trip that has the same `shape_id` as the route you're modifying.

### Route Modification Workflow

To modify a route without adding new stops:

1. **Generate BRouter URL for the route:**
   ```bash
   python main.py gen-brouter-urls
   ```
   Copy the URL for the route you want to modify.

2. **Modify the route in BRouter:**
   - Open the URL in [BRouter web interface](https://brouter.de/brouter-web/)
   - Drag stops to adjust the route
   - Add nogos (no-go areas) using the no-go tool in BRouter to mark areas to avoid
   - Copy the modified URL from the browser

3. **Update stop positions and save nogos:**
   ```bash
   python main.py --update-stop-positions --brouter-url "<modified_url>" --trip-id "<trip_id>"
   ```
   This will:
   - Update stop coordinates based on the new route
   - Automatically save any nogos from the URL to `nogos.csv`
   - Generate future BRouter URLs with the saved nogos included

## Project Structure

```
├── main.py                 # CLI entry point
├── src/
│   ├── gen_gtfs.py        # Transit data definitions (routes, stops, trips)
│   ├── gtfs_lib.py        # Utility functions and GTFS enums
│   └── brouter.py         # BRouter URL utilities
├── shapes/                # GeoJSON files for route geometries
│   ├── HUD_ALB_NB.geojson
│   ├── HUD_ALB_SB.geojson
│   ├── SHOPPING.geojson
│   └── ...
├── stops.csv             # Stop information (name, lat, lon)
├── nogos.csv             # No-go areas for route planning (shape_id, lat, lon, radius)
└── columbia_county_gtfs.zip  # Generated GTFS feed
```

## Data Management

### Routes
Route definitions are stored in `src/gen_gtfs.py` as Python data structures. Each route includes:
- Route ID and name
- Route type (bus service)
- Agency information

### Stops
Stop information is managed through:
- `stops.csv`: Master list with coordinates and names
- `STOPS` constant in `gen_gtfs.py`: Python data structure for GTFS generation

#### Create Route Map
You can use [https://brouter.de/brouter-web/](https://brouter.de/brouter-web/)
as an intermediary tool to create map of each of the routes. `main.py
gen-brouter-urls` produces a unique URL for each route, and each route
version. 

### Trips and Schedules
Trip definitions include:
- Stop sequences with arrival/departure times
- Service calendars (weekday, weekend, holiday schedules)
- Route shapes from GeoJSON files

### Route Shapes
Route geometries are stored as GeoJSON LineString files in the `shapes/`
directory. Each route references a shape_id that corresponds to a `.geojson`
file.

## GTFS Output

The generated feed includes all standard GTFS files:
- `agency.txt` - Transit agency information
- `routes.txt` - Route definitions
- `stops.txt` - Stop locations and names
- `trips.txt` - Trip definitions
- `stop_times.txt` - Stop sequences and schedules
- `calendar.txt` - Service patterns
- `calendar_dates.txt` - Service exceptions
- `feed_info.txt` - Feed metadata
- `shapes.txt` - Route geometries

## Contributing

When modifying transit data:
1. Update stop definitions in `stops.csv` and run `python main.py gen-stops`
2. Update route/stop definitions in `src/gen_gtfs.py`
3. Add/update GeoJSON shape files in `shapes/` directory using `python main.py gen-brouter-urls` as needed
4. Run `python main.py gen-gtfs` to regenerate the feed
5. Test the generated GTFS feed with [validators](https://gtfs-validator.mobilitydata.org/)

## Contact

For questions about the transit system, contact Columbia County Public Transportation:
- Phone: 518-672-4901
- Website: [https://publictransportation.columbiacountyny.com](https://publictransportation.columbiacountyny.com)
