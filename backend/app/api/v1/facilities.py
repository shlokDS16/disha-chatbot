from fastapi import APIRouter, Depends, Query

from app.config import Settings, get_settings
from app.models.schemas import (
    DirectionsResponse,
    FacilityService,
    NearbyFacilitiesResponse,
)
from app.services import maps as maps_service

router = APIRouter(prefix="/facilities", tags=["facilities"])


@router.get("/nearby", response_model=NearbyFacilitiesResponse)
def nearby(
    lat: float = Query(...),
    lng: float = Query(...),
    service: FacilityService = Query(FacilityService.ANY),
    radius_m: int = Query(10000, ge=500, le=50000),
    limit: int = Query(10, ge=1, le=20),
    settings: Settings = Depends(get_settings),
) -> NearbyFacilitiesResponse:
    items = maps_service.find_nearby(settings, lat, lng, service, radius_m, limit)
    return NearbyFacilitiesResponse(
        user_location={"lat": lat, "lng": lng}, facilities=items
    )


@router.get("/directions", response_model=DirectionsResponse)
def directions(
    destination_place_id: str = Query(...),
    dest_lat: float = Query(...),
    dest_lng: float = Query(...),
) -> DirectionsResponse:
    url = (
        "https://www.google.com/maps/dir/?api=1"
        f"&destination={dest_lat},{dest_lng}"
        f"&destination_place_id={destination_place_id}"
    )
    return DirectionsResponse(directions_url=url)
