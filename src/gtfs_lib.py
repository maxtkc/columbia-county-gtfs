#!/usr/bin/env python3
# This file contains resources and tools that are not route specific

from enum import Enum

import geojson


class RouteTypes(Enum):
    TRAM = 0  # Tram, Streetcar, Light rail. Any light rail or street level system within a metropolitan area.
    SUBWAY = 1  # Subway, Metro. Any underground rail system within a metropolitan area.
    RAIL = 2  # Rail. Used for intercity or long-distance travel.
    BUS = 3  # Bus. Used for short- and long-distance bus routes.
    FERRY = 4  # Ferry. Used for short- and long-distance boat service.
    CABLE = 5  # Cable tram. Used for street-level rail cars where the cable runs beneath the vehicle (e.g., cable car in San Francisco).
    AERIAL = 6  # Aerial lift, suspended cable car (e.g., gondola lift, aerial tramway). Cable transport where cabins, cars, gondolas or open chairs are suspended by means of one or more cables.
    FUNICULAR = 7  # Funicular. Any rail system designed for steep inclines.
    TROLLEY = 11  # Trolleybus. Electric buses that draw power from overhead wires using poles.
    MONORAIL = (
        12  # Monorail. Railway in which the track consists of a single rail or a beam.
    )


class DirectionId(Enum):
    OUTBOUND = 0  # Travel in one direction (e.g. outbound travel).
    INBOUND = 1  # Travel in the opposite direction (e.g. inbound travel).


class BikesAllowed(Enum):
    UNKNOWN = 0  # No bike information for the trip.
    YES = 1  # Vehicle being used on this particular trip can accommodate at least one bicycle.
    NO = 2  # No bicycles are allowed on this trip.


class ServiceAvailable(Enum):
    YES = 1  # Service is available
    NO = 0  # Service is not available


class ServiceException(Enum):
    ADDED = 1  # Service is added
    REMOVED = 2  # Service is removed


def linestring_from_geojson(fp):
    """Helper to open fp and return its first feature’s LineString coords."""
    with open(fp, "r", encoding="utf-8") as f:
        fc = geojson.load(f)
    return fc.features[0].geometry.coordinates
