import re


def has_chinese(text: str) -> bool:
    if not text:
        return False
    return bool(re.search(r"[\u4e00-\u9fff]", text))


def choose_poster_labels(
    copy_language: str,
    display_city: str,
    display_country: str,
    english_city: str,
    english_country: str,
    chinese_city: str,
    chinese_country: str,
) -> tuple[str, str]:
    auto_city = chinese_city if copy_language == "zh" and chinese_city else english_city
    auto_country = chinese_country if copy_language == "zh" and chinese_country else english_country
    return display_city or auto_city, display_country or auto_country
