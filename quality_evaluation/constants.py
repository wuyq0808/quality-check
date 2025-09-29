#!/usr/bin/env python3
"""
Shared constants for quality evaluation
"""

from enum import Enum


class WebsiteKey(Enum):
    GOOGLE_TRAVEL = "google_travel"
    AGODA = "agoda_com"
    BOOKING_COM = "booking_com"
    SKYSCANNER = "skyscanner"


# Individual website constants
GOOGLE_TRAVEL = {
    "url": "https://www.google.com/travel/",
    "key": WebsiteKey.GOOGLE_TRAVEL
}

AGODA = {
    "url": "https://www.agoda.com",
    "key": WebsiteKey.AGODA
}

BOOKING_COM = {
    "url": "https://www.booking.com",
    "key": WebsiteKey.BOOKING_COM
}

SKYSCANNER_HOTELS = {
    "url": "https://www.skyscanner.com/hotels",
    "key": WebsiteKey.SKYSCANNER
}

# Common website list for all features
WEBSITES = [
    SKYSCANNER_HOTELS,
    GOOGLE_TRAVEL,
    BOOKING_COM,
    AGODA,
]