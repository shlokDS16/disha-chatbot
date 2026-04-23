"""Google Maps Places (New) + Geocoding wrappers.

Used by /facilities to find nearby HPLC centres, haematology hospitals, and
general hospitals. If GOOGLE_MAPS_API_KEY is missing, MAPS_UNAVAILABLE is
raised and the frontend falls back to a generic referral block.
"""
from __future__ import annotations

import logging
from typing import Any

import httpx

from app.config import Settings
from app.errors import DishaError, ErrorCode
from app.models.schemas import FacilityItem, FacilityService

_log = logging.getLogger("disha.maps")


# Type-to-query strategy. Google Places taxonomy does not have a
# "sickle cell testing" type, so we combine type hints + keyword hints.
_QUERY_CONFIG: dict[FacilityService, dict[str, Any]] = {
    FacilityService.HPLC_CENTRE: {
        "includedTypes": ["medical_lab", "hospital"],
        "keyword": "HPLC hemoglobin electrophoresis sickle cell",
    },
    FacilityService.CVS_AMNIO: {
        "includedTypes": ["hospital"],
        "keyword": "prenatal diagnosis CVS amniocentesis",
    },
    FacilityService.HAEMATOLOGY: {
        "includedTypes": ["hospital", "doctor"],
        "keyword": "haematology sickle cell",
    },
    FacilityService.HU_DISPENSING: {
        "includedTypes": ["pharmacy", "hospital"],
        "keyword": "hydroxyurea sickle cell",
    },
    FacilityService.GENERAL_HOSPITAL: {
        "includedTypes": ["hospital"],
        "keyword": "general hospital",
    },
    FacilityService.ANY: {
        "includedTypes": ["hospital"],
        "keyword": "hospital",
    },
}


_PLACES_NEARBY_ENDPOINT = "https://places.googleapis.com/v1/places:searchNearby"
_PLACES_TEXT_ENDPOINT = "https://places.googleapis.com/v1/places:searchText"


def _require_key(settings: Settings) -> str:
    if not settings.google_maps_api_key:
        raise DishaError(
            ErrorCode.MAPS_UNAVAILABLE,
            "Maps service is not configured on the server.",
            status_code=503,
        )
    return settings.google_maps_api_key


def _directions_url(lat: float, lng: float, place_id: str) -> str:
    return (
        "https://www.google.com/maps/dir/?api=1"
        f"&destination={lat},{lng}&destination_place_id={place_id}"
    )


def find_nearby(
    settings: Settings,
    lat: float,
    lng: float,
    service: FacilityService,
    radius_m: int = 10000,
    limit: int = 10,
) -> list[FacilityItem]:
    key = _require_key(settings)
    cfg = _QUERY_CONFIG.get(service, _QUERY_CONFIG[FacilityService.ANY])

    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": key,
        "X-Goog-FieldMask": (
            "places.id,places.displayName,places.formattedAddress,"
            "places.location,places.rating,places.currentOpeningHours.openNow,"
            "places.types"
        ),
    }

    # For specific facility types (HPLC, haematology, etc.) we want keyword
    # filtering — nearbySearch only supports includedTypes, so use searchText
    # which accepts a free-text query. Fall back to nearbySearch for ANY.
    use_text = service != FacilityService.ANY
    if use_text:
        body: dict[str, Any] = {
            "textQuery": cfg["keyword"],
            "maxResultCount": limit,
            "locationBias": {
                "circle": {
                    "center": {"latitude": lat, "longitude": lng},
                    "radius": float(radius_m),
                }
            },
        }
        endpoint = _PLACES_TEXT_ENDPOINT
    else:
        body = {
            "includedTypes": cfg["includedTypes"],
            "maxResultCount": limit,
            "locationRestriction": {
                "circle": {
                    "center": {"latitude": lat, "longitude": lng},
                    "radius": float(radius_m),
                }
            },
        }
        endpoint = _PLACES_NEARBY_ENDPOINT

    try:
        resp = httpx.post(endpoint, json=body, headers=headers, timeout=20.0)
    except httpx.HTTPError as e:
        _log.exception("Places request failed")
        raise DishaError(
            ErrorCode.MAPS_UNAVAILABLE,
            "Maps service did not respond.",
            status_code=503,
            details={"reason": str(e)},
        ) from e
    if resp.status_code != 200:
        _log.warning("Places %s returned %s: %s", endpoint, resp.status_code, resp.text[:200])
        raise DishaError(
            ErrorCode.MAPS_UNAVAILABLE,
            f"Maps service returned HTTP {resp.status_code}.",
            status_code=502,
            details={"body": resp.text[:200]},
        )
    data = resp.json()
    places = data.get("places") or []
    items: list[FacilityItem] = []
    for p in places:
        loc = p.get("location") or {}
        plat = loc.get("latitude", 0.0)
        plng = loc.get("longitude", 0.0)
        distance_km = _haversine_km(lat, lng, plat, plng)
        items.append(
            FacilityItem(
                id=p.get("id", ""),
                name=(p.get("displayName") or {}).get("text", "Unknown"),
                type=service,
                address=p.get("formattedAddress", ""),
                distance_km=round(distance_km, 2),
                rating=p.get("rating"),
                open_now=(p.get("currentOpeningHours") or {}).get("openNow"),
                directions_url=_directions_url(plat, plng, p.get("id", "")),
            )
        )
    items.sort(key=lambda i: i.distance_km)
    return items


def _haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    from math import asin, cos, radians, sin, sqrt

    r = 6371.0
    dlat = radians(lat2 - lat1)
    dlng = radians(lng2 - lng1)
    a = (
        sin(dlat / 2) ** 2
        + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlng / 2) ** 2
    )
    return 2 * r * asin(sqrt(a))
