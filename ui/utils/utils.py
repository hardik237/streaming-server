from datetime import datetime, date
import pytz
import urllib.parse

def convert_to_iso_standard(time_obj):
    """Convert a time object to ISO 8601 format with IST timezone"""
    dt = datetime.combine(date.today(), time_obj)
    ist = pytz.timezone("Asia/Kolkata")
    dt_ist = ist.localize(dt)

    # Format datetime to ISO 8601 with microseconds and timezone (+hhmm)
    iso = dt_ist.strftime("%Y-%m-%dT%H:%M:%S.%f%z")

    # Insert colon in timezone offset, e.g. +0530 -> +05:30
    iso = iso[:-2] + ':' + iso[-2:]

    # Truncate microseconds to 5 digits exactly (e.g. 749068 -> 74906)
    if '.' in iso:
        dot_index = iso.find('.')
        iso = iso[:dot_index + 6] + iso[dot_index + 7:]

    return iso

