# aurora api 
from datetime import UTC, timedelta

import requests
from django.conf import settings
from django.core.cache import cache
from django.utils.dateparse import parse_datetime

NOAA_KP_FORECAST_URL = "https://services.swpc.noaa.gov/products/noaa-planetary-k-index-forecast.json"
KP_CACHE_KEY = "noaa_kp_forecast"
KP_CACHE_SECONDS = 60 * 60
KP_INTERVAL = timedelta(hours=3)


def get_kp_forecast():
    cached = cache.get(KP_CACHE_KEY)
    if cached is not None:
        return cached

    response = requests.get(
        NOAA_KP_FORECAST_URL,
        headers={"User-Agent": settings.MET_NORWAY_USER_AGENT},
        timeout=10,
    )
    response.raise_for_status()
    data = response.json()

    cache.set(KP_CACHE_KEY, data, KP_CACHE_SECONDS)
    return data


def kp_at(data, moment):
    """Return the Kp value for the 3-hour window containing the given moment, or None."""
    for entry in data:
        start = parse_datetime(entry["time_tag"]).replace(tzinfo=UTC)
        if start <= moment < start + KP_INTERVAL:
            return entry["kp"]
    return None

# observation quality factors
CLOUDY_THRESHOLD = 75
CLEAR_SKY_THRESHOLD = 40
STRONG_KP = 4
ACTIVE_KP = 2


def aurora_chance(kp, cloud_area_fraction):
    """Rough aurora viewing chance in Northern Norway, based on Kp index and cloud cover."""
    if kp is None or cloud_area_fraction is None:
        return None
    if cloud_area_fraction >= CLOUDY_THRESHOLD:
        return "low"
    if kp >= STRONG_KP and cloud_area_fraction < CLEAR_SKY_THRESHOLD:
        return "high"
    if kp >= ACTIVE_KP:
        return "medium"
    return "low"