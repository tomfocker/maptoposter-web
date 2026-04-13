from dataclasses import dataclass
import math


@dataclass(frozen=True)
class CacheRequest:
    point: tuple[float, float]
    dist: float
    width: float
    height: float
    map_x_offset: float = 0.0
    map_y_offset: float = 0.0


@dataclass(frozen=True)
class FetchContext:
    fetch_point: tuple[float, float]
    fetch_dist: float


def normalize_point(point: tuple[float, float], precision: int = 5) -> tuple[float, float]:
    lat, lon = point
    return (round(lat, precision), round(lon, precision))


def compute_fetch_context(request: CacheRequest) -> FetchContext:
    compensated_dist = request.dist * (max(request.height, request.width) / min(request.height, request.width)) / 4
    lat_shift_m = request.map_y_offset * compensated_dist
    lon_shift_m = -request.map_x_offset * compensated_dist
    meters_per_deg_lat = 111320.0
    meters_per_deg_lon = 111320.0 * abs(math.cos(math.radians(request.point[0])))
    fetch_point = (
        request.point[0] + lat_shift_m / meters_per_deg_lat,
        request.point[1] + lon_shift_m / max(meters_per_deg_lon, 1e-9),
    )
    offset_extra = max(abs(request.map_x_offset), abs(request.map_y_offset)) * 0.5
    return FetchContext(fetch_point=fetch_point, fetch_dist=compensated_dist * (1 + offset_extra))


def request_fits_within_cached_coverage(
    request: CacheRequest,
    cached_center: tuple[float, float],
    cached_fetch_dist: float,
) -> bool:
    context = compute_fetch_context(request)
    return normalize_point(context.fetch_point) == normalize_point(cached_center) and cached_fetch_dist >= context.fetch_dist
