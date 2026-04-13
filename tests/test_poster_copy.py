from app.poster_copy import choose_poster_labels, has_chinese


def test_choose_poster_labels_keeps_existing_english_default():
    city, country = choose_poster_labels(
        copy_language="en",
        display_city="",
        display_country="",
        english_city="Shanghai",
        english_country="China",
        chinese_city="上海",
        chinese_country="中国",
    )

    assert city == "Shanghai"
    assert country == "China"


def test_choose_poster_labels_prefers_chinese_when_selected():
    city, country = choose_poster_labels(
        copy_language="zh",
        display_city="",
        display_country="",
        english_city="Shanghai",
        english_country="China",
        chinese_city="上海",
        chinese_country="中国",
    )

    assert city == "上海"
    assert country == "中国"


def test_choose_poster_labels_keeps_manual_override_highest_priority():
    city, country = choose_poster_labels(
        copy_language="zh",
        display_city="魔都",
        display_country="中国",
        english_city="Shanghai",
        english_country="China",
        chinese_city="上海",
        chinese_country="中国",
    )

    assert city == "魔都"
    assert country == "中国"


def test_choose_poster_labels_falls_back_to_english_when_chinese_missing():
    city, country = choose_poster_labels(
        copy_language="zh",
        display_city="",
        display_country="",
        english_city="Paris",
        english_country="France",
        chinese_city="",
        chinese_country="",
    )

    assert city == "Paris"
    assert country == "France"


def test_has_chinese_detects_chinese_copy():
    assert has_chinese("上海中国")
