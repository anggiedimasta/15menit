from app.config import settings


def in_java_bbox(lat: float, lng: float) -> bool:
    min_lat, min_lng, max_lat, max_lng = settings.java_bbox
    return min_lat <= lat <= max_lat and min_lng <= lng <= max_lng


def in_bodetabek_bbox(lat: float, lng: float) -> bool:
    min_lat, min_lng, max_lat, max_lng = settings.bodetabek_bbox
    return min_lat <= lat <= max_lat and min_lng <= lng <= max_lng
