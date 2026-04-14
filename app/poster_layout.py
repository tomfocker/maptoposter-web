from dataclasses import dataclass


@dataclass(frozen=True)
class PosterTypography:
    city_text: str
    country_text: str
    city_y: float
    country_y: float
    coords_y: float
    divider_y: float
    divider_start: float
    divider_end: float
    title_scale: float
    subtitle_scale: float
    divider_linewidth_scale: float
    title_shrink_threshold: int
    min_title_size: float


def is_latin_script(text):
    """
    Check whether the text is primarily rendered with Latin glyphs.
    """
    if not text:
        return True

    latin_count = 0
    total_alpha = 0

    for char in text:
        if char.isalpha():
            total_alpha += 1
            if ord(char) < 0x250:
                latin_count += 1

    if total_alpha == 0:
        return True

    return (latin_count / total_alpha) > 0.8


def _chinese_title_scale(display_city: str) -> float:
    char_count = len(display_city.strip())
    if char_count <= 2:
        return 1.18
    if char_count <= 4:
        return 1.10
    if char_count <= 6:
        return 1.00
    if char_count <= 8:
        return 0.91
    return 0.84


def build_poster_typography(display_city: str, display_country: str) -> PosterTypography:
    if is_latin_script(display_city):
        return PosterTypography(
            city_text="  ".join(list(display_city.upper())),
            country_text=display_country.upper(),
            city_y=0.14,
            country_y=0.10,
            coords_y=0.07,
            divider_y=0.125,
            divider_start=0.4,
            divider_end=0.6,
            title_scale=1.0,
            subtitle_scale=1.0,
            divider_linewidth_scale=1.0,
            title_shrink_threshold=10,
            min_title_size=10.0,
        )

    return PosterTypography(
        city_text=display_city,
        country_text=display_country,
        city_y=0.156,
        country_y=0.089,
        coords_y=0.047,
        divider_y=0.118,
        divider_start=0.445,
        divider_end=0.555,
        title_scale=_chinese_title_scale(display_city),
        subtitle_scale=0.94,
        divider_linewidth_scale=0.78,
        title_shrink_threshold=6,
        min_title_size=18.0,
    )
