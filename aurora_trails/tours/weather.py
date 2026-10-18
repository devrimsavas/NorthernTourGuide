from email.utils import parsedate_to_datetime

import requests
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone
from datetime import timedelta
from django.utils.dateparse import parse_datetime

MET_FORECAST_URL = "https://api.met.no/weatherapi/locationforecast/2.0/compact"
DEFAULT_CACHE_SECONDS = 30 * 60


def get_forecast(latitude, longitude):
    lat = round(float(latitude), 4)
    lon = round(float(longitude), 4)
    cache_key = f"met_forecast_{lat}_{lon}"

    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    response = requests.get(
        MET_FORECAST_URL,
        params={"lat": lat, "lon": lon},
        headers={"User-Agent": settings.MET_NORWAY_USER_AGENT},
        timeout=10,
    )
    response.raise_for_status()
    data = response.json()

    cache.set(cache_key, data, _seconds_until_expiry(response))
    return data


def _seconds_until_expiry(response):
    expires = response.headers.get("Expires")
    if not expires:
        return DEFAULT_CACHE_SECONDS
    seconds = (parsedate_to_datetime(expires) - timezone.now()).total_seconds()
    return max(int(seconds), 60)

MAX_TIME_DIFFERENCE = timedelta(hours=3)


def forecast_at(data, moment):
    """Return the forecast closest to the given moment, or None if it is out of range."""
    timeseries = data["properties"]["timeseries"]
    if not timeseries:
        return None

    closest = min(timeseries, key=lambda entry: abs(parse_datetime(entry["time"]) - moment))
    if abs(parse_datetime(closest["time"]) - moment) > MAX_TIME_DIFFERENCE:
        return None

    details = closest["data"]["instant"]["details"]
    summary = closest["data"].get("next_1_hours") or closest["data"].get("next_6_hours") or {}

    return {
        "time": timezone.localtime(parse_datetime(closest["time"])),
        "air_temperature": details.get("air_temperature"),
        "cloud_area_fraction": details.get("cloud_area_fraction"),
        "wind_speed": details.get("wind_speed"),
        "symbol_code": summary.get("summary", {}).get("symbol_code"),
    }