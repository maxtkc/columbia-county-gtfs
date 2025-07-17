#!/usr/bin/env python3
"""
GTFS Utility Library

This module provides GTFS-compliant enumerations and utility functions for
processing transit data. Contains standardized GTFS constants and helper
functions for working with GeoJSON route shapes.
"""

from enum import Enum

import geojson


class RouteTypes(Enum):
    """
    GTFS route_type enumeration defining different modes of transportation.
    
    These values correspond to the GTFS specification route_type field,
    which categorizes the type of vehicle used on each route.
    """
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
    """
    GTFS direction_id enumeration for trip direction.
    
    Used to distinguish between directional variants of a route,
    such as inbound vs outbound travel.
    """
    OUTBOUND = 0  # Travel in one direction (e.g. outbound travel).
    INBOUND = 1  # Travel in the opposite direction (e.g. inbound travel).


class BikesAllowed(Enum):
    """
    GTFS bikes_allowed enumeration for bicycle accommodation.
    
    Indicates whether bicycles are allowed on a particular trip.
    """
    UNKNOWN = 0  # No bike information for the trip.
    YES = 1  # Vehicle being used on this particular trip can accommodate at least one bicycle.
    NO = 2  # No bicycles are allowed on this trip.


class ServiceAvailable(Enum):
    """
    GTFS service availability enumeration for calendar service patterns.
    
    Used in calendar.txt to indicate whether service operates on specific days.
    """
    YES = 1  # Service is available
    NO = 0  # Service is not available


class ServiceException(Enum):
    """
    GTFS exception_type enumeration for calendar date exceptions.
    
    Used in calendar_dates.txt to indicate service additions or removals
    on specific dates that differ from the regular calendar pattern.
    """
    ADDED = 1  # Service is added
    REMOVED = 2  # Service is removed


def linestring_from_geojson(fp):
    """
    Extract LineString coordinates from a GeoJSON file.
    
    Opens a GeoJSON file and returns the coordinate array from the first
    feature's LineString geometry. Used for processing route shape files
    into GTFS shapes.txt format.
    
    Args:
        fp (str): File path to the GeoJSON file containing route geometry
        
    Returns:
        list: Array of [longitude, latitude] coordinate pairs representing
              the route shape points in sequence
              
    Raises:
        FileNotFoundError: If the specified GeoJSON file doesn't exist
        IndexError: If the GeoJSON file contains no features
        KeyError: If the first feature doesn't contain valid LineString geometry
    """
    with open(fp, "r", encoding="utf-8") as f:
        fc = geojson.load(f)  # Load the GeoJSON feature collection
    # Extract coordinates from the first feature's LineString geometry
    return fc.features[0].geometry.coordinates
