from pathlib import Path

from app.poster_layout import build_poster_typography
from font_management import load_fonts


def test_build_poster_typography_keeps_english_signature_style():
    typography = build_poster_typography("Paris", "France")

    assert typography.city_text == "P  A  R  I  S"
    assert typography.country_text == "FRANCE"
    assert typography.city_y == 0.14
    assert typography.country_y == 0.10
    assert typography.coords_y == 0.07
    assert typography.divider_start == 0.4
    assert typography.divider_end == 0.6
    assert typography.title_scale == 1.0


def test_build_poster_typography_uses_more_refined_chinese_spacing():
    typography = build_poster_typography("上海", "中国")

    assert typography.city_text == "上海"
    assert typography.country_text == "中国"
    assert typography.city_y >= 0.155
    assert typography.country_y <= 0.09
    assert typography.coords_y <= 0.05
    assert typography.divider_start >= 0.44
    assert typography.divider_end <= 0.56
    assert typography.title_scale > 1.0
    assert 0.9 < typography.subtitle_scale < 1.0


def test_build_poster_typography_gives_chinese_bottom_block_more_breathing_room():
    typography = build_poster_typography("青岛", "中国")

    assert typography.city_y - typography.country_y >= 0.06
    assert typography.country_y - typography.coords_y >= 0.04


def test_build_poster_typography_scales_chinese_titles_by_length():
    short_title = build_poster_typography("青岛", "中国")
    medium_title = build_poster_typography("呼和浩特", "中国")
    long_title = build_poster_typography("阿拉善左旗城区", "中国")

    assert short_title.title_scale > medium_title.title_scale > long_title.title_scale
    assert long_title.min_title_size >= 18.0


def test_load_fonts_supports_local_chinese_poster_preset():
    fonts = load_fonts("poster_zh_cn")

    assert fonts is not None
    assert fonts["title"].endswith("fonts/JingHuaLaoSong-v3.0.ttf")
    assert fonts["subtitle"].endswith("fonts/JingHuaLaoSong-v3.0.ttf")
    assert fonts["meta_regular"].endswith("fonts/Roboto-Regular.ttf")
    assert Path(fonts["title"]).exists()
