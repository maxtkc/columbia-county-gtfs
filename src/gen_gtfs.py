#!/usr/bin/env python3

import holidays

from src.gtfs_lib import (
    BikesAllowed,
    DirectionId,
    RouteTypes,
    ServiceAvailable,
    ServiceException,
)


# Agency Info
AGENCY_ID = "CC"
AGENCY_EMAIL = "tbd"

# Route IDs
SHOPPING = "SHOPPING"
HUD_ALB = "HUD_ALB"
HUD_CHT = "HUD_CHT"
MOND = "MOND"

# Service IDs
DAILY_SERVICE_ID = "DAILY"
MONDAY_SERVICE_ID = "MONDAY"
TUES_FRI_SERVICE_ID = "TUES_FRI"
WEEKDAY_SERVICE_ID = "WEEKDAY"

AGENCY = {
    # Agency Id
    "agency_id": AGENCY_ID,
    # Agency Name
    "agency_name": "Columbia County Public Transportation",
    # Agency URL
    "agency_url": "https://publictransportation.columbiacountyny.com",
    # Agency Timezone
    "agency_timezone": "America/New_York",
    "agency_phone": "518-672-4901",
    "agency_email": AGENCY_EMAIL,
}

FEED_INFO = {
    "feed_publisher_name": AGENCY["agency_name"],
    "feed_publisher_url": AGENCY["agency_url"],
    "feed_contact_email": AGENCY_EMAIL,
    "feed_contact_url": AGENCY["agency_url"],
    "feed_lang": "en-US",
    "feed_version": 1,
    "feed_start_date": 20250704,
    "feed_end_date": 20290704,
}

ROUTES = [
    {
        "route_id": SHOPPING,
        "agency_id": AGENCY_ID,
        "route_long_name": "Hudson-Greenport Shopping Shuttle",
        "route_desc": "Daily service looping through many shopping locations between Hudson and Greenport",
        "route_type": RouteTypes.BUS.value,
    },
    {
        "route_id": HUD_ALB,
        "agency_id": AGENCY_ID,
        "route_long_name": "Hudson-Albany Commuter Shuttle",
        "route_desc": "Weekday shuttle service between Hudson and Albany",
        "route_type": RouteTypes.BUS.value,
    },
    {
        "route_id": HUD_CHT,
        "agency_id": AGENCY_ID,
        "route_long_name": "Chatham-Hudson Bus Route",
        "route_desc": "Tuesday and Friday free service between Chatham and Hudson",
        "route_type": RouteTypes.BUS.value,
    },
    {
        "route_id": MOND,
        "agency_id": AGENCY_ID,
        "route_long_name": "Monday County Bus",
        "route_desc": "Monday morning bus service through various shopping locations in the county",
        "route_type": RouteTypes.BUS.value,
    },
]

TRIPS = [
    {
        "route_id": SHOPPING,
        "service_id": DAILY_SERVICE_ID,
        "trip_id": "PORTLAND_BOS_SOUTHBOUND_0315",
        "trip_short_name": "Boston Logan International Airport",
        "direction_id": DirectionId.OUTBOUND.value,
        "shape_id": "PORTLAND_BOS_SOUTHBOUND_LOGAN_FIRST",
        "bikes_allowed": BikesAllowed.YES.value,
        "stop_times": [
            ("03:15", "STOP-c99cb943-4db3-4fb6-b612-c97a7d202d13"),
            ("05:05", "STOP-9a1d503f-4812-4ec4-af0d-6275316cc2c4"),
            ("05:25", "STOP-0a858b61-d2dc-44f8-a6fd-9a528df6a3a8"),
        ],
    },
]

STOPS = [
]

CALENDAR = [
    {
        "service_id": DAILY_SERVICE_ID,
        "monday": ServiceAvailable.YES.value,
        "tuesday": ServiceAvailable.YES.value,
        "wednesday": ServiceAvailable.YES.value,
        "thursday": ServiceAvailable.YES.value,
        "friday": ServiceAvailable.YES.value,
        "saturday": ServiceAvailable.YES.value,
        "sunday": ServiceAvailable.YES.value,
        "start_date": 20250704,
        "end_date": 20290704,
    },
    {
        "service_id": MONDAY_SERVICE_ID,
        "monday": ServiceAvailable.YES.value,
        "tuesday": ServiceAvailable.NO.value,
        "wednesday": ServiceAvailable.NO.value,
        "thursday": ServiceAvailable.NO.value,
        "friday": ServiceAvailable.NO.value,
        "saturday": ServiceAvailable.NO.value,
        "sunday": ServiceAvailable.NO.value,
        "start_date": 20250704,
        "end_date": 20290704,
    },
    {
        "service_id": TUES_FRI_SERVICE_ID,
        "monday": ServiceAvailable.NO.value,
        "tuesday": ServiceAvailable.YES.value,
        "wednesday": ServiceAvailable.NO.value,
        "thursday": ServiceAvailable.YES.value,
        "friday": ServiceAvailable.NO.value,
        "saturday": ServiceAvailable.NO.value,
        "sunday": ServiceAvailable.NO.value,
        "start_date": 20250704,
        "end_date": 20290704,
    },
    {
        "service_id": WEEKDAY_SERVICE_ID,
        "monday": ServiceAvailable.YES.value,
        "tuesday": ServiceAvailable.YES.value,
        "wednesday": ServiceAvailable.YES.value,
        "thursday": ServiceAvailable.YES.value,
        "friday": ServiceAvailable.YES.value,
        "saturday": ServiceAvailable.NO.value,
        "sunday": ServiceAvailable.NO.value,
        "start_date": 20250704,
        "end_date": 20290704,
    },
]


CALENDAR_DATES = [
    {
        "service_id": DAILY_SERVICE_ID,
        "date": int(d.strftime("%Y%m%d")),  # e.g. 20250704
        "exception_type": ServiceException.REMOVED.value,
    }
    for d in sorted(holidays.US(years=range(2025, 2030)).keys())
]
