import asyncio
import importlib
import logging
import re
import sys
import types
from pathlib import Path


def _module(name: str, **attrs):
    module = types.ModuleType(name)
    module.__dict__.update(attrs)
    return module


def _install_import_stubs():
    if "fastapi" not in sys.modules:
        class _FastAPI:
            def __init__(self, *args, **kwargs):
                pass

            def mount(self, *args, **kwargs):
                return None

            def get(self, *args, **kwargs):
                return lambda func: func

            def post(self, *args, **kwargs):
                return lambda func: func

        class _Jinja2Templates:
            def __init__(self, *args, **kwargs):
                pass

            def TemplateResponse(self, *args, **kwargs):
                return {"args": args, "kwargs": kwargs}

        class _StaticFiles:
            def __init__(self, *args, **kwargs):
                pass

        class _HTMLResponse:
            def __init__(self, content="", *args, **kwargs):
                self.content = content

        sys.modules["fastapi"] = _module(
            "fastapi",
            FastAPI=_FastAPI,
            Request=object,
            BackgroundTasks=object,
            Form=lambda default=None, *args, **kwargs: default,
        )
        sys.modules["fastapi.templating"] = _module("fastapi.templating", Jinja2Templates=_Jinja2Templates)
        sys.modules["fastapi.staticfiles"] = _module("fastapi.staticfiles", StaticFiles=_StaticFiles)
        sys.modules["fastapi.responses"] = _module("fastapi.responses", HTMLResponse=_HTMLResponse)

    sys.modules.setdefault(
        "create_map_poster",
        _module(
            "create_map_poster",
            THEME={},
            get_available_themes=lambda: [],
            create_poster=lambda *args, **kwargs: None,
            load_theme=lambda *args, **kwargs: {},
        ),
    )
    sys.modules.setdefault("font_management", _module("font_management", load_fonts=lambda *args, **kwargs: ["stub-font"]))

    if "geopy" not in sys.modules:
        geocoders = _module(
            "geopy.geocoders",
            Nominatim=type("Nominatim", (), {"__init__": lambda self, *args, **kwargs: None, "geocode": lambda self, *args, **kwargs: None}),
        )
        sys.modules["geopy"] = _module("geopy", geocoders=geocoders)
        sys.modules["geopy.geocoders"] = geocoders

    sys.modules.setdefault(
        "osmnx",
        _module(
            "osmnx",
            settings=types.SimpleNamespace(
                log_console=False,
                use_cache=False,
                http_user_agent="",
                requests_kwargs={},
            ),
        ),
    )


_install_import_stubs()

app_main = importlib.import_module("app.main")
choose_poster_labels = app_main.choose_poster_labels
has_chinese = app_main.has_chinese


class RecordingBackgroundTasks:
    def __init__(self):
        self.calls = []

    def add_task(self, func, **kwargs):
        self.calls.append((func, kwargs))


class FakeLocation:
    def __init__(self, latitude, longitude, address, name=""):
        self.latitude = latitude
        self.longitude = longitude
        self.raw = {"address": address, "name": name}


def test_index_template_exposes_copy_language_selector():
    template = Path("app/templates/index.html").read_text(encoding="utf-8")
    assert 'name="copy_language"' in template
    assert re.search(r'<option\b[^>]*value="en"', template)
    assert re.search(r'<option\b[^>]*value="zh"', template)


def test_index_template_defaults_copy_language_to_english():
    template = Path("app/templates/index.html").read_text(encoding="utf-8")
    assert re.search(r'<option\b[^>]*value="en"[^>]*selected', template)


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


def test_generate_poster_uses_chinese_lookup_for_display_labels(monkeypatch):
    geocode_calls = []

    class FakeGeolocator:
        def geocode(self, query, **kwargs):
            geocode_calls.append((query, kwargs["language"]))
            if kwargs["language"] == "en":
                return FakeLocation(31.23, 121.47, {"city": "Shanghai", "country": "China"})
            return FakeLocation(31.23, 121.47, {"city": "上海", "country": "中国"})

    background_tasks = RecordingBackgroundTasks()

    monkeypatch.setattr(app_main, "Nominatim", lambda *args, **kwargs: FakeGeolocator())
    monkeypatch.setattr(app_main, "load_fonts", lambda font_name: [font_name])

    response = asyncio.run(
        app_main.generate_poster(
            request=object(),
            background_tasks=background_tasks,
            city="Shanghai",
            country="China",
            copy_language="zh",
        )
    )

    assert geocode_calls == [("Shanghai, China", "en"), ("Shanghai, China", "zh")]
    assert len(background_tasks.calls) == 1
    _, task_kwargs = background_tasks.calls[0]
    assert task_kwargs["city"] == "上海"
    assert task_kwargs["country"] == "中国"
    assert task_kwargs["original_city"] == "Shanghai"
    assert task_kwargs["original_country"] == "China"
    assert task_kwargs["active_fonts"] == ["Noto Sans SC"]
    assert "progress-container" in response.content


def test_generate_poster_logs_and_falls_back_when_chinese_lookup_fails(monkeypatch, caplog):
    class FakeGeolocator:
        def geocode(self, query, **kwargs):
            if kwargs["language"] == "en":
                return FakeLocation(48.85, 2.35, {"city": "Paris", "country": "France"})
            raise RuntimeError("zh lookup exploded")

    background_tasks = RecordingBackgroundTasks()

    monkeypatch.setattr(app_main, "Nominatim", lambda *args, **kwargs: FakeGeolocator())
    monkeypatch.setattr(app_main, "load_fonts", lambda font_name: [font_name])

    with caplog.at_level(logging.WARNING):
        asyncio.run(
            app_main.generate_poster(
                request=object(),
                background_tasks=background_tasks,
                city="Paris",
                country="France",
                copy_language="zh",
            )
        )

    _, task_kwargs = background_tasks.calls[0]
    assert task_kwargs["city"] == "Paris"
    assert task_kwargs["country"] == "France"
    assert task_kwargs["active_fonts"] is None
    assert "Chinese display lookup failed" in caplog.text
