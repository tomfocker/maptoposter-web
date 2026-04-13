from app.cache_coverage import (
    CacheRequest,
    compute_fetch_context,
    normalize_point,
    request_fits_within_cached_coverage,
)


def test_compute_fetch_context_matches_existing_formula_for_default_poster():
    ctx = compute_fetch_context(
        CacheRequest(
            point=(31.2304, 121.4737),
            dist=10000,
            width=12,
            height=16,
            map_x_offset=0.0,
            map_y_offset=0.0,
        )
    )
    assert round(ctx.fetch_dist, 3) == 3333.333
    assert ctx.fetch_point == (31.2304, 121.4737)


def test_compute_fetch_context_expands_for_offsets():
    ctx = compute_fetch_context(
        CacheRequest(
            point=(31.2304, 121.4737),
            dist=10000,
            width=12,
            height=16,
            map_x_offset=0.4,
            map_y_offset=-0.2,
        )
    )
    assert ctx.fetch_dist > 3333.333


def test_request_fits_within_cached_coverage_for_same_center_and_smaller_need():
    request = CacheRequest(
        point=(31.2304, 121.4737),
        dist=8000,
        width=10,
        height=10,
        map_x_offset=0.0,
        map_y_offset=0.0,
    )
    assert request_fits_within_cached_coverage(
        request=request,
        cached_center=(31.2304, 121.4737),
        cached_fetch_dist=4000.0,
    )


def test_normalize_point_rounds_to_stable_precision():
    assert normalize_point((31.2304123, 121.4737444)) == (31.23041, 121.47374)
